"""
MetadataAgentState — the single source of truth for the LangGraph state machine.

This TypedDict travels through every node of the graph, accumulating evidence,
drafts, evaluations, governance findings, and audit entries.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict


class AuditEntry(TypedDict, total=False):
    """A single audit-log record appended at each node."""
    timestamp: str
    node: str
    action: str
    details: dict[str, Any]


class HumanFeedback(TypedDict, total=False):
    """Estructura de feedback del Data Steward (Contrato B)."""
    general_observations: str
    edited_table_comment: str
    edited_columns: dict[str, str]


class MetadataAgentState(TypedDict, total=False):
    """
    Full state for the Metadata Governance State Machine.

    Fields marked with ``Annotated[..., operator.add]`` use LangGraph's
    *reducer* pattern so that successive nodes **append** to the list
    rather than overwriting it.
    """

    # ── Identity ───────────────────────────────────────────────────────
    request_id: str
    asset_fqn: str               # catalog.schema.table

    # ── Context / Evidence (populated by collect_context) ──────────────
    table_info: dict[str, Any]          # SDK TableInfo dict
    column_details: list[dict[str, Any]]  # name, type, comment, nullable...
    profiling_summary: dict[str, Any]   # basic profiling stats
    lineage_info: list[dict[str, Any]]  # upstream + downstream lineage
    column_tags: list[dict[str, Any]]   # DAC / EDC tags

    # ── Naming-convention context (injected from modelamiento docs) ────
    naming_context: str  # condensed naming-convention knowledge for prompt

    # ── Draft Metadata ─────────────────────────────────────────────────
    draft_table_comment: str
    draft_column_comments: dict[str, str]   # {col_name: comment}
    
    # ── Governance Indicator ───────────────────────────────────────────
    governance_indicator: dict[str, Any]    # {"status": str, "compliance_notes": list[str]}

    # ── HITL (Human-In-The-Loop) ───────────────────────────────────────
    human_feedback: HumanFeedback | None
    human_decision: Literal["approve", "reject", "rework"] | None

    # ── Operational Control ────────────────────────────────────────────
    workflow_status: str            # collecting | drafting | evaluating | ...
    loop_count: int
    retry_count: int

    # ── Audit Trail ────────────────────────────────────────────────────
    audit_log: Annotated[list[AuditEntry], operator.add]
