"""
Governance Reflection Prompt — validates compliance with the 7 governance
principles of Pacífico Seguros' metadata standard.
"""

from __future__ import annotations

from typing import Any

from config.governance_pillars import GOVERNANCE_PRINCIPLES


SYSTEM_PROMPT = """\
Eres un agente de reflexión de governance de metadatos. Tu rol es validar \
que un draft de metadatos funcionales cumple con los principios de gobierno \
de datos de Pacífico Seguros ANTES de su publicación.

## Principios de Gobierno a Validar

{principles_text}

CRÍTICO: Estás evaluando el TEXTO DEL BORRADOR (draft), no el proceso humano \
ni la arquitectura de la base de datos subyacente. Por lo tanto:
- Asume que los principios P2 (Colaboración), P3 (Trazabilidad), P4 (Aprobación) y P7 (Publicación) \
  están CUMPLIDOS (`true`) porque son pasos del flujo de trabajo que suceden DESPUÉS. \
  NUNCA penalices el draft por no mostrar evidencia de aprobación o colaboración.
- Para P1 (Unicidad) y P5 (Actualización), enfócate en si el borrador de texto se contradice \
  o documenta cosas evidentemente obsoletas. NO penalices si la tabla misma tiene datos \
  duplicados o campos nulos (eso es arquitectura de datos, no metadatos).

## Validaciones Específicas

Además de los principios, verifica:

1. **Naming compliance**: ¿Los comentarios son coherentes con las convenciones \
   de nomenclatura UDV? (prefijos: id, cod, des, fec, flg, mto, prima, etc.)
2. **Completitud**: ¿Todas las columnas tienen comentarios? ¿El comentario \
   de tabla cubre los 4 pilares?
3. **Consistencia**: ¿Los comentarios de columnas son consistentes entre sí \
   y con el comentario de tabla?
4. **Sensibilidad**: ¿Las columnas con tags DAC/EDC tienen descripciones \
   que mencionan la clasificación de sensibilidad?
5. **No invención**: ¿Los comentarios se basan en evidencia técnica o están \
   inventando semántica sin soporte?

## Formato de Respuesta

Responde ÚNICAMENTE en JSON válido:
```json
{{
  "governance_status": "pass|fail|needs_review",
  "findings": [
    "Hallazgo 1: [Principio Pn] descripción concreta de la violación.",
    "Hallazgo 2: ..."
  ],
  "principle_compliance": {{
    "P1_unicidad": true,
    "P2_colaboracion": true,
    "P3_trazabilidad": true,
    "P4_aprobacion": true,
    "P5_actualizacion": true,
    "P6_clasificacion": true,
    "P7_publicacion": true
  }},
  "recommendation": "Texto breve con la recomendación general."
}}
```

## Reglas
1. governance_status = "pass" si no hay violaciones críticas.
2. governance_status = "fail" si hay violaciones que impiden publicación.
3. governance_status = "needs_review" si hay ambigüedades que requieren \
   juicio humano.
4. Sé específico en los findings — indica QUÉ principio se viola y POR QUÉ.
"""


def build_governance_prompt(
    draft_table_comment: str,
    draft_column_comments: dict[str, str],
    quality_score: float,
    pillar_scores: dict[str, float],
    table_info: dict[str, Any],
    column_tags: list[dict[str, Any]] | None = None,
    profiling_summary: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Build (system_prompt, user_prompt) for the governance reflection agent.

    Returns
    -------
    tuple[str, str]
        (system_message, user_message)
    """
    # Format principles into system prompt
    principles_lines = []
    for p in GOVERNANCE_PRINCIPLES:
        principles_lines.append(f"### {p['id']}. {p['name']}\n{p['rule']}\n")
    principles_text = "\n".join(principles_lines)
    system = SYSTEM_PROMPT.format(principles_text=principles_text)

    # Build user message
    parts = []
    parts.append(f"## Tabla: `{table_info.get('full_name', 'unknown')}`")
    parts.append(f"- Quality Score: {quality_score:.2f}")
    parts.append("- Pillar Scores:")
    for k, v in pillar_scores.items():
        parts.append(f"  - {k}: {v:.2f}")

    # Tags
    if column_tags:
        parts.append("\n## Tags de Sensibilidad")
        for tag in column_tags:
            parts.append(
                f"- `{tag['nombre_columna']}`: "
                f"{tag['tag_clave']}={tag['tag_valor']}"
            )

    # Profiling — only include columns with informative signal (no null_pct)
    if profiling_summary and profiling_summary.get("column_profiles"):
        parts.append("\n## Profiling (referencia para verificación — muestra indicativa)")
        for cp in profiling_summary["column_profiles"]:
            notable = []
            if cp['distinct_count'] == 1 and cp.get('sample_values'):
                notable.append(f"valor fijo: {cp['sample_values'][0]}")
            if cp.get('sample_values') and any(len(str(v)) > 60 for v in cp['sample_values']):
                notable.append("posible dato anonimizado/hash")
            if notable:
                parts.append(f"- `{cp['column']}`: {', '.join(notable)}")

    # Draft
    parts.append(f"\n## Comentario de Tabla\n{draft_table_comment}")
    parts.append("\n## Comentarios de Columnas")
    total_cols = len(table_info.get("columns", []))
    commented_cols = len(draft_column_comments)
    parts.append(f"({commented_cols}/{total_cols} columnas con comentario)")
    for col_name, comment in draft_column_comments.items():
        parts.append(f"- **`{col_name}`**: {comment}")

    # Missing columns
    existing_col_names = {c["name"] for c in table_info.get("columns", [])}
    commented_names = set(draft_column_comments.keys())
    missing = existing_col_names - commented_names
    if missing:
        parts.append(f"\n⚠️ Columnas SIN comentario: {', '.join(sorted(missing))}")

    user = "\n".join(parts)
    return system, user
