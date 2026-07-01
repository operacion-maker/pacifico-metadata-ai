"""
finalize — Terminal nodes for success and failure.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import mlflow

from state.schema import MetadataAgentState


@mlflow.trace(name="node.finalize_success")
def finalize_success(state: MetadataAgentState) -> dict[str, Any]:
    """Mark the workflow as successfully completed."""
    return {
        "workflow_status": "completed_success",
        "audit_log": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "node": "finalize_success",
                "action": "workflow_completed",
                "details": {
                    "asset_fqn": state.get("asset_fqn", ""),
                    "final_quality_score": state.get("quality_score", 0.0),
                    "total_loops": state.get("loop_count", 0),
                    "governance_status": state.get("governance_status", ""),
                },
            }
        ],
    }


@mlflow.trace(name="node.finalize_failed")
def finalize_failed(state: MetadataAgentState) -> dict[str, Any]:
    """Mark the workflow as failed."""
    # Determine failure reason
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
        "audit_log": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "node": "finalize_failed",
                "action": "workflow_failed",
                "details": {
                    "asset_fqn": state.get("asset_fqn", ""),
                    "failure_reason": reason,
                    "final_quality_score": state.get("quality_score", 0.0),
                    "total_loops": state.get("loop_count", 0),
                    "governance_status": state.get("governance_status", ""),
                },
            }
        ],
    }
