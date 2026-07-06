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

    Behaviour depends on ``resource_status``:
    - ``"strict"`` (default): Writes table + column comments (existing behaviour).
    - ``"soft"``: Skips comment publication; instead writes a custom UC tag
      ``governance_status = "soft_draft"`` to mark the asset as pending review.
    """
    fqn = state["asset_fqn"]
    resource_status = state.get("resource_status", "strict")

    # ── Soft mode: write tag only ────────────────────────────────────
    if resource_status == "soft":
        try:
            from tools.unity_catalog import set_asset_tag
            tag_result = set_asset_tag(fqn, "governance_status", "soft_draft")
            tag_ok = tag_result.get("status") == "success"
        except Exception as e:
            logger.warning("set_asset_tag not available or failed: %s", e)
            tag_ok = False

        workflow_status = "soft_draft_saved" if tag_ok else "soft_draft_saved_no_tag"
        return {
            "workflow_status": workflow_status,
            "audit_log": [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "node": "publish_uc",
                    "action": "soft_draft_tagged",
                    "details": {
                        "asset_fqn": fqn,
                        "resource_status": "soft",
                        "tag_written": tag_ok,
                    },
                }
            ],
        }

    # ── Strict mode: full publication ────────────────────────────────
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
                    "resource_status": "strict",
                    "quality_score": state.get("quality_score", 0.0),
                },
            }
        ],
    }

