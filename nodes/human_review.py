"""
human_review — HITL node that pauses the graph for Data Steward review.

Uses LangGraph's ``interrupt()`` to halt execution and present the current
state to a human reviewer.  The graph persists its state via
``MemorySaver`` and resumes when the Data Steward calls
``resume_with_feedback()`` from the next notebook cell.

How it works internally
~~~~~~~~~~~~~~~~~~~~~~~~
1. ``interrupt(payload)`` raises ``GraphInterrupt`` internally.
2. LangGraph catches it **above** this function, saves state to the
   checkpointer, and stops the stream.
3. ``run_notebook()`` detects the pause and prints the review payload.
4. The Data Steward calls ``resume_with_feedback(thread_id, decision, feedback)``.
5. LangGraph restores state and re-enters this function: this time
   ``interrupt()`` **returns** the resume value (the dict with
   decision + feedback).
6. The rest of this function processes the decision normally.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import mlflow
from langgraph.types import interrupt

from state.schema import MetadataAgentState

logger = logging.getLogger("metadata_governance")


def _build_review_payload(state: MetadataAgentState) -> dict[str, Any]:
    """Build a human-readable payload for the Data Steward."""
    return {
        "asset_fqn": state.get("asset_fqn", ""),
        "quality_score": state.get("quality_score", 0.0),
        "pillar_scores": state.get("pillar_scores", {}),
        "governance_status": state.get("governance_status", "unknown"),
        "draft_table_comment": state.get("draft_table_comment", ""),
        "draft_column_comments": state.get("draft_column_comments", {}),
        "quality_findings": state.get("quality_findings", []),
        "governance_findings": state.get("governance_findings", []),
        "loop_count": state.get("loop_count", 0),
        "instructions": (
            "Revise el draft de metadatos y responda con un JSON:\n"
            '{"decision": "approve|reject|rework", '
            '"feedback": "su retroalimentación aquí"}\n\n'
            "- approve: El draft es aceptable, continuar con validación.\n"
            "- rework: El draft necesita mejoras (incluya feedback detallado).\n"
            "- reject: Rechazar definitivamente este draft."
        ),
    }


@mlflow.trace(name="node.human_review")
def human_review(state: MetadataAgentState) -> dict[str, Any]:
    """
    Pause execution for human Data Steward review.

    On the first call, ``interrupt(payload)`` raises ``GraphInterrupt``
    which LangGraph catches to pause the graph.  On resume,
    ``interrupt()`` returns the value passed via ``Command(resume=...)``.
    """
    payload = _build_review_payload(state)

    # ── This call PAUSES the graph ──────────────────────────────────
    # interrupt() raises GraphInterrupt → LangGraph catches it above,
    # saves state to MemorySaver, and stops the stream.
    # On resume, interrupt() RETURNS the dict the steward provided.
    human_input = interrupt(payload)

    # ── After resumption: process the steward's response ────────────
    logger.info("Data Steward responded — processing feedback")

    if isinstance(human_input, str):
        try:
            human_input = json.loads(human_input)
        except json.JSONDecodeError:
            human_input = {"decision": "rework", "feedback": human_input}

    decision = human_input.get("decision", "rework")
    feedback = human_input.get("feedback", "")

    # Validate decision
    if decision not in ("approve", "reject", "rework"):
        decision = "rework"

    return {
        "human_decision": decision,
        "human_feedback": feedback,
        "workflow_status": f"human_{decision}",
        "audit_log": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "node": "human_review",
                "action": "steward_reviewed",
                "details": {
                    "decision": decision,
                    "feedback_length": len(feedback),
                    "quality_score_at_review": state.get("quality_score", 0.0),
                },
            }
        ],
    }

