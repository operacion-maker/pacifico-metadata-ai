# Databricks notebook source
# MAGIC %md
# MAGIC # 🏛️ Metadata Governance Agent — MVP Notebook (Self-Contained)
# MAGIC
# MAGIC Copy this entire cell into your Databricks notebook.
# MAGIC It is **100% self-contained** — no external file imports needed.

# COMMAND ----------

# MAGIC %pip install langgraph>=0.2.0 langchain-core>=0.3.0 langchain-databricks>=0.1.0 databricks-sdk>=0.30.0 pydantic>=2.0.0 typing_extensions>=4.15.0
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CELDA 1: Configuración y Imports                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝

import json
import logging
import operator
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated, Any, Literal, TypedDict, Optional, Union

import mlflow

# ⚠️ NO usar mlflow.langchain.autolog() — es incompatible con langchain >= 0.3.0
# Usamos @mlflow.trace directamente en cada función.

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
log = logging.getLogger("metadata_governance")

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CELDA 2: Settings                                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝

@dataclass(frozen=True)
class Settings:
    LLM_MODEL: str = "databricks-meta-llama-3-1-8b-instruct"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096
    AUTO_REFLEXION_CEILING: float = 0.4
    HITL_TRIGGER: float = 0.7
    PUBLISH_READY: float = 0.9
    MAX_REFLEXION_LOOPS: int = 3
    MAX_PUBLISH_RETRIES: int = 2
    PROFILING_SAMPLE_ROWS: int = 1000

    UC_OBJETOS_COLUMNAS: str = (
        "ctl_lakehouse_modelamiento_prod"
        ".sch_ctl_modelamiento_silver_vw"
        ".md_objetos_uc_columnas"
    )
    UC_COLUMNAS_TAGS: str = (
        "ctl_lakehouse_modelamiento_prod"
        ".sch_ctl_modelamiento_silver_vw"
        ".ud_columnas_tags"
    )
    UC_LINEAGE_FUNCTION: str = (
        "ctl_lakehouse_modelamiento_prod"
        ".sch_ctl_modelamiento_silver_vw"
        ".fn_get_specific_lineage_in_lakehouse"
    )

SETTINGS = Settings()

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CELDA 3: State Schema                                              ║
# ╚══════════════════════════════════════════════════════════════════════╝

class AuditEntry(TypedDict, total=False):
    timestamp: str
    node: str
    action: str
    details: dict

class MetadataAgentState(TypedDict, total=False):
    request_id: str
    asset_fqn: str
    table_info: dict
    column_details: list
    profiling_summary: dict
    lineage_info: list
    column_tags: list
    naming_context: str
    draft_table_comment: str
    draft_column_comments: dict
    quality_score: float
    pillar_scores: dict
    quality_findings: Annotated[list, operator.add]
    governance_status: str
    governance_findings: Annotated[list, operator.add]
    human_feedback: Optional[str]
    human_decision: Optional[str]
    workflow_status: str
    loop_count: int
    retry_count: int
    audit_log: Annotated[list, operator.add]

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CELDA 4: Governance Pillars + Principles                           ║
# ╚══════════════════════════════════════════════════════════════════════╝

GOVERNANCE_PRINCIPLES = [
    {"id": "P1", "name": "Unicidad", "rule": "Cada activo de datos debe tener una única definición canónica, validada y publicada."},
    {"id": "P2", "name": "Colaboración obligatoria con el negocio", "rule": "Toda definición de metadatos funcionales debe construirse en conjunto con las áreas de negocio responsables del activo."},
    {"id": "P3", "name": "Trazabilidad del proceso", "rule": "Toda definición o actualización de metadatos debe seguir el flujo establecido con sus entregables correspondientes."},
    {"id": "P4", "name": "Aprobación formal", "rule": "Ningún metadato puede considerarse oficial sin el Visto Bueno del Domain Owner correspondiente."},
    {"id": "P5", "name": "Actualización continua", "rule": "Los metadatos deben actualizarse cada vez que el activo sufra cambios estructurales, funcionales o de uso."},
    {"id": "P6", "name": "Clasificación correcta", "rule": "Metadatos técnicos y funcionales no son intercambiables. Deben documentarse de forma separada y complementaria."},
    {"id": "P7", "name": "Publicación centralizada", "rule": "El repositorio oficial de metadatos debe ser el sistema centralizado de gobierno (Unity Catalog / MS Purview)."},
]

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CELDA 5: Unity Catalog Tools                                       ║
# ╚══════════════════════════════════════════════════════════════════════╝

def _get_spark():
    from pyspark.sql import SparkSession
    return SparkSession.getActiveSession()

@mlflow.trace(name="tool.get_table_info")
def get_table_info(fqn):
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    ti = w.tables.get(full_name=fqn)
    columns = []
    if ti.columns:
        for col in ti.columns:
            columns.append({
                "name": col.name,
                "type": str(col.type_text) if col.type_text else str(col.type_name),
                "comment": col.comment or "",
                "nullable": col.nullable if col.nullable is not None else True,
                "position": col.position,
            })
    return {
        "table_name": ti.name,
        "catalog": ti.catalog_name,
        "schema": ti.schema_name,
        "full_name": fqn,
        "table_type": str(ti.table_type) if ti.table_type else "UNKNOWN",
        "comment": ti.comment or "",
        "columns": columns,
        "created_at": str(ti.created_at) if ti.created_at else None,
        "updated_at": str(ti.updated_at) if ti.updated_at else None,
        "data_source_format": str(ti.data_source_format) if ti.data_source_format else None,
    }

@mlflow.trace(name="tool.get_column_details")
def get_column_details(fqn):
    spark = _get_spark()
    rows = spark.sql(f"DESCRIBE TABLE EXTENDED {fqn}").collect()
    columns = []
    for row in rows:
        name = row["col_name"]
        if name and (name.startswith("#") or name == "Detailed Table Information"):
            break
        if not name or name.strip() == "" or name.startswith("--"):
            continue
        columns.append({
            "col_name": name,
            "data_type": row["data_type"],
            "comment": row["comment"] if "comment" in row.asDict() else "",
        })
    return columns

@mlflow.trace(name="tool.get_column_tags")
def get_column_tags(fqn):
    spark = _get_spark()
    parts = fqn.split(".")
    if len(parts) != 3:
        return []
    catalog, schema, table = parts
    query = f"""
        SELECT nombre_columna, tag_clave, tag_valor
        FROM {SETTINGS.UC_COLUMNAS_TAGS}
        WHERE nombre_catalog = '{catalog}'
          AND nombre_esquema = '{schema}'
          AND nombre_tabla   = '{table}'
    """
    try:
        rows = spark.sql(query).collect()
        return [row.asDict() for row in rows]
    except Exception as e:
        log.warning("get_column_tags failed for %s: %s", fqn, e)
        return []



@mlflow.trace(name="tool.get_lineage")
def get_lineage(table_name, module_name="Silver", direction="UP"):
    spark = _get_spark()
    query = f"""
        SELECT *
        FROM {SETTINGS.UC_LINEAGE_FUNCTION}(
            '{table_name}', '{module_name}', '{direction}'
        )
    """
    try:
        rows = spark.sql(query).collect()
        return [row.asDict() for row in rows]
    except Exception as e:
        log.warning("get_lineage failed for %s: %s", table_name, e)
        return []

@mlflow.trace(name="tool.get_profiling_summary")
def get_profiling_summary(fqn):
    spark = _get_spark()
    sample_n = SETTINGS.PROFILING_SAMPLE_ROWS
    try:
        total_count = spark.sql(f"SELECT COUNT(*) AS cnt FROM {fqn}").first()["cnt"]
        sample_df = spark.sql(f"SELECT * FROM {fqn} LIMIT {sample_n}")
        columns_info = sample_df.dtypes
        profiles = []
        for col_name, col_type in columns_info:
            if col_name in ("codapp", "feccargainfo", "periododia"):
                continue
            stats = sample_df.selectExpr(
                f"COUNT(`{col_name}`) AS non_null",
                f"SUM(CASE WHEN `{col_name}` IS NULL THEN 1 ELSE 0 END) AS null_count",
                f"COUNT(DISTINCT `{col_name}`) AS distinct_count",
            ).first()
            sample_vals = (
                sample_df.select(col_name)
                .where(f"`{col_name}` IS NOT NULL")
                .distinct().limit(5).collect()
            )
            sample_values = [str(r[0]) for r in sample_vals]
            profiles.append({
                "column": col_name,
                "type": col_type,
                "non_null": int(stats["non_null"]),
                "null_count": int(stats["null_count"]),
                "null_pct": round(stats["null_count"] / sample_n * 100 if sample_n else 0, 1),
                "distinct_count": int(stats["distinct_count"]),
                "sample_values": sample_values,
            })
        return {"row_count": int(total_count), "sample_size": sample_n, "column_profiles": profiles}
    except Exception as e:
        log.warning("get_profiling_summary failed for %s: %s", fqn, e)
        return {"row_count": 0, "sample_size": 0, "column_profiles": []}

@mlflow.trace(name="tool.publish_table_comment")
def publish_table_comment(fqn, comment):
    spark = _get_spark()
    escaped = comment.replace("'", "\\'").replace("\n", " ")
    try:
        spark.sql(f"COMMENT ON TABLE {fqn} IS '{escaped}'")
        return {"status": "success", "fqn": fqn}
    except Exception as e:
        log.error("publish_table_comment failed: %s", e)
        return {"status": "error", "error": str(e), "fqn": fqn}

@mlflow.trace(name="tool.publish_column_comments")
def publish_column_comments(fqn, comments):
    spark = _get_spark()
    results = {"successes": [], "failures": []}
    for col_name, comment in comments.items():
        escaped = comment.replace("'", "\\'").replace("\n", " ")
        try:
            spark.sql(f"ALTER TABLE {fqn} ALTER COLUMN `{col_name}` COMMENT '{escaped}'")
            results["successes"].append(col_name)
        except Exception as e:
            log.error("Failed to set comment for %s.%s: %s", fqn, col_name, e)
            results["failures"].append({"column": col_name, "error": str(e)})
    results["status"] = "success" if not results["failures"] else "partial"
    return results

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CELDA 6: Prompts                                                   ║
# ╚══════════════════════════════════════════════════════════════════════╝

NAMING_CONVENTION_KNOWLEDGE = """
## Convenciones de Nomenclatura UDV (Lakehouse Silver Layer)

### Prefijos de entidades UDV
- **h** = histórica (hd=diaria, hm=mensual, ha=anual)
- **m** = maestra (md=diaria, mm=mensual, ma=anual)
- **u** = última (ud=diaria, um=mensual)
- **lkp_** = lookups/catálogos, **drv_** = derivadas, **ext_** = externas
- **dac** = datos de alta criticidad (sensibles)

### Estructura: `prefijo_[dac]_dominio_concepto_scope_origen`

### Prefijos de campos obligatorios
- id=identificador, cod=código, des=descripción, nom=nombre, fec=fecha
- flg=flag(0/1), ind=indicador(S/N), mto=monto, prima=prima, ctd=cantidad
- num=secuencial, porc=porcentaje, tasa=tasa, tip=tipo, ts=timestamp

### Campos técnicos: codapp, feccargainfo, periododia, flgvalido, flgobservado, desmensajeobs

### Contexto: Pacífico Seguros (Perú), Ramos SBS, Modelo ACORD
### Capas: RDV (Bronze) → UDV (Silver, semántica) → DDV (Gold, analítica)
"""

DRAFT_SYSTEM_PROMPT = """\
Eres un experto en gobierno de datos y metadatos funcionales para el sector \
asegurador peruano (Pacífico Seguros). Tu tarea es generar definiciones de \
metadatos funcionales de alta calidad para tablas y columnas del Unity Catalog.

## Instrucciones

Genera una descripción funcional para la tabla y para CADA columna, \
siguiendo estrictamente los 4 pilares de gobierno.

### Para la Descripción de la Tabla:
- **Deduce el propósito real** a partir de las columnas que la componen y \
cómo encaja en el modelo ACORD (Póliza, Cliente, Reclamo, etc.).
- **Proporciona utilidad de negocio**: Explica exactamente CÓMO la usaría el \
negocio y qué procesos analíticos específicos habilita.
- **Contexto de Linaje**: Menciona de forma breve cómo se construyó (sus \
predecesores/orígenes) y qué activos o modelos permite construir aguas abajo (sucesores).
- 🚫 **PROHIBIDO** usar frases de relleno genéricas como "ayuda a tomar decisiones \
informadas", "sirve para entender el comportamiento", o "proporciona información \
detallada". Ve directo al valor técnico y funcional.

### Para las Descripciones de Columnas (Aplicando los 4 Pilares):
- **Pilar 1 (Claridad)**: Describe exactamente qué valor contiene. Aclara acrónimos.
- **Pilar 2 (Propósito)**: ¿Para qué sirve esta métrica/atributo en particular?
- **Pilar 3 (Detalle)**: Dominio de valores esperados, reglas de cálculo y si es obligatorio.
- **Pilar 4 (Contexto)**: ¿De qué sistema core viene o en qué lógica se basa?

""" + NAMING_CONVENTION_KNOWLEDGE + """

## Formato de Respuesta

Responde ÚNICAMENTE en JSON válido con esta estructura:
```json
{{
  "table_comment": "Descripción funcional completa de la tabla (2-4 oraciones).",
  "column_comments": {{
    "nombre_columna_1": "Descripción funcional de la columna aplicando los 4 pilares.",
    "nombre_columna_2": "..."
  }}
}}
```

## Reglas
1. Escribe SIEMPRE en español formal.
2. NO inventes semántica; basa la descripción en la evidencia técnica proporcionada.
3. Si no puedes inferir algo con confianza, indícalo explícitamente.
4. Para campos técnicos obligatorios (codapp, feccargainfo, periododia, flgvalido, \
flgobservado, desmensajeobs), usa definiciones estándar breves.
5. Considera los tags de columna (DAC, EDC) para clasificación de sensibilidad.
6. Si una columna ya tiene comentario, debes retarlo y mejorarlo garantizando que tu \
nueva versión tenga una **longitud igual o superior**.
7. Si una columna NO tiene comentario (o es vacío), plantea uno sustancial que tenga \
estrictamente **entre 15 y 25 palabras** aplicando los pilares.
"""

QUALITY_SYSTEM_PROMPT = """\
Eres un evaluador experto de calidad de metadatos funcionales. Tu rol es \
evaluar un draft de metadatos contra los 4 pilares de gobierno de datos \
de Pacífico Seguros.

## Pilares de Evaluación

### 1. Claridad y Comprensión (clarity) — peso 25%
- 0.0–0.3: Vaga/confusa. 0.4–0.6: Parcialmente clara. 0.7–0.8: Clara, mejorable. 0.9–1.0: Ejemplar.

### 2. Propósito del Dato (purpose) — peso 25%
- 0.0–0.3: Sin propósito. 0.4–0.6: Genérico. 0.7–0.8: Claro sin consumidores. 0.9–1.0: Completo.

### 3. Nivel de Detalle (detail) — peso 25%
- 0.0–0.3: Sin detalle. 0.4–0.6: Superficial. 0.7–0.8: Bueno, falta particularidades. 0.9–1.0: Completo.

### 4. Contexto y Relacionamiento (context) — peso 25%
- 0.0–0.3: Sin contexto. 0.4–0.6: Parcial. 0.7–0.8: Bueno, falta ecosistema. 0.9–1.0: Completo.

Responde ÚNICAMENTE en JSON válido:
```json
{{
  "pillar_scores": {{"clarity": 0.0, "purpose": 0.0, "detail": 0.0, "context": 0.0}},
  "quality_score": 0.0,
  "findings": ["Hallazgo 1: descripción concreta."],
  "strengths": ["Fortaleza 1: qué hace bien."]
}}
```

Reglas: Sé ESTRICTO. Cada finding debe ser ACCIONABLE. quality_score = promedio de pillar_scores.
"""

GOVERNANCE_SYSTEM_PROMPT_TEMPLATE = """\
Eres un agente de reflexión de governance de metadatos. Valida que un draft \
cumple con los principios de gobierno de datos de Pacífico Seguros.

## Principios de Gobierno a Validar

{principles_text}

## Validaciones Específicas
1. Naming compliance con UDV (prefijos: id, cod, des, fec, flg, mto, prima, etc.)
2. Completitud: ¿Todas las columnas tienen comentarios?
3. Consistencia entre comentarios de columnas y tabla.
4. Sensibilidad: columnas DAC/EDC deben mencionar clasificación.
5. No invención: basado en evidencia técnica.

Responde ÚNICAMENTE en JSON válido:
```json
{{
  "governance_status": "pass|fail|needs_review",
  "findings": ["Hallazgo 1: [Principio Pn] descripción."],
  "principle_compliance": {{
    "P1_unicidad": true, "P2_colaboracion": true, "P3_trazabilidad": true,
    "P4_aprobacion": true, "P5_actualizacion": true, "P6_clasificacion": true,
    "P7_publicacion": true
  }},
  "recommendation": "Recomendación general."
}}
```
"""

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CELDA 7: LLM Helper + JSON Parser                                  ║
# ╚══════════════════════════════════════════════════════════════════════╝

def call_llm(system_msg, user_msg):
    """Call Databricks Foundation Model endpoint."""
    from langchain_databricks import ChatDatabricks
    llm = ChatDatabricks(
        endpoint=SETTINGS.LLM_MODEL,
        temperature=SETTINGS.LLM_TEMPERATURE,
        max_tokens=SETTINGS.LLM_MAX_TOKENS,
    )
    response = llm.invoke([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ])
    return response.content

def parse_json_response(text):
    """Extract JSON from LLM response, handling markdown fences."""
    clean = text.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        start = 1
        end = len(lines)
        if lines[-1].strip() == "```":
            end = len(lines) - 1
        clean = "\n".join(lines[start:end])
    return json.loads(clean)

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CELDA 8: Graph Nodes                                               ║
# ╚══════════════════════════════════════════════════════════════════════╝

@mlflow.trace(name="node.collect_context")
def collect_context(state):
    fqn = state["asset_fqn"]
    parts = fqn.split(".")
    table_short_name = parts[-1] if parts else fqn
    table_info = get_table_info(fqn)
    column_details = get_column_details(fqn)
    column_tags = get_column_tags(fqn)
    lineage_info = get_lineage(table_name=table_short_name, module_name="Silver", direction="UP")
    profiling_summary = get_profiling_summary(fqn)
    return {
        "table_info": table_info,
        "column_details": column_details,
        "column_tags": column_tags,
        "lineage_info": lineage_info,
        "profiling_summary": profiling_summary,
        "request_id": state.get("request_id") or str(uuid.uuid4()),
        "workflow_status": "context_collected",
        "loop_count": 0,
        "retry_count": 0,
        "audit_log": [{"timestamp": datetime.now(timezone.utc).isoformat(), "node": "collect_context", "action": "evidence_collected", "details": {"asset_fqn": fqn, "columns_found": len(column_details)}}],
    }

@mlflow.trace(name="node.generate_draft")
def generate_draft(state):
    table_info = state["table_info"]
    column_details = state.get("column_details", [])
    profiling_summary = state.get("profiling_summary")
    lineage_info = state.get("lineage_info")
    column_tags = state.get("column_tags")
    quality_findings = state.get("quality_findings")
    human_feedback = state.get("human_feedback")

    # Build user prompt
    parts = []
    parts.append(f"## Tabla: `{table_info.get('full_name', 'unknown')}`")
    parts.append(f"- Tipo: {table_info.get('table_type', 'N/A')}")
    parts.append(f"- Formato: {table_info.get('data_source_format', 'N/A')}")
    if table_info.get("comment"):
        parts.append(f"- Comentario actual: {table_info['comment']}")
    parts.append("\n## Columnas")
    for col in column_details:
        line = f"- `{col.get('col_name', col.get('name', ''))}` ({col.get('data_type', col.get('type', ''))}) "
        comment = col.get("comment", "")
        if comment:
            line += f"— Comentario actual: {comment}"
        parts.append(line)
    if profiling_summary and profiling_summary.get("column_profiles"):
        parts.append(f"\n## Profiling (muestra de {profiling_summary.get('sample_size', 'N/A')} filas, total: {profiling_summary.get('row_count', 'N/A')})")
        for cp in profiling_summary["column_profiles"]:
            line = f"- `{cp['column']}`: no_null={cp['non_null']}, null%={cp['null_pct']}%, distinct={cp['distinct_count']}"
            if cp.get("sample_values"):
                line += f", samples={cp['sample_values'][:3]}"
            parts.append(line)
    if column_tags:
        parts.append("\n## Tags de Columnas")
        for tag in column_tags:
            parts.append(f"- `{tag['nombre_columna']}`: {tag['tag_clave']}={tag['tag_valor']}")
    if lineage_info:
        parts.append("\n## Linaje (upstream)")
        for li in lineage_info[:10]:
            parts.append(f"- {li.get('trg_name', '')} ({li.get('module_name', '')}, domain={li.get('domain_name', '')})")
    if quality_findings:
        parts.append("\n## ⚠️ Hallazgos de Calidad Previos (CORREGIR)")
        for f in quality_findings:
            parts.append(f"- {f}")
    if human_feedback:
        parts.append(f"\n## 📝 Feedback del Data Steward\n{human_feedback}")

    user_prompt = "\n".join(parts)
    raw_response = call_llm(DRAFT_SYSTEM_PROMPT, user_prompt)

    try:
        parsed = parse_json_response(raw_response)
        draft_table_comment = parsed.get("table_comment", "")
        draft_column_comments = parsed.get("column_comments", {})
    except (json.JSONDecodeError, KeyError) as e:
        log.error("Failed to parse draft response: %s", e)
        draft_table_comment = raw_response
        draft_column_comments = {}

    loop_count = state.get("loop_count", 0)
    return {
        "draft_table_comment": draft_table_comment,
        "draft_column_comments": draft_column_comments,
        "workflow_status": "draft_generated",
        "loop_count": loop_count + 1,
        "human_feedback": None,
        "human_decision": None,
        "audit_log": [{"timestamp": datetime.now(timezone.utc).isoformat(), "node": "generate_draft", "action": "draft_created", "details": {"iteration": loop_count + 1, "table_comment_length": len(draft_table_comment), "columns_commented": len(draft_column_comments)}}],
    }

@mlflow.trace(name="node.evaluate_quality")
def evaluate_quality(state):
    table_info = state["table_info"]
    draft_table_comment = state["draft_table_comment"]
    draft_column_comments = state.get("draft_column_comments", {})
    column_tags = state.get("column_tags")

    # Build user prompt
    parts = []
    parts.append(f"## Tabla: `{table_info.get('full_name', 'unknown')}`")
    parts.append(f"- Tipo: {table_info.get('table_type', 'N/A')}")
    parts.append("\n## Schema de Columnas (referencia)")
    for col in table_info.get("columns", []):
        parts.append(f"- `{col['name']}` ({col.get('type', 'N/A')})")
    if column_tags:
        parts.append("\n## Tags de Sensibilidad")
        for tag in column_tags:
            parts.append(f"- `{tag['nombre_columna']}`: {tag['tag_clave']}={tag['tag_valor']}")
    parts.append("\n---\n## DRAFT A EVALUAR\n")
    parts.append(f"### Comentario de Tabla\n{draft_table_comment}")
    parts.append("\n### Comentarios de Columnas")
    for col_name, comment in draft_column_comments.items():
        parts.append(f"- **`{col_name}`**: {comment}")

    user_prompt = "\n".join(parts)
    raw_response = call_llm(QUALITY_SYSTEM_PROMPT, user_prompt)

    try:
        parsed = parse_json_response(raw_response)
        pillar_scores = parsed.get("pillar_scores", {})
        quality_score = parsed.get("quality_score", 0.0)
        findings = parsed.get("findings", [])
        for key in ["clarity", "purpose", "detail", "context"]:
            if key not in pillar_scores:
                pillar_scores[key] = 0.0
            pillar_scores[key] = max(0.0, min(1.0, float(pillar_scores[key])))
        quality_score = sum(pillar_scores.values()) / max(len(pillar_scores), 1)
        quality_score = round(quality_score, 3)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        log.error("Failed to parse quality evaluation: %s", e)
        pillar_scores = {"clarity": 0.0, "purpose": 0.0, "detail": 0.0, "context": 0.0}
        quality_score = 0.0
        findings = [f"Error parsing quality evaluation: {e}"]

    return {
        "quality_score": quality_score,
        "pillar_scores": pillar_scores,
        "quality_findings": findings,
        "workflow_status": "quality_evaluated",
        "audit_log": [{"timestamp": datetime.now(timezone.utc).isoformat(), "node": "evaluate_quality", "action": "quality_scored", "details": {"quality_score": quality_score, "pillar_scores": pillar_scores, "findings_count": len(findings)}}],
    }

@mlflow.trace(name="node.reflect_governance")
def reflect_governance(state):
    draft_table_comment = state["draft_table_comment"]
    draft_column_comments = state.get("draft_column_comments", {})
    quality_score = state.get("quality_score", 0.0)
    pillar_scores = state.get("pillar_scores", {})
    table_info = state["table_info"]
    column_tags = state.get("column_tags")

    # Build governance system prompt
    principles_lines = []
    for p in GOVERNANCE_PRINCIPLES:
        principles_lines.append(f"### {p['id']}. {p['name']}\n{p['rule']}\n")
    principles_text = "\n".join(principles_lines)
    system = GOVERNANCE_SYSTEM_PROMPT_TEMPLATE.format(principles_text=principles_text)

    # Build user prompt
    parts = []
    parts.append(f"## Tabla: `{table_info.get('full_name', 'unknown')}`")
    parts.append(f"- Quality Score: {quality_score:.2f}")
    parts.append("- Pillar Scores:")
    for k, v in pillar_scores.items():
        parts.append(f"  - {k}: {v:.2f}")
    if column_tags:
        parts.append("\n## Tags de Sensibilidad")
        for tag in column_tags:
            parts.append(f"- `{tag['nombre_columna']}`: {tag['tag_clave']}={tag['tag_valor']}")
    parts.append(f"\n## Comentario de Tabla\n{draft_table_comment}")
    parts.append("\n## Comentarios de Columnas")
    total_cols = len(table_info.get("columns", []))
    commented_cols = len(draft_column_comments)
    parts.append(f"({commented_cols}/{total_cols} columnas con comentario)")
    for col_name, comment in draft_column_comments.items():
        parts.append(f"- **`{col_name}`**: {comment}")
    existing_col_names = {c["name"] for c in table_info.get("columns", [])}
    commented_names = set(draft_column_comments.keys())
    missing = existing_col_names - commented_names
    if missing:
        parts.append(f"\n⚠️ Columnas SIN comentario: {', '.join(sorted(missing))}")

    user_prompt = "\n".join(parts)
    raw_response = call_llm(system, user_prompt)

    try:
        parsed = parse_json_response(raw_response)
        governance_status = parsed.get("governance_status", "needs_review")
        findings = parsed.get("findings", [])
        recommendation = parsed.get("recommendation", "")
        if governance_status not in ("pass", "fail", "needs_review"):
            governance_status = "needs_review"
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        log.error("Failed to parse governance reflection: %s", e)
        governance_status = "needs_review"
        findings = [f"Error parsing governance reflection: {e}"]
        recommendation = "Cannot evaluate governance — review required."

    return {
        "governance_status": governance_status,
        "governance_findings": findings,
        "workflow_status": "governance_evaluated",
        "audit_log": [{"timestamp": datetime.now(timezone.utc).isoformat(), "node": "reflect_governance", "action": "governance_evaluated", "details": {"governance_status": governance_status, "findings_count": len(findings), "recommendation": recommendation}}],
    }

@mlflow.trace(name="node.human_review")
def human_review(state):
    """Auto-approve HITL step for MVP (no checkpointer)."""
    log.info("HITL auto-approved (MVP mode, no checkpointer)")
    return {
        "human_decision": "approve",
        "human_feedback": "Auto-approved in MVP mode.",
        "workflow_status": "human_approve",
        "audit_log": [{"timestamp": datetime.now(timezone.utc).isoformat(), "node": "human_review", "action": "steward_reviewed", "details": {"decision": "approve", "mode": "auto_mvp"}}],
    }

@mlflow.trace(name="node.publish_uc")
def publish_uc(state):
    fqn = state["asset_fqn"]
    table_comment = state.get("draft_table_comment", "")
    column_comments = state.get("draft_column_comments", {})
    errors = []
    if table_comment:
        result = publish_table_comment(fqn, table_comment)
        if result.get("status") != "success":
            errors.append(f"Table comment: {result.get('error', 'unknown error')}")
    if column_comments:
        result = publish_column_comments(fqn, column_comments)
        if result.get("failures"):
            for fail in result["failures"]:
                errors.append(f"Column '{fail['column']}': {fail.get('error', 'unknown')}")
    if errors:
        workflow_status = "publish_failed"
    else:
        workflow_status = "published"
    return {
        "workflow_status": workflow_status,
        "audit_log": [{"timestamp": datetime.now(timezone.utc).isoformat(), "node": "publish_uc", "action": "metadata_published", "details": {"status": workflow_status, "asset_fqn": fqn, "errors": errors}}],
    }

@mlflow.trace(name="node.finalize_success")
def finalize_success(state):
    return {
        "workflow_status": "completed_success",
        "audit_log": [{"timestamp": datetime.now(timezone.utc).isoformat(), "node": "finalize_success", "action": "workflow_completed", "details": {"asset_fqn": state.get("asset_fqn", ""), "final_quality_score": state.get("quality_score", 0.0), "total_loops": state.get("loop_count", 0)}}],
    }

@mlflow.trace(name="node.finalize_failed")
def finalize_failed(state):
    reason = "unknown"
    if state.get("loop_count", 0) >= 3:
        reason = "max_loops_exceeded"
    elif state.get("human_decision") == "reject":
        reason = "steward_rejected"
    elif state.get("workflow_status") == "publish_failed":
        reason = "publish_error"
    elif state.get("quality_score", 0.0) < 0.4:
        reason = "low_quality_persistent"
    return {
        "workflow_status": f"completed_failed_{reason}",
        "audit_log": [{"timestamp": datetime.now(timezone.utc).isoformat(), "node": "finalize_failed", "action": "workflow_failed", "details": {"failure_reason": reason, "final_quality_score": state.get("quality_score", 0.0)}}],
    }

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CELDA 9: Router Decisions                                          ║
# ╚══════════════════════════════════════════════════════════════════════╝

def route_after_quality(state):
    score = state.get("quality_score", 0.0)
    loops = state.get("loop_count", 0)
    if score >= SETTINGS.AUTO_REFLEXION_CEILING:
        return "reflect_governance"
    if loops < SETTINGS.MAX_REFLEXION_LOOPS:
        return "generate_draft"
    return "finalize_failed"

def route_after_governance(state):
    gov_status = state.get("governance_status", "needs_review")
    score = state.get("quality_score", 0.0)
    loops = state.get("loop_count", 0)
    human_decision = state.get("human_decision")
    if gov_status == "pass":
        if human_decision == "approve" and score >= SETTINGS.PUBLISH_READY:
            return "publish_uc"
        return "human_review"
    if gov_status == "needs_review":
        return "human_review"
    if loops < SETTINGS.MAX_REFLEXION_LOOPS:
        return "generate_draft"
    return "human_review"

def route_after_hitl(state):
    decision = state.get("human_decision", "rework")
    if decision == "approve":
        return "reflect_governance"
    if decision == "rework":
        return "generate_draft"
    return "finalize_failed"

def route_after_publish(state):
    status = state.get("workflow_status", "")
    if status == "published":
        return "finalize_success"
    return "finalize_failed"

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CELDA 10: Build Graph                                              ║
# ╚══════════════════════════════════════════════════════════════════════╝

from langgraph.graph import StateGraph, START, END

def build_graph():
    builder = StateGraph(MetadataAgentState)

    # Register nodes
    builder.add_node("collect_context", collect_context)
    builder.add_node("generate_draft", generate_draft)
    builder.add_node("evaluate_quality", evaluate_quality)
    builder.add_node("reflect_governance", reflect_governance)
    builder.add_node("human_review", human_review)
    builder.add_node("publish_uc", publish_uc)
    builder.add_node("finalize_success", finalize_success)
    builder.add_node("finalize_failed", finalize_failed)

    # Deterministic edges
    builder.add_edge(START, "collect_context")
    builder.add_edge("collect_context", "generate_draft")
    builder.add_edge("generate_draft", "evaluate_quality")

    # Conditional edges
    builder.add_conditional_edges("evaluate_quality", route_after_quality, {
        "reflect_governance": "reflect_governance",
        "generate_draft": "generate_draft",
        "finalize_failed": "finalize_failed",
    })
    builder.add_conditional_edges("reflect_governance", route_after_governance, {
        "human_review": "human_review",
        "generate_draft": "generate_draft",
        "publish_uc": "publish_uc",
        "finalize_failed": "finalize_failed",
    })
    builder.add_conditional_edges("human_review", route_after_hitl, {
        "reflect_governance": "reflect_governance",
        "generate_draft": "generate_draft",
        "finalize_failed": "finalize_failed",
    })
    builder.add_conditional_edges("publish_uc", route_after_publish, {
        "finalize_success": "finalize_success",
        "finalize_failed": "finalize_failed",
    })

    # Terminal edges
    builder.add_edge("finalize_success", END)
    builder.add_edge("finalize_failed", END)

    # Compile WITHOUT checkpointer (no MemorySaver needed for MVP)
    graph = builder.compile()
    return graph

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CELDA 11: Run the Agent                                            ║
# ╚══════════════════════════════════════════════════════════════════════╝

def run_notebook(fqn):
    """Run the metadata governance workflow for a given table."""
    graph = build_graph()
    tid = str(uuid.uuid4())

    initial_state = {
        "asset_fqn": fqn,
        "request_id": str(uuid.uuid4()),
        "workflow_status": "started",
        "loop_count": 0,
        "retry_count": 0,
        "audit_log": [],
        "quality_findings": [],
        "governance_findings": [],
    }

    print(f"🚀 Starting metadata governance for: {fqn}")
    print(f"📋 Thread ID: {tid}")
    print("-" * 60)

    icons = {
        "collect_context": "🔍", "generate_draft": "✍️",
        "evaluate_quality": "📊", "reflect_governance": "🔎",
        "human_review": "👤", "publish_uc": "📤",
        "finalize_success": "✅", "finalize_failed": "❌",
    }

    result = None
    for event in graph.stream(initial_state, stream_mode="updates"):
        for node_name, node_output in event.items():
            status = node_output.get("workflow_status", "")
            score = node_output.get("quality_score")
            gov = node_output.get("governance_status")
            icon = icons.get(node_name, "⚙️")
            msg = f"{icon} [{node_name}] status={status}"
            if score is not None:
                msg += f" | quality={score:.2f}"
            if gov:
                msg += f" | governance={gov}"
            print(msg)
            result = node_output

    # Print final summary
    print("\n" + "=" * 60)
    if result:
        final_status = result.get("workflow_status", "unknown")
        if "success" in final_status:
            print(f"✅ Workflow completed: {final_status}")
        else:
            print(f"❌ Workflow ended: {final_status}")

        # Print draft if available
        if result.get("draft_table_comment"):
            print(f"\n📝 Table Comment:\n{result['draft_table_comment']}")
        if result.get("draft_column_comments"):
            print(f"\n📝 Column Comments ({len(result['draft_column_comments'])} columns):")
            for col, comment in result["draft_column_comments"].items():
                print(f"  - {col}: {comment}")
    print("=" * 60)

    return {"status": result.get("workflow_status", "unknown") if result else "error", "thread_id": tid, "result": result}

# COMMAND ----------

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CELDA 12: ▶️ EJECUTAR                                              ║
# ╚══════════════════════════════════════════════════════════════════════╝

result = run_notebook("udv_prod.sch_udv_vw.hd_dac_poliza_vig_cliente_rol_renta_core")
