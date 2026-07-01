"""
builder.py — Assembles the LangGraph StateGraph for the metadata governance
state machine.

Graph structure:

    START
      │
      ▼
    collect_context ──► generate_draft ──► evaluate_quality
                                               │
                            ┌──────────────────┤
                            │               ┌──┘
                            ▼               ▼
                    generate_draft   reflect_governance
                     (rework loop)         │
                                    ┌──────┤──────┐
                                    ▼      ▼      ▼
                              human_review  gen.  human_review
                                    │
                              ┌─────┤─────┐
                              ▼     ▼     ▼
                       reflect_gov gen. finalize_failed
                              │
                        ┌─────┤─────┐
                        ▼     ▼     ▼
                   publish  human  gen.
                     │
                  ┌──┴──┐
                  ▼     ▼
           success  failed
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from state.schema import MetadataAgentState

# Nodes
from nodes.collect_context import collect_context
from nodes.generate_draft import generate_draft
from nodes.evaluate_quality import evaluate_quality
from nodes.reflect_governance import reflect_governance
from nodes.human_review import human_review
from nodes.publish_uc import publish_uc
from nodes.finalize import finalize_success, finalize_failed

# Routers
from routers.decisions import (
    route_after_quality,
    route_after_governance,
    route_after_hitl,
    route_after_post_hitl_governance,
    route_after_publish,
)


def build_graph(checkpointer=None):
    """
    Build and compile the metadata governance state machine.

    Parameters
    ----------
    checkpointer : optional
        LangGraph checkpointer for state persistence. Defaults to None
        to avoid serialization bugs on Databricks Serverless.

    Returns
    -------
    CompiledGraph
        The compiled LangGraph ready for ``.invoke()`` or ``.stream()``.
    """
    builder = StateGraph(MetadataAgentState)

    # ── Register nodes ────────────────────────────────────────────────
    builder.add_node("collect_context", collect_context)
    builder.add_node("generate_draft", generate_draft)
    builder.add_node("evaluate_quality", evaluate_quality)
    builder.add_node("reflect_governance", reflect_governance)
    builder.add_node("human_review", human_review)
    builder.add_node("publish_uc", publish_uc)
    builder.add_node("finalize_success", finalize_success)
    builder.add_node("finalize_failed", finalize_failed)

    # ── Deterministic edges ───────────────────────────────────────────
    builder.add_edge(START, "collect_context")
    builder.add_edge("collect_context", "generate_draft")
    builder.add_edge("generate_draft", "evaluate_quality")

    # ── Conditional edges ─────────────────────────────────────────────

    # After quality evaluation
    builder.add_conditional_edges(
        "evaluate_quality",
        route_after_quality,
        {
            "reflect_governance": "reflect_governance",
            "generate_draft": "generate_draft",
            "finalize_failed": "finalize_failed",
        },
    )

    # After governance reflection (handles both initial and post-HITL checks)
    builder.add_conditional_edges(
        "reflect_governance",
        route_after_governance,
        {
            "human_review": "human_review",
            "generate_draft": "generate_draft",
            "publish_uc": "publish_uc",
            "finalize_failed": "finalize_failed",
        },
    )

    # After HITL
    builder.add_conditional_edges(
        "human_review",
        route_after_hitl,
        {
            "reflect_governance": "reflect_governance",
            "generate_draft": "generate_draft",
            "finalize_failed": "finalize_failed",
        },
    )

    # After publish
    builder.add_conditional_edges(
        "publish_uc",
        route_after_publish,
        {
            "finalize_success": "finalize_success",
            "finalize_failed": "finalize_failed",
        },
    )

    # ── Terminal edges ────────────────────────────────────────────────
    builder.add_edge("finalize_success", END)
    builder.add_edge("finalize_failed", END)

    # ── Compile with checkpointer (required for HITL interrupt) ───────
    graph = builder.compile(checkpointer=checkpointer)

    return graph
