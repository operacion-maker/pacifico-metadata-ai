"""
decisions.py — Pure routing functions for the state machine.

These functions contain NO side effects; they only read the state and
return the name of the next node. This makes them trivially testable.

Threshold summary:
- score < 0.4  → automatic reflexion (rework via generate_draft)
- score >= 0.4 → proceed to governance
- score >= 0.7 → trigger HITL (Data Steward review)
- score >= 0.9 → publish-ready after post-HITL governance
- max_loops = 3 → escalate to HITL or fail
"""

from __future__ import annotations

from typing import Literal

from config.settings import SETTINGS
from state.schema import MetadataAgentState


def route_after_quality(
    state: MetadataAgentState,
) -> Literal["reflect_governance", "generate_draft", "finalize_failed"]:
    """
    Route after quality evaluation.

    - score >= AUTO_REFLEXION_CEILING (0.4) → reflect_governance
    - score < 0.4 AND loops < max → generate_draft (automatic rework)
    - score < 0.4 AND loops >= max → finalize_failed
    """
    score = state.get("quality_score", 0.0)
    loops = state.get("loop_count", 0)
    max_loops = SETTINGS.MAX_REFLEXION_LOOPS

    if score >= SETTINGS.AUTO_REFLEXION_CEILING:
        return "reflect_governance"

    if loops < max_loops:
        return "generate_draft"

    return "finalize_failed"


def route_after_governance(
    state: MetadataAgentState,
) -> Literal["human_review", "generate_draft", "publish_uc", "finalize_failed"]:
    """
    Route after governance reflection.

    This router is used BOTH for the initial governance check AND the
    post-HITL governance re-evaluation.

    Decision matrix:
    - governance pass AND human already approved → publish_uc
      (avoids infinite loop when running without checkpointer / MVP mode)
    - governance pass AND quality >= PUBLISH_READY (0.9) AND not yet reviewed
      → human_review (first time, let steward confirm)
    - governance pass AND quality >= 0.4 AND not yet reviewed → human_review
    - governance needs_review AND not yet reviewed → human_review
    - governance fail AND loops < max → generate_draft (auto-rework)
    - governance fail AND loops >= max → finalize_failed
    """
    gov_status = state.get("governance_status", "needs_review")
    score = state.get("quality_score", 0.0)
    loops = state.get("loop_count", 0)
    max_loops = SETTINGS.MAX_REFLEXION_LOOPS
    human_decision = state.get("human_decision")

    if gov_status == "pass":
        # Post-HITL path: steward already reviewed (approve or any decision)
        # Go directly to publish rather than looping back to human_review.
        # This is the critical fix for the recursion loop in MVP/no-checkpointer mode.
        if human_decision == "approve":
            return "publish_uc"
        if human_decision in ("reject",):
            return "finalize_failed"
        # First pass (human_decision is None or "rework") → send for HITL
        return "human_review"

    if gov_status == "needs_review":
        # If steward already reviewed and governance still needs_review, fail
        if human_decision == "approve":
            return "publish_uc"
        return "human_review"

    # governance_status == "fail"
    if loops < max_loops:
        return "generate_draft"

    # Max loops reached — fail definitively to avoid recursion
    return "finalize_failed"


def route_after_hitl(
    state: MetadataAgentState,
) -> Literal["reflect_governance", "generate_draft", "finalize_failed"]:
    """
    Route after Data Steward HITL review.

    - approve → reflect_governance (post-HITL validation)
    - rework → generate_draft (with steward feedback)
    - reject → finalize_failed
    """
    decision = state.get("human_decision", "rework")

    if decision == "approve":
        return "reflect_governance"

    if decision == "rework":
        return "generate_draft"

    # reject
    return "finalize_failed"


def route_after_post_hitl_governance(
    state: MetadataAgentState,
) -> Literal["publish_uc", "human_review", "generate_draft"]:
    """
    Route after the governance re-evaluation that follows HITL approval.

    This is the critical gate before publication:
    - governance pass AND quality >= PUBLISH_READY (0.9) → publish_uc
    - governance pass AND quality >= 0.7 but < 0.9 → human_review (final approval)
    - governance fail OR quality < 0.7 → generate_draft (if loops allow)
    """
    gov_status = state.get("governance_status", "needs_review")
    score = state.get("quality_score", 0.0)
    loops = state.get("loop_count", 0)
    max_loops = SETTINGS.MAX_REFLEXION_LOOPS

    if gov_status == "pass" and score >= SETTINGS.PUBLISH_READY:
        return "publish_uc"

    if gov_status in ("pass", "needs_review") and score >= SETTINGS.HITL_TRIGGER:
        return "human_review"

    if loops < max_loops:
        return "generate_draft"

    return "human_review"


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
