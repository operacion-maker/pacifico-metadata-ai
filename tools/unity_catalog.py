"""
Unity Catalog Tools — read/write metadata against Databricks UC.
Adaptado para Serverless Model Serving utilizando Databricks SQL Warehouses.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import mlflow
from config.settings import SETTINGS

logger = logging.getLogger(__name__)

def _get_execution_context():
    """
    Retorna una sesión de Spark (si corres interactivamente en un Notebook)
    o una conexión Databricks SQL (si corre en un Endpoint de Model Serving).
    """
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.getActiveSession()
        if spark is not None:
            return ("spark", spark)
    except ImportError:
        pass
        
    # Conexión al SQL Warehouse (Endpoint)
    import os
    from databricks import sql

    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")

    if not all([host, token, warehouse_id]):
        raise RuntimeError(
            "Faltan variables de entorno. Define DATABRICKS_HOST, DATABRICKS_TOKEN y DATABRICKS_SQL_WAREHOUSE_ID."
        )

    server_hostname = host.replace("https://", "").replace("http://", "").rstrip("/")
    http_path = f"/sql/1.0/warehouses/{warehouse_id}"

    conn = sql.connect(
        server_hostname=server_hostname,
        http_path=http_path,
        access_token=token
    )
    return ("sql", conn)

def _run_query(query: str, fetch_all=True):
    """Helper para ejecutar comandos SQL únicos abstraídos del contexto."""
    ctx_type, ctx = _get_execution_context()
    try:
        if ctx_type == "spark":
            df = ctx.sql(query)
            if not fetch_all:
                row = df.first()
                return row.asDict() if row else None
            return [row.asDict() for row in df.collect()]
        else:
            with ctx.cursor() as cursor:
                cursor.execute(query)
                if cursor.description is None:
                    return None
                columns = [desc[0] for desc in cursor.description]
                if not fetch_all:
                    row = cursor.fetchone()
                    return dict(zip(columns, row)) if row else None
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    finally:
        if ctx_type == "sql":
            ctx.close()

# ── READ TOOLS ────────────────────────────────────────────────────────

@mlflow.trace(name="tool.get_table_info")
def get_table_info(fqn: str) -> dict[str, Any]:
    try:
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
    except Exception as e:
        logger.error("get_table_info failed for %s: %s", fqn, e)
        raise

@mlflow.trace(name="tool.get_column_details")
def get_column_details(fqn: str) -> list[dict[str, Any]]:
    rows = _run_query(f"DESCRIBE TABLE EXTENDED {fqn}")
    
    columns = []
    for row in rows:
        name = row.get("col_name")
        if name and (name.startswith("#") or name == "Detailed Table Information"):
            break
        if not name or name.strip() == "" or name.startswith("--"):
            continue
            
        columns.append({
            "col_name": name,
            "data_type": row.get("data_type", ""),
            "comment": row.get("comment", ""),
        })
    return columns

@mlflow.trace(name="tool.get_column_tags")
def get_column_tags(fqn: str) -> list[dict[str, Any]]:
    parts = fqn.split(".")
    if len(parts) != 3:
        return []

    catalog, schema, table = parts
    query = f"""
        SELECT nombre_columna, tag_clave, tag_valor
        FROM {SETTINGS.UC_COLUMNAS_TAGS}
        WHERE nombreuc_nivel_uno  = '{catalog}' 
          AND nombreuc_nivel_dos  = '{schema}' 
          AND nombre_tabla    = '{table}'
    """
    try:
        return _run_query(query)
    except Exception as e:
        logger.warning("get_column_tags failed for %s: %s", fqn, e)
        return []

@mlflow.trace(name="tool.get_lineage")
def get_lineage(table_name: str, module_name: str = "Silver", direction: str = "UP") -> list[dict[str, Any]]:
    query = f"SELECT * FROM {SETTINGS.UC_LINEAGE_FUNCTION}('{table_name}', '{module_name}', '{direction}')"
    try:
        return _run_query(query)
    except Exception as e:
        logger.warning("get_lineage failed for %s: %s", table_name, e)
        return []

@mlflow.trace(name="tool.get_profiling_summary")
def get_profiling_summary(fqn: str) -> dict[str, Any]:
    sample_n = SETTINGS.PROFILING_SAMPLE_ROWS
    ctx_type, ctx = _get_execution_context()
    
    try:
        if ctx_type == "spark":
            # Ejecución nativa por PySpark (Testing local en Notebooks)
            total_count = ctx.sql(f"SELECT COUNT(*) AS cnt FROM {fqn}").first()["cnt"]
            sample_df = ctx.sql(f"SELECT * FROM {fqn} LIMIT {sample_n}")
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

                sample_vals = sample_df.select(col_name).where(f"`{col_name}` IS NOT NULL").distinct().limit(5).collect()
                
                profiles.append({
                    "column": col_name,
                    "type": col_type,
                    "non_null": int(stats["non_null"]),
                    "null_count": int(stats["null_count"]),
                    "null_pct": round(stats["null_count"] / sample_n * 100 if sample_n else 0, 1),
                    "distinct_count": int(stats["distinct_count"]),
                    "sample_values": [str(r[0]) for r in sample_vals],
                })
        else:
            # Ejecución por SQL Warehouse vía API DBAPI (Model Serving Endpoint)
            from databricks.sdk import WorkspaceClient
            w = WorkspaceClient()
            ti = w.tables.get(full_name=fqn)
            
            with ctx.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {fqn}")
                total_count = cursor.fetchone()[0]
                
                profiles = []
                for col in ti.columns:
                    col_name = col.name
                    if col_name in ("codapp", "feccargainfo", "periododia"): 
                        continue
                    
                    # Generación de métricas con sentencias SQL puras
                    cursor.execute(f"SELECT COUNT(`{col_name}`), SUM(CASE WHEN `{col_name}` IS NULL THEN 1 ELSE 0 END), COUNT(DISTINCT `{col_name}`) FROM (SELECT `{col_name}` FROM {fqn} LIMIT {sample_n})")
                    stats_row = cursor.fetchone()
                    
                    cursor.execute(f"SELECT DISTINCT `{col_name}` FROM (SELECT `{col_name}` FROM {fqn} LIMIT {sample_n}) WHERE `{col_name}` IS NOT NULL LIMIT 5")
                    sample_vals = [str(r[0]) for r in cursor.fetchall()]
                    
                    profiles.append({
                        "column": col_name,
                        "type": str(col.type_text),
                        "non_null": int(stats_row[0]) if stats_row[0] else 0,
                        "null_count": int(stats_row[1]) if stats_row[1] else 0,
                        "null_pct": round(int(stats_row[1]) / sample_n * 100 if stats_row[1] and sample_n else 0, 1),
                        "distinct_count": int(stats_row[2]) if stats_row[2] else 0,
                        "sample_values": sample_vals,
                    })

        return {
            "row_count": int(total_count),
            "sample_size": sample_n,
            "column_profiles": profiles,
        }
    except Exception as e:
        logger.warning("get_profiling_summary failed for %s: %s", fqn, e)
        return {"row_count": 0, "sample_size": 0, "column_profiles": []}
    finally:
        if ctx_type == "sql":
            ctx.close()

# ── WRITE TOOLS ───────────────────────────────────────────────────────

@mlflow.trace(name="tool.publish_table_comment")
def publish_table_comment(fqn: str, comment: str) -> dict[str, Any]:
    escaped = comment.replace("'", "\\'").replace("\n", " ")
    try:
        _run_query(f"COMMENT ON TABLE {fqn} IS '{escaped}'")
        logger.info("Published table comment for %s", fqn)
        return {"status": "success", "fqn": fqn, "type": "table_comment"}
    except Exception as e:
        logger.error("publish_table_comment failed: %s", e)
        return {"status": "error", "error": str(e), "fqn": fqn}

@mlflow.trace(name="tool.publish_column_comments")
def publish_column_comments(fqn: str, comments: dict[str, str]) -> dict[str, Any]:
    results = {"successes": [], "failures": []}
    for col_name, comment in comments.items():
        escaped = comment.replace("'", "\\'").replace("\n", " ")
        try:
            _run_query(f"ALTER TABLE {fqn} ALTER COLUMN `{col_name}` COMMENT '{escaped}'")
            results["successes"].append(col_name)
        except Exception as e:
            logger.error("Failed to set comment for %s.%s: %s", fqn, col_name, e)
            results["failures"].append({"column": col_name, "error": str(e)})

    results["status"] = "success" if not results["failures"] else "partial"
    return results