"""
Quality Evaluation Prompt — LLM-as-a-Judge for metadata draft quality.

Produces a structured JSON score per governance pillar (0.0–1.0)
and a list of actionable findings.
"""

from __future__ import annotations

from typing import Any


SYSTEM_PROMPT = """\
Eres un evaluador experto de calidad de metadatos funcionales. Tu rol es \
evaluar un draft de metadatos contra los 4 pilares de gobierno de datos \
de Pacífico Seguros.

CRÍTICO: Estás evaluando la calidad del TEXTO DEL DRAFT, no la calidad de \
la base de datos. Si una columna es 100% nula o inútil en la realidad, y el \
draft lo describe correctamente así, eso es un EXCELENTE metadato. \
NUNCA penalices al draft por reflejar defectos reales de los datos.

## Pilares de Evaluación

### 1. Claridad y Comprensión (clarity) — peso 25%
Evalúa si la definición:
- Es clara, precisa y sin ambigüedades.
- Explica todo término técnico.
- Identifica correctamente el tipo de tabla/columna.
- Indica frecuencia de actualización si aplica.

**Scoring**:
- 0.0–0.3: Definición vaga, confusa o incorrecta.
- 0.4–0.6: Definición parcialmente clara, faltan aclaraciones.
- 0.7–0.8: Definición clara pero mejorable.
- 0.9–1.0: Definición ejemplar, sin ambigüedades.

### 2. Propósito del Dato (purpose) — peso 25%
Evalúa si la definición:
- Describe para qué se usa en el negocio.
- Menciona procesos que habilita o impacta.
- Identifica usuarios o consumidores típicos.

**Scoring**:
- 0.0–0.3: No menciona propósito de negocio.
- 0.4–0.6: Propósito genérico o incompleto.
- 0.7–0.8: Propósito claro pero le faltan consumidores o procesos.
- 0.9–1.0: Propósito completamente contextualizado.

### 3. Nivel de Detalle (detail) — peso 25%
Evalúa si la definición:
- Describe alcance y contenido del dato.
- Indica si es histórico o estado actual.
- Menciona excepciones y reglas relevantes.
- Para columnas: dominio de valores, si es calculado, si es obligatorio.

**Scoring**:
- 0.0–0.3: Sin detalle útil.
- 0.4–0.6: Detalle superficial.
- 0.7–0.8: Buen detalle, faltan particularidades.
- 0.9–1.0: Detalle completo con excepciones y reglas.

### 4. Contexto y Relacionamiento (context) — peso 25%
Evalúa si la definición:
- Menciona fuentes o sistemas de origen.
- Describe relaciones con otros activos.
- Explica integración en el ecosistema.

**Scoring**:
- 0.0–0.3: Sin contexto.
- 0.4–0.6: Contexto parcial.
- 0.7–0.8: Buen contexto, falta ecosistema.
- 0.9–1.0: Contexto completo con relaciones.

## Validación contra Profiling

Si se proporciona profiling de columnas, aplica estas validaciones adicionales:

1. **distinct=1 ignorado**: Si una columna tiene un solo valor distinto y el \
draft no menciona ese valor fijo, penaliza en Detalle (-0.15). El valor fijo DEBE \
mencionarse explícitamente (ej: rol='Contratante', lineanegocio='Rentas').
2. **Comments existentes incorrectos no retados**: Si el nombre de la columna \
contradice su comment existente (ej: codproducto con comment de "prima") \
y el draft NO corrige esto, penaliza en Claridad (-0.2).
3. **Hash/SHA no identificado**: Si los sample_values muestran strings de 64+ \
caracteres y el draft no lo identifica como dato anonimizado, penaliza \
en Detalle (-0.1).

NOTA: El profiling es una muestra pequeña. NO penalices si el draft describe \
funcionalmente columnas que en la muestra no tienen valores. Un buen metadato \
describe el PROPÓSITO del campo, no el estado de los datos en un momento dado.

## Penalización por Repetitividad

Si más del 30% de los comentarios de columnas comparten la misma \
estructura de frase o coletilla (ej: "... de la póliza de seguro" repetido \
en múltiples columnas), resta 0.2 puntos al pilar de Claridad. \
Las descripciones deben ser ÚNICAS y ESPECÍFICAS para cada columna.

## Formato de Respuesta

Responde ÚNICAMENTE en JSON válido:
```json
{{
  "pillar_scores": {{
    "clarity": 0.0,
    "purpose": 0.0,
    "detail": 0.0,
    "context": 0.0
  }},
  "quality_score": 0.0,
  "findings": [
    "Hallazgo 1: descripción concreta del problema y sugerencia de mejora.",
    "Hallazgo 2: ..."
  ],
  "strengths": [
    "Fortaleza 1: qué hace bien el draft."
  ]
}}
```

## Reglas
1. Sé ESTRICTO pero justo. No infles scores.
2. Cada finding debe ser ACCIONABLE (qué falta y cómo corregirlo).
3. quality_score = promedio ponderado de pillar_scores (25% cada uno).
4. Evalúa TANTO el comentario de tabla como los de columnas.
5. Presta atención especial a columnas que tienen tags DAC/EDC — sus \
   definiciones deben ser más detalladas respecto a sensibilidad.
6. Si tienes profiling disponible, úsalo como FUENTE DE VERDAD para \
   contrastar las afirmaciones del draft.
"""


def build_quality_prompt(
    draft_table_comment: str,
    draft_column_comments: dict[str, str],
    table_info: dict[str, Any],
    column_tags: list[dict[str, Any]] | None = None,
    profiling_summary: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Build (system_prompt, user_prompt) for the quality evaluator.

    Returns
    -------
    tuple[str, str]
        (system_message, user_message)
    """
    parts = []

    # Table reference
    parts.append(f"## Tabla: `{table_info.get('full_name', 'unknown')}`")
    parts.append(f"- Tipo: {table_info.get('table_type', 'N/A')}")

    # Columns schema (for reference)
    parts.append("\n## Schema de Columnas (referencia)")
    for col in table_info.get("columns", []):
        line = f"- `{col['name']}` ({col.get('type', 'N/A')})"
        if col.get('comment') and col['comment'] not in ('', 'None'):
            line += f" — comment existente: {col['comment']}"
        parts.append(line)

    # Tags
    if column_tags:
        parts.append("\n## Tags de Sensibilidad")
        for tag in column_tags:
            parts.append(
                f"- `{tag['nombre_columna']}`: "
                f"{tag['tag_clave']}={tag['tag_valor']}"
            )

    # Profiling — ONLY distinct_count and samples (no null_pct, see draft_generation.py)
    if profiling_summary and profiling_summary.get("column_profiles"):
        parts.append(f"\n## Profiling (muestra de {profiling_summary.get('sample_size', 'N/A')} filas sobre {profiling_summary.get('row_count', 'N/A')} totales)")
        parts.append("Usa distinct_count y sample_values como referencia. NO uses ausencia de muestras para inferir nulidad.")
        for cp in profiling_summary["column_profiles"]:
            if not cp.get("sample_values") and cp['distinct_count'] == 0:
                continue  # Skip columns with no signal
            line = f"- `{cp['column']}`: distinct={cp['distinct_count']}"
            if cp.get("sample_values"):
                line += f", samples={cp['sample_values'][:3]}"
            parts.append(line)

    # Draft to evaluate
    parts.append("\n---\n## DRAFT A EVALUAR\n")
    parts.append(f"### Comentario de Tabla\n{draft_table_comment}")
    parts.append("\n### Comentarios de Columnas")
    for col_name, comment in draft_column_comments.items():
        parts.append(f"- **`{col_name}`**: {comment}")

    user = "\n".join(parts)
    return SYSTEM_PROMPT, user
