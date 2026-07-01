"""
Draft Generation Prompt — produces functional metadata for tables and columns.

Incorporates:
- The 4 governance pillars (Claridad, Propósito, Detalle, Contexto)
- Naming-convention knowledge from modelamiento docs (ACORD, UDV standards)
- Technical evidence (schema, profiling, lineage, tags)
- Examples from lineamiento_gobierno_metadatos.md
"""

from __future__ import annotations

import json
from typing import Any

# ── Condensed Naming-Convention Knowledge ─────────────────────────────
# Extracted from doc_1..doc_4 — only the substance relevant for comment
# generation, not the full documents.

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

## Instrucciones

Genera una descripción funcional para la tabla y para CADA columna, \
siguiendo estrictamente los 4 pilares de gobierno.

### Para la Descripción de la Tabla:
- **Decodifica el nombre** aplicando el Paso 0 como primera oración.
- **Deduce el propósito real** a partir de las columnas, el profiling, y \
cómo encaja en el modelo ACORD (Póliza, Cliente, Reclamo, etc.).
- **Proporciona utilidad de negocio**: Explica exactamente CÓMO la usaría el \
negocio y qué procesos analíticos específicos habilita.
- **Contexto de Linaje**: Menciona de forma breve sus predecesores (upstream) \
y qué activos la consumen aguas abajo (downstream).
- 🚫 **PROHIBIDO** usar frases de relleno genéricas (ver Regla 9).

### Para las Descripciones de Columnas (Aplicando los 4 Pilares):
- **Pilar 1 (Claridad)**: Describe exactamente qué valor contiene. Aclara acrónimos.
- **Pilar 2 (Propósito)**: ¿Para qué sirve esta métrica/atributo en particular?
- **Pilar 3 (Detalle)**: Dominio de valores esperados, reglas de cálculo y si es obligatorio.
- **Pilar 4 (Contexto)**: ¿De qué sistema core viene o en qué lógica se basa?

## Reglas de Interpretación del Profiling

Cuando analices el profiling de columnas, aplica OBLIGATORIAMENTE estas reglas:

1. **distinct=1**: La columna actúa como FILTRO FIJO de esta vista. Menciona \
el valor exacto en la descripción. Ejemplo: "En esta vista, el campo \
siempre contiene 'Contratante' (filtro de origen, línea Rentas)."
2. **Valores tipo hash/SHA** (strings de 64+ caracteres alfanuméricos sin \
espacios ni guiones): Es un dato anonimizado/hasheado. Descríbelo como: \
"Identificador anonimizado mediante hash SHA-256 de la persona asegurada \
por clasificación DAC (datos de alta criticidad)."
3. **distinct muy alto** (>90% del total no-null): Probablemente un \
identificador único o valor de alta cardinalidad. Menciónalo.
4. **sample_values con códigos cortos** (ej: 'S', 'D', 'RV', '812'): Describe \
qué representan los códigos si puedes inferirlo del contexto de negocio \
(S=Soles, D=Dólares, RV=Renta Vitalicia, etc.).

{naming_knowledge}

## Formato de Respuesta — CRÍTICO

Tu respuesta DEBE ser EXCLUSIVAMENTE un objeto JSON válido. \
NO uses markdown, NO uses encabezados ##, NO escribas texto libre. \
SOLO JSON puro con esta estructura exacta:

{{"table_comment": "Tu descripción de tabla aquí.", "column_comments": {{"col1": "desc1", "col2": "desc2"}}}}

Cada columna del schema DEBE tener una entrada en "column_comments". \
NO repitas los nombres de los pilares (Pilar 1, Pilar 2...) en la respuesta. \
Integra los 4 pilares en una sola oración funcional por columna.

## Reglas
1. Escribe SIEMPRE en español formal.
2. NO inventes semántica; basa la descripción en la evidencia técnica proporcionada.
3. Si no puedes inferir algo con confianza, indícalo explícitamente.
4. Para campos técnicos obligatorios (codapp, feccargainfo, periododia, flgvalido, \
flgobservado, desmensajeobs), usa definiciones estándar breves.
5. Considera los tags de columna (DAC, EDC) para clasificación de sensibilidad.
6. Si una columna ya tiene comentario, debes RETARLO (ver Regla 8) y mejorarlo \
garantizando que tu nueva versión tenga una **longitud igual o superior**.
7. Si una columna NO tiene comentario (o es vacío), plantea uno sustancial que \
tenga estrictamente **entre 15 (mínimo) y 25 (máximo) palabras** aplicando los pilares.

### Regla 8: Detección de Comments Existentes Incorrectos
Cuando una columna tiene un comentario existente, VERIFÍCALO contra su nombre y profiling:
- ¿El comentario es coherente con el NOMBRE del campo? \
  Ejemplo: `codproducto` con comment "PRIMA POR RECARGOS" → INCORRECTO \
  (codproducto = código de producto, no tiene relación con prima ni recargos).
- ¿El comentario es coherente con los VALORES del profiling? \
  Ejemplo: `feciniciovigencia` con comment "FECHA INICIO CAMPAÑA" → INCORRECTO \
  (los valores muestran fechas de inicio de vigencia de póliza, no de campaña).
- Si detectas inconsistencia, genera un comment NUEVO y CORRECTO basado en \
  la evidencia del nombre del campo y el profiling.

### Regla 9: Anti-Patrones Prohibidos
Las siguientes frases están PROHIBIDAS por ser genéricas y sin valor funcional:
- "... de la póliza de seguro" (repetido para cada columna sin diferenciación)
- "Esta información es crucial para entender el comportamiento"
- "Ayuda a tomar decisiones informadas"
- "Proporciona información detallada"
- "Se utiliza para análisis y reportes"

En su lugar, describe el PARA QUÉ ESPECÍFICO de cada campo:
- ❌ "Monto de prima de la póliza de seguro."
- ✅ "Monto total de prima pagada por el contratante en el contrato de renta \
vitalicia. Permite calcular la rentabilidad del producto y la constitución de \
reservas técnicas según normativa SBS."

Cada descripción de columna debe ser ÚNICA y específica al campo — NO uses \
la misma coletilla repetida en todas las columnas.
"""


def build_draft_prompt(
    table_info: dict[str, Any],
    column_details: list[dict[str, Any]],
    profiling_summary: dict[str, Any] | None = None,
    lineage_info: list[dict[str, Any]] | None = None,
    column_tags: list[dict[str, Any]] | None = None,
    quality_findings: list[str] | None = None,
    human_feedback: str | None = None,
) -> tuple[str, str]:
    """
    Build (system_prompt, user_prompt) for the draft-generation agent.

    Returns
    -------
    tuple[str, str]
        (system_message, user_message)
    """
    system = SYSTEM_PROMPT.format(naming_knowledge=NAMING_CONVENTION_KNOWLEDGE)

    # ── Build user message with evidence ──────────────────────────────
    parts = []

    # Table basics
    parts.append(f"## Tabla: `{table_info.get('full_name', 'unknown')}`")
    parts.append(f"- Tipo: {table_info.get('table_type', 'N/A')}")
    parts.append(f"- Formato: {table_info.get('data_source_format', 'N/A')}")
    if table_info.get("comment"):
        parts.append(f"- Comentario actual: {table_info['comment']}")

    # Columns
    parts.append("\n## Columnas")
    for col in column_details:
        line = f"- `{col.get('col_name', col.get('name', ''))}` "
        line += f"({col.get('data_type', col.get('type', ''))}) "
        comment = col.get("comment", "")
        if comment:
            line += f"— Comentario actual: {comment}"
        parts.append(line)

    # Profiling — ONLY send distinct_count and sample_values.
    # null_pct is intentionally EXCLUDED: the sample (1K rows) is too small
    # relative to the total table (potentially millions of rows) to make
    # reliable null assertions. Sending null_pct causes the LLM to write
    # false absolute statements like "always null in this view".
    if profiling_summary and profiling_summary.get("column_profiles"):
        parts.append(f"\n## Profiling (muestra indicativa de {profiling_summary.get('sample_size', 'N/A')} filas sobre {profiling_summary.get('row_count', 'N/A')} totales — NO usar para afirmar nulidad)")
        for cp in profiling_summary["column_profiles"]:
            # Only include columns with useful signal: distinct values or samples
            has_samples = bool(cp.get("sample_values"))
            has_distinct = cp['distinct_count'] > 0
            if not has_samples and not has_distinct:
                # Column has no data signal at all in the sample — skip it
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

    # Previous findings (rework context)
    if quality_findings:
        parts.append("\n## ⚠️ Hallazgos de Calidad Previos (CORREGIR)")
        for f in quality_findings:
            parts.append(f"- {f}")

    # Human feedback (HITL context)
    if human_feedback:
        parts.append(f"\n## 📝 Feedback del Data Steward\n{human_feedback}")

    user = "\n".join(parts)
    return system, user
