"""
publish_uc — Deterministic node that writes approved metadata to Unity Catalog.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import mlflow

from state.schema import MetadataAgentState
from tools.unity_catalog import publish_table_comment, publish_column_comments

logger = logging.getLogger(__name__)


@mlflow.trace(name="node.publish_uc")
def publish_uc(state: MetadataAgentState) -> dict[str, Any]:
    """
    Publish the approved metadata to Unity Catalog.

    Writes:
    1. Table-level comment via ``COMMENT ON TABLE``.
    2. Column-level comments via ``ALTER TABLE ALTER COLUMN COMMENT``.

    This is a **deterministic** node — no LLM calls.
    """
    fqn = state["asset_fqn"]
    table_comment = state.get("draft_table_comment", "")
    column_comments = state.get("draft_column_comments", {})

    errors = []

    # 1. Publish table comment
    if table_comment:
        result = publish_table_comment(fqn, table_comment)
        if result.get("status") != "success":
            errors.append(f"Table comment: {result.get('error', 'unknown error')}")

    # 2. Publish column comments
    if column_comments:
        result = publish_column_comments(fqn, column_comments)
        if result.get("failures"):
            for fail in result["failures"]:
                errors.append(
                    f"Column '{fail['column']}': {fail.get('error', 'unknown')}"
                )

    if errors:
        workflow_status = "publish_failed"
        publish_detail = {"status": "error", "errors": errors}
    else:
        workflow_status = "published"
        publish_detail = {
            "status": "success",
            "table_comment_published": bool(table_comment),
            "columns_published": len(column_comments),
        }

    return {
        "workflow_status": workflow_status,
        "audit_log": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "node": "publish_uc",
                "action": "metadata_published",
                "details": {
                    **publish_detail,
                    "asset_fqn": fqn,
                    "quality_score": state.get("quality_score", 0.0),
                },
            }
        ],
    }
