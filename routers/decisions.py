"""
decisions.py — Pure routing functions for the state machine.

These functions contain NO side effects; they only read the state and
return the name of the next node.
"""

from __future__ import annotations

from typing import Literal

from state.schema import MetadataAgentState


def route_after_hitl(
    state: MetadataAgentState,
) -> Literal["publish_uc", "generate_draft", "finalize_failed"]:
    """
    Route after Data Steward HITL review.

    - approve → publish_uc
    - rework → generate_draft (with steward feedback / prompt anchoring)
    - reject → finalize_failed
    """
    decision = state.get("human_decision", "rework")

    if decision == "approve":
        return "publish_uc"

    if decision == "rework":
        return "generate_draft"

    # reject
    return "finalize_failed"


def route_after_publish(
    state: MetadataAgentState,
) -> Literal["finalize_success", "finalize_failed"]:
    """
    Route after publication attempt.

    - published → finalize_success
    - any error → finalize_failed
    """
    status = state.get("workflow_status", "")

    if status == "published":
        return "finalize_success"

    return "finalize_failed"
