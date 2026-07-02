"""
builder.py — Assembles the LangGraph StateGraph for the metadata governance
state machine.

Graph structure:

    START
      │
      ▼
    collect_context ──► generate_draft ──► human_review
                             ▲                  │
                             │                  │
                             └──────rework──────┤
                                                │
                                          ┌─────┴─────┐
                                          ▼           ▼
                                     publish_uc  finalize_failed
                                          │
                                    ┌─────┴─────┐
                                    ▼           ▼
                            finalize_success finalize_failed
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from state.schema import MetadataAgentState

# Nodes
from nodes.collect_context import collect_context
from nodes.generate_draft import generate_draft
from nodes.human_review import human_review
from nodes.publish_uc import publish_uc
from nodes.finalize import finalize_success, finalize_failed

# Routers
from routers.decisions import (
    route_after_hitl,
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
    builder.add_node("human_review", human_review)
    builder.add_node("publish_uc", publish_uc)
    builder.add_node("finalize_success", finalize_success)
    builder.add_node("finalize_failed", finalize_failed)

    # ── Deterministic edges ───────────────────────────────────────────
    builder.add_edge(START, "collect_context")
    builder.add_edge("collect_context", "generate_draft")
    builder.add_edge("generate_draft", "human_review")

    # ── Conditional edges ─────────────────────────────────────────────

    # After HITL
    builder.add_conditional_edges(
        "human_review",
        route_after_hitl,
        {
            "publish_uc": "publish_uc",
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
