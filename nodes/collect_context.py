"""
collect_context — Deterministic node that gathers all evidence before drafting.

Calls UC tools to collect: table info, column details, profiling, lineage
(both upstream and downstream), and column tags.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import mlflow

from state.schema import MetadataAgentState
from tools.unity_catalog import (
    get_table_info,
    get_column_details,
    get_column_tags,
    get_lineage,
    get_profiling_summary,
)


# ── Module detection from schema naming conventions ───────────────────
# The lineage function expects module names as they appear in the
# modelamiento catalog: RAW, UNIVERSAL, ANALYTICS — NOT the conceptual
# names (Bronze, Silver, Gold) which are only documentation references.

_SCHEMA_TO_MODULE = {
    "rdv": "RAW",         # Raw Data Vault → RAW module
    "udv": "UNIVERSAL",   # Universal Data Vault → UNIVERSAL module
    "ddv": "ANALYTICS",   # Data-Driven Vault → ANALYTICS module
}


def _detect_module(fqn: str) -> str:
    """
    Detect the lakehouse module from the catalog/schema naming convention.

    Examples
    --------
    >>> _detect_module("udv_prod.sch_udv_vw.hd_dac_poliza_vig_...")
    'UNIVERSAL'
    >>> _detect_module("ddv_prod.sch_ddv_tb.ft_produccion")
    'ANALYTICS'
    """
    parts = fqn.lower().split(".")
    catalog = parts[0] if parts else ""

    # Check catalog prefix: udv_prod, rdv_prod, ddv_prod
    for prefix, module in _SCHEMA_TO_MODULE.items():
        if catalog.startswith(prefix):
            return module

    # Fallback: check schema if catalog doesn't match
    if len(parts) > 1:
        schema = parts[1]
        for prefix, module in _SCHEMA_TO_MODULE.items():
            if prefix in schema:
                return module

    # Default to UNIVERSAL (most common for governance)
    return "UNIVERSAL"


@mlflow.trace(name="node.collect_context")
def collect_context(state: MetadataAgentState) -> dict[str, Any]:
    """
    Collect all technical evidence for the given asset.

    This is a **deterministic** node — no LLM calls, only tool invocations.
    """
    fqn = state["asset_fqn"]
    parts = fqn.split(".")
    table_short_name = parts[-1] if parts else fqn

    # 1. Table metadata via SDK
    table_info = get_table_info(fqn)

    # 2. Column details via DESCRIBE
    column_details = get_column_details(fqn)

    # 3. Column tags (DAC, EDC)
    column_tags = get_column_tags(fqn)

    # 4. Lineage — detect the correct module and fetch BOTH directions
    module_name = _detect_module(fqn)

    lineage_upstream = get_lineage(
        table_name=table_short_name,
        module_name=module_name,
        direction="UP",
    )
    lineage_downstream = get_lineage(
        table_name=table_short_name,
        module_name=module_name,
        direction="DOWN",
    )

    # Combine upstream and downstream with direction markers
    lineage_info = []
    for entry in lineage_upstream:
        entry["lineage_direction"] = "upstream"
        lineage_info.append(entry)
    for entry in lineage_downstream:
        entry["lineage_direction"] = "downstream"
        lineage_info.append(entry)

    # 5. Profiling
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
        "audit_log": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "node": "collect_context",
                "action": "evidence_collected",
                "details": {
                    "asset_fqn": fqn,
                    "columns_found": len(column_details),
                    "tags_found": len(column_tags),
                    "lineage_upstream": len(lineage_upstream),
                    "lineage_downstream": len(lineage_downstream),
                    "module_detected": module_name,
                    "row_count": profiling_summary.get("row_count", 0),
                },
            }
        ],
    }

