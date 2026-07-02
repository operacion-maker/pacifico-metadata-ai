"""
Draft Generation Prompt — produces functional metadata for tables and columns.

Incorporates:
- The 4 governance pillars (Claridad, Propósito, Detalle, Contexto)
- Naming-convention knowledge from modelamiento docs (ACORD, UDV standards)
- Technical evidence (schema, profiling, lineage, tags)
- Prompt Anchoring (locks human-validated feedback from UI)
"""

from __future__ import annotations

import json
from typing import Any

# ── Condensed Naming-Convention Knowledge ─────────────────────────────
NAMING_CONVENTION_KNOWLEDGE = """
## Convenciones de Nomenclatura UDV (Lakehouse Silver Layer)

### Prefijos de entidades UDV
- **h** = histórica (registra historial de cambios/movimientos)
  - hd = histórica diaria, hm = histórica mensual, ha = histórica anual
- **m** = maestra (dato maestro, fuente única de verdad)
  - md = maestra diaria, mm = maestra mensual, ma = maestra anual
- **u** = última (solo estado actual, sin historial)
  - ud = última diaria, um = última mensual
- **lkp_** = lookups/catálogos de referencia
- **drv_** = entidades derivadas (resultado de reglas/combinaciones)
- **ext_** = integraciones externas
- **config_** = entidades de configuración/parámetros
- **dac** = indicador de datos de alta criticidad (sensibles)

### Estructura de nombre de entidad
`prefijo_[dac]_dominio_concepto_scope_origen`
- scope: gen (generales), vida, renta, cross (transversal), embebido
- origen: fuente gobernada (ej: core)

### Prefijos de campos (obligatorios)
- **id** = identificador único (BIGINT)
- **cod** = código numérico o alfanumérico de catálogo (STRING)
- **des** = descripción textual (STRING)
- **nom** = nombre propio (STRING)
- **fec** = fecha (DATE, formato yyyy-MM-dd)
- **flg** = flag booleano (INT: 0/1)
- **ind** = indicador alfanumérico (STRING: S/N)
- **mto** = monto monetario (DECIMAL)
- **prima** = prima de seguro (sin prefijo mto, DECIMAL(20,6))
- **ctd** = cantidad numérica (INT)
- **num** = número secuencial (BIGINT)
- **porc** = porcentaje (DECIMAL(7,4))
- **tasa** = tasa de interés/actuarial (DECIMAL(12,8))
- **tip** = tipo/clasificación categórica (STRING)
- **ts** = timestamp (TIMESTAMP)
- **periodo** = periodo lógico (STRING: yyyyMMdd)

### Campos técnicos obligatorios en UDV
- codapp, feccargainfo, periododia, flgvalido, flgobservado, desmensajeobs

### Contexto de negocio (Pacífico Seguros - Perú)
- Ramos SBS: Generales, Vida, Renta, Embebidos
- Modelo canónico: ACORD (Policy, Party, Claim, Product)
- Capas: RDV (Bronze) → UDV (Silver, semántica) → DDV (Gold, analítica)
- UDV custodia el SIGNIFICADO del dato; DDV custodia el CONSUMO
"""

SYSTEM_PROMPT = """\
Eres un experto en gobierno de datos y metadatos funcionales para el sector \
asegurador peruano (Pacífico Seguros). Tu tarea es generar definiciones de \
metadatos funcionales de alta calidad para tablas y columnas del Unity Catalog.

## Paso 0 — Decodifica el nombre de la tabla ANTES de escribir

Analiza el nombre de la tabla aplicando las convenciones de nomenclatura:
1. Identifica el **prefijo temporal** (hd=histórica diaria, hm=mensual, ud=última diaria, md=maestra diaria, etc.)
2. Detecta el **marcador DAC** si existe (datos de alta criticidad / sensibles)
3. Extrae el **dominio y concepto** (poliza, persona, siniestro, cobertura, etc.)
4. Identifica el **scope** (vig=vigentes, gen=generales, renta, vida, cross, etc.)
5. Identifica el **origen** (core, sf, etc.)

Ejemplo: `hd_dac_poliza_vig_cliente_rol_renta_core`
→ hd (histórica diaria) + dac (datos sensibles) + poliza_vig (pólizas vigentes)
  + cliente_rol (relación cliente-rol) + renta (línea Rentas Vitalicias) + core (sistema core)

**INCLUYE esta decodificación como primera oración del table_comment.**

## Instrucciones de Generación de Borrador

Genera una descripción funcional para la tabla y para CADA columna, \
siguiendo los pilares de Claridad, Propósito, Detalle y Contexto.

### Para la Descripción de la Tabla:
- **Decodifica el nombre** aplicando el Paso 0 como primera oración.
- **Deduce el propósito real** a partir de las columnas, el profiling, y \
cómo encaja en el modelo ACORD.
- **Proporciona utilidad de negocio**: Explica CÓMO la usaría el \
negocio y qué procesos analíticos habilita.
- **Contexto de Linaje**: Menciona de forma breve sus predecesores (upstream) \
y qué activos la consumen aguas abajo (downstream).

### Para las Descripciones de Columnas:
- **Claridad**: Describe exactamente qué valor contiene. Aclara acrónimos.
- **Propósito**: ¿Para qué sirve esta métrica/atributo en particular?
- **Detalle**: Dominio de valores esperados, reglas de cálculo y obligatoriedad.
- **Contexto**: ¿De qué sistema core viene o en qué lógica se basa?

## REGLAS DE PONDERACIÓN HUMANA (PROMPT ANCHORING) - CRÍTICO

Si en el contexto provisto (prompt del usuario) encuentras textos bajo la etiqueta `[TEXTO_VALIDADO_POR_HUMANO]`, DEBES respetar la siguiente regla inquebrantable:
- **Inmutabilidad Semántica**: Tienes **prohibido** alterar el significado, la redacción o la intención de las descripciones que el humano ya ha validado. Puedes copiarlas textualmente o integrarlas de manera fluida, pero NUNCA debes sobreescribir la lógica de negocio que el Data Steward ha establecido.
- Usa la sección `general_observations` para guiar la optimización de las columnas que **AÚN NO** han sido editadas por el humano.

{naming_knowledge}

## Formato de Respuesta — CRÍTICO

Tu respuesta DEBE ser EXCLUSIVAMENTE un objeto JSON válido. \
NO uses markdown, NO uses encabezados ##, NO escribas texto libre. \
SOLO JSON puro con esta estructura exacta:

{{
  "table_comment": "Descripción final de la tabla...",
  "column_comments": {{
    "col_1": "Descripción..."
  }},
  "governance_indicator": {{
    "status": "pass",
    "compliance_notes": ["Nota 1 sobre estándares UDV detectados", "Nota 2..."]
  }}
}}

Para `governance_indicator.status`, usa "pass" si cumple con las reglas, o "warn" si hay desviaciones menores.
"""

def build_draft_prompt(
    table_info: dict[str, Any],
    column_details: list[dict[str, Any]],
    profiling_summary: dict[str, Any] | None = None,
    lineage_info: list[dict[str, Any]] | None = None,
    column_tags: list[dict[str, Any]] | None = None,
    human_feedback: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Build (system_prompt, user_prompt) for the draft-generation agent.
    """
    system = SYSTEM_PROMPT.format(naming_knowledge=NAMING_CONVENTION_KNOWLEDGE)

    # ── Build user message with evidence ──────────────────────────────
    parts = []

    # Table basics
    parts.append(f"## Tabla: `{table_info.get('full_name', 'unknown')}`")
    parts.append(f"- Tipo: {table_info.get('table_type', 'N/A')}")
    parts.append(f"- Formato: {table_info.get('data_source_format', 'N/A')}")
    if table_info.get("comment"):
        parts.append(f"- Comentario original técnico: {table_info['comment']}")

    # Columns
    parts.append("\n## Columnas")
    for col in column_details:
        line = f"- `{col.get('col_name', col.get('name', ''))}` "
        line += f"({col.get('data_type', col.get('type', ''))}) "
        comment = col.get("comment", "")
        if comment:
            line += f"— Comentario técnico: {comment}"
        parts.append(line)

    # Profiling
    if profiling_summary and profiling_summary.get("column_profiles"):
        parts.append(f"\n## Profiling (muestra indicativa de {profiling_summary.get('sample_size', 'N/A')} filas)")
        for cp in profiling_summary["column_profiles"]:
            has_samples = bool(cp.get("sample_values"))
            has_distinct = cp['distinct_count'] > 0
            if not has_samples and not has_distinct:
                continue
            line = f"- `{cp['column']}`: distinct={cp['distinct_count']}"
            if cp.get("sample_values"):
                line += f", samples={cp['sample_values'][:3]}"
            parts.append(line)

    # Tags
    if column_tags:
        parts.append("\n## Tags de Columnas")
        for tag in column_tags:
            parts.append(
                f"- `{tag['nombre_columna']}`: "
                f"{tag['tag_clave']}={tag['tag_valor']}"
            )

    # Lineage (upstream + downstream)
    if lineage_info:
        upstream = [li for li in lineage_info if li.get('lineage_direction') == 'upstream']
        downstream = [li for li in lineage_info if li.get('lineage_direction') == 'downstream']

        if upstream:
            parts.append("\n## Linaje — Upstream (de dónde viene)")
            for li in upstream[:10]:
                parts.append(
                    f"- {li.get('trg_name', '')} "
                    f"(module={li.get('module_name', '')}, "
                    f"domain={li.get('domain_name', '')})"
                )

        if downstream:
            parts.append("\n## Linaje — Downstream (quién la consume)")
            for li in downstream[:10]:
                parts.append(
                    f"- {li.get('trg_name', '')} "
                    f"(module={li.get('module_name', '')}, "
                    f"domain={li.get('domain_name', '')})"
                )

    # Human feedback (HITL context / Prompt Anchoring)
    if human_feedback:
        parts.append("\n## 📝 FEEDBACK DEL DATA STEWARD (RETRABAJO)\n")
        
        obs = human_feedback.get("general_observations", "")
        if obs:
            parts.append(f"**Observaciones Generales:**\n{obs}\n")

        table_c = human_feedback.get("edited_table_comment", "")
        if table_c:
            parts.append(f"**[TEXTO_VALIDADO_POR_HUMANO] Comentario de Tabla:**\n{table_c}\n")

        edited_cols = human_feedback.get("edited_columns", {})
        if edited_cols:
            parts.append("**[TEXTO_VALIDADO_POR_HUMANO] Comentarios de Columnas Editadas:**")
            for c_name, c_val in edited_cols.items():
                parts.append(f"- `{c_name}`: {c_val}")

    user = "\n".join(parts)
    return system, user
