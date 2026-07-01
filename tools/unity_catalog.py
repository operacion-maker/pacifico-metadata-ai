"""
Unity Catalog Tools — read/write metadata against Databricks UC.

These functions are designed to run **inside a Databricks notebook**
where ``spark`` is available in the global scope.  For local testing,
callers must inject a mock ``spark`` session.

All functions are decorated with ``@mlflow.trace`` so that every call
is captured in the MLflow trace viewer.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import mlflow
from config.settings import SETTINGS

logger = logging.getLogger(__name__)


def _get_spark():
    """Retrieve the active SparkSession (Databricks notebook context)."""
    try:
        from pyspark.sql import SparkSession
        return SparkSession.getActiveSession()
    except ImportError:
        raise RuntimeError(
            "PySpark is not available. "
            "This tool must run inside a Databricks cluster."
        )


# ── READ TOOLS ────────────────────────────────────────────────────────


@mlflow.trace(name="tool.get_table_info")
def get_table_info(fqn: str) -> dict[str, Any]:
    """
    Fetch table-level metadata from Unity Catalog.

    Uses the Databricks SDK ``WorkspaceClient().tables.get()`` to retrieve
    table info including columns, data types, and existing comments.

    Parameters
    ----------
    fqn : str
        Fully-qualified table name: ``catalog.schema.table``.

    Returns
    -------
    dict
        Keys: table_name, catalog, schema, table_type, comment,
              columns (list of dicts with name, type, comment, nullable).
    """
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
            "data_source_format": (
                str(ti.data_source_format) if ti.data_source_format else None
            ),
        }
    except Exception as e:
        logger.error("get_table_info failed for %s: %s", fqn, e)
        raise


@mlflow.trace(name="tool.get_column_details")
def get_column_details(fqn: str) -> list[dict[str, Any]]:
    """
    Get detailed column metadata via ``DESCRIBE TABLE EXTENDED``.

    Parameters
    ----------
    fqn : str
        Fully-qualified table name.

    Returns
    -------
    list[dict]
        Each dict has keys: col_name, data_type, comment.
    """
    spark = _get_spark()
    rows = spark.sql(f"DESCRIBE TABLE EXTENDED {fqn}").collect()

    columns = []
    for row in rows:
        name = row["col_name"]
        
        # Stop completely when we reach the metadata sections
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
def get_column_tags(fqn: str) -> list[dict[str, Any]]:
    """
    Retrieve column-level tags (e.g. DAC, EDC) from the governance layer.

    Parameters
    ----------
    fqn : str
        Fully-qualified table name.

    Returns
    -------
    list[dict]
        Each dict: nombre_columna, tag_clave, tag_valor.
    """
    spark = _get_spark()
    parts = fqn.split(".")
    if len(parts) != 3:
        return []

    catalog, schema, table = parts
    query = f"""
        SELECT nombre_columna, tag_clave, tag_valor
        FROM {SETTINGS.UC_COLUMNAS_TAGS}
        WHERE nombre_catalog  = '{catalog}'
          AND nombre_esquema  = '{schema}'
          AND nombre_tabla    = '{table}'
    """
    try:
        rows = spark.sql(query).collect()
        return [row.asDict() for row in rows]
    except Exception as e:
        logger.warning("get_column_tags failed for %s: %s", fqn, e)
        return []


@mlflow.trace(name="tool.get_lineage")
def get_lineage(
    table_name: str,
    module_name: str = "Silver",
    direction: str = "UP",
) -> list[dict[str, Any]]:
    """
    Get lineage information using the lakehouse lineage function.

    Parameters
    ----------
    table_name : str
        Short table name (not FQN).
    module_name : str
        Layer/module: ``Silver``, ``Gold``, etc.
    direction : str
        ``UP`` for upstream, ``DOWN`` for downstream.

    Returns
    -------
    list[dict]
        Each dict: trg_name, module_name, domain_name, squad_name, level.
    """
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
        logger.warning("get_lineage failed for %s: %s", table_name, e)
        return []


@mlflow.trace(name="tool.get_profiling_summary")
def get_profiling_summary(fqn: str) -> dict[str, Any]:
    """
    Generate a basic profiling summary for a table.

    Computes per-column: count, nulls, distinct count, and sample values.
    Designed to run efficiently on large tables by sampling.

    Parameters
    ----------
    fqn : str
        Fully-qualified table name.

    Returns
    -------
    dict
        Keys: row_count, column_profiles (list of dicts per column).
    """
    spark = _get_spark()
    sample_n = SETTINGS.PROFILING_SAMPLE_ROWS

    try:
        # Total count
        total_count = spark.sql(f"SELECT COUNT(*) AS cnt FROM {fqn}").first()["cnt"]

        # Sample the table
        sample_df = spark.sql(f"SELECT * FROM {fqn} LIMIT {sample_n}")
        columns_info = sample_df.dtypes  # list of (name, dtype)

        profiles = []
        for col_name, col_type in columns_info:
            # Skip technical audit columns for brevity
            if col_name in ("codapp", "feccargainfo", "periododia"):
                continue

            stats = sample_df.selectExpr(
                f"COUNT(`{col_name}`) AS non_null",
                f"SUM(CASE WHEN `{col_name}` IS NULL THEN 1 ELSE 0 END) AS null_count",
                f"COUNT(DISTINCT `{col_name}`) AS distinct_count",
            ).first()

            # Grab a few sample values (up to 5)
            sample_vals = (
                sample_df
                .select(col_name)
                .where(f"`{col_name}` IS NOT NULL")
                .distinct()
                .limit(5)
                .collect()
            )
            sample_values = [str(r[0]) for r in sample_vals]

            profiles.append({
                "column": col_name,
                "type": col_type,
                "non_null": int(stats["non_null"]),
                "null_count": int(stats["null_count"]),
                "null_pct": round(
                    stats["null_count"] / sample_n * 100 if sample_n else 0, 1
                ),
                "distinct_count": int(stats["distinct_count"]),
                "sample_values": sample_values,
            })

        return {
            "row_count": int(total_count),
            "sample_size": sample_n,
            "column_profiles": profiles,
        }

    except Exception as e:
        logger.warning("get_profiling_summary failed for %s: %s", fqn, e)
        return {"row_count": 0, "sample_size": 0, "column_profiles": []}


# ── WRITE TOOLS ───────────────────────────────────────────────────────


@mlflow.trace(name="tool.publish_table_comment")
def publish_table_comment(fqn: str, comment: str) -> dict[str, Any]:
    """
    Set or update the table-level comment in Unity Catalog.

    Uses ``COMMENT ON TABLE`` SQL.

    Parameters
    ----------
    fqn : str
        Fully-qualified table name.
    comment : str
        The comment text to publish.

    Returns
    -------
    dict
        Status: ``{"status": "success"}`` or error details.
    """
    spark = _get_spark()
    escaped = comment.replace("'", "\\'").replace("\n", " ")
    try:
        spark.sql(f"COMMENT ON TABLE {fqn} IS '{escaped}'")
        logger.info("Published table comment for %s", fqn)
        return {"status": "success", "fqn": fqn, "type": "table_comment"}
    except Exception as e:
        logger.error("publish_table_comment failed: %s", e)
        return {"status": "error", "error": str(e), "fqn": fqn}


@mlflow.trace(name="tool.publish_column_comments")
def publish_column_comments(
    fqn: str,
    comments: dict[str, str],
) -> dict[str, Any]:
    """
    Set or update column-level comments in Unity Catalog.

    Uses ``ALTER TABLE … ALTER COLUMN … COMMENT`` SQL for each column.

    Parameters
    ----------
    fqn : str
        Fully-qualified table name.
    comments : dict[str, str]
        Mapping of column_name → comment text.

    Returns
    -------
    dict
        Aggregated result with successes and failures.
    """
    spark = _get_spark()
    results = {"successes": [], "failures": []}

    for col_name, comment in comments.items():
        escaped = comment.replace("'", "\\'").replace("\n", " ")
        try:
            spark.sql(
                f"ALTER TABLE {fqn} ALTER COLUMN `{col_name}` "
                f"COMMENT '{escaped}'"
            )
            results["successes"].append(col_name)
        except Exception as e:
            logger.error("Failed to set comment for %s.%s: %s", fqn, col_name, e)
            results["failures"].append({"column": col_name, "error": str(e)})

    results["status"] = "success" if not results["failures"] else "partial"
    return results
