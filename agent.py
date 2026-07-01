"""
agent.py — Orchestrator for the Metadata Governance pipeline.

This module provides two interfaces:

1. ``run_notebook(fqn)`` — Primary entry point for Databricks notebooks.
   Runs the full pipeline and **pauses** at ``human_review`` so the Data
   Steward can provide feedback before publication.
2. ``resume_with_feedback(thread_id, decision, feedback)`` — Resumes the
   graph after the Data Steward reviews the draft.
3. ``MetadataGovernanceAgent`` — Future wrapper for Model Serving.

HITL (Human-in-the-Loop) Flow
------------------------------
The graph uses ``MemorySaver`` as an in-memory checkpointer, which keeps
state alive as long as the Databricks notebook kernel is running.  This
enables the following interactive workflow:

**Celda A — Lanzar el agente:**
```python
from agent import run_notebook
result = run_notebook("catalog.schema.table")
# → Graph pauses at human_review, shows the review payload.
# → result["thread_id"] is needed for the next step.
```

**Celda B — Dar feedback (approve / rework / reject):**
```python
from agent import resume_with_feedback
result = resume_with_feedback(
    thread_id=result["thread_id"],
    decision="approve",       # or "rework" or "reject"
    feedback="Agregar mención al ramo SBS en el comentario de tabla."
)
```

If you choose ``rework``, the graph will regenerate → re-evaluate →
re-check governance → and pause again for another review cycle.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Generator

import mlflow

from graph.builder import build_graph
from state.schema import MetadataAgentState

logger = logging.getLogger(__name__)

# Autologging removed due to incompatibility with LangChain >= 0.3.0
# (It causes AttributeError on 'langchain.debug' and crashes the Databricks kernel)


# ── Global graph instance (singleton for notebook use) ────────────────
_GRAPH = None
_CHECKPOINTER = None


def _get_graph():
    """
    Get or create the compiled graph (singleton).

    Uses ``MemorySaver`` as checkpointer so that ``interrupt()`` in the
    ``human_review`` node can persist state and resume later via
    ``resume_with_feedback()``.  MemorySaver keeps state in process
    memory — perfect for interactive Databricks notebooks where the
    kernel stays alive between cells.
    """
    global _GRAPH, _CHECKPOINTER
    if _GRAPH is None:
        from langgraph.checkpoint.memory import MemorySaver

        _CHECKPOINTER = MemorySaver()
        _GRAPH = build_graph(checkpointer=_CHECKPOINTER)
    return _GRAPH


def reset_graph():
    """
    Force re-creation of the graph on next call to ``_get_graph()``.

    Useful after code changes or when you want a fresh MemorySaver
    (clears all stored thread states).
    """
    global _GRAPH, _CHECKPOINTER
    _GRAPH = None
    _CHECKPOINTER = None
    print("🔄 Graph reset — will be re-created on next run.")


# ── Notebook Runner ───────────────────────────────────────────────────


def run_notebook(
    fqn: str,
    thread_id: str | None = None,
) -> dict[str, Any]:
    """
    Run the metadata governance workflow for a given table.

    This is the primary entry point for the MVP notebook experience.

    Parameters
    ----------
    fqn : str
        Fully-qualified table name: ``catalog.schema.table``.
    thread_id : str, optional
        Thread ID for state persistence. Auto-generated if not provided.

    Returns
    -------
    dict
        Final state of the workflow, including audit_log, scores, and
        the draft metadata.

    Notes
    -----
    If the graph reaches the HITL (human_review) node, it will interrupt
    and this function returns the interrupt payload. Use
    ``resume_with_feedback()`` to continue.
    """
    graph = _get_graph()
    tid = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": tid}}

    initial_state: MetadataAgentState = {
        "asset_fqn": fqn,
        "request_id": str(uuid.uuid4()),
        "workflow_status": "started",
        "loop_count": 0,
        "retry_count": 0,
        "audit_log": [],
        "quality_findings": [],
        "governance_findings": [],
    }

    print(f"🚀 Starting metadata governance for: {fqn}")
    print(f"📋 Thread ID: {tid}")
    print("-" * 60)

    result = None
    interrupt_payload = None
    for event in graph.stream(initial_state, config, stream_mode="updates"):
        for node_name, node_output in event.items():
            # When a node raises GraphInterrupt (e.g., human_review with
            # a checkpointer), LangGraph emits the interrupt value as a
            # tuple instead of a dict.  We detect this and skip the
            # normal progress display.
            if not isinstance(node_output, dict):
                # node_output is the interrupt tuple — store it for later
                interrupt_payload = node_output
                print(f"⏸️  [{node_name}] — interrupt received")
                continue

            status = node_output.get("workflow_status", "")
            score = node_output.get("quality_score")
            gov = node_output.get("governance_status")

            # Display progress
            icon = _get_node_icon(node_name)
            msg = f"{icon} [{node_name}] status={status}"
            if score is not None:
                msg += f" | quality={score:.2f}"
            if gov:
                msg += f" | governance={gov}"
            print(msg)

            result = node_output

    # Check if we hit an interrupt (HITL)
    try:
        snapshot = graph.get_state(config)
        is_paused = snapshot.next
    except Exception:
        # Fallback if no checkpointer is available
        is_paused = False
        snapshot = None

    if is_paused:
        # Graph is paused at a node (likely human_review)
        print("\n" + "=" * 60)
        print("⏸️  GRAPH PAUSED — Data Steward review required")
        print(f"   Thread ID: {tid}")
        print("   Use resume_with_feedback() to continue.")
        print("=" * 60)

        # Display the interrupt payload
        if snapshot and snapshot.tasks:
            for task in snapshot.tasks:
                if hasattr(task, "interrupts") and task.interrupts:
                    for intr in task.interrupts:
                        print("\n📋 Review Payload:")
                        print(json.dumps(intr.value, indent=2, ensure_ascii=False))

        return {
            "status": "paused_for_review",
            "thread_id": tid,
            "state": dict(snapshot.values) if snapshot else {},
        }

    # Get final state — use snapshot if available, otherwise use last result
    if snapshot is not None:
        try:
            final_state = dict(snapshot.values)
        except Exception:
            final_state = result if isinstance(result, dict) else {}
    else:
        # No checkpointer — use the last node output we captured
        final_state = result if isinstance(result, dict) else {}

    print("\n" + "=" * 60)
    final_status = final_state.get("workflow_status", "unknown")
    if "success" in final_status:
        print(f"✅ Workflow completed: {final_status}")
    else:
        print(f"❌ Workflow ended: {final_status}")
    print("=" * 60)

    return {"status": final_status, "thread_id": tid, "state": final_state}


def resume_with_feedback(
    thread_id: str,
    decision: str,
    feedback: str = "",
) -> dict[str, Any]:
    """
    Resume the graph after HITL interrupt with Data Steward feedback.

    Parameters
    ----------
    thread_id : str
        The thread ID from the paused run.
    decision : str
        One of: ``approve``, ``rework``, ``reject``.
    feedback : str
        Textual feedback from the Data Steward.

    Returns
    -------
    dict
        Updated state after resumption.
    """
    from langgraph.types import Command

    graph = _get_graph()
    config = {"configurable": {"thread_id": thread_id}}

    print(f"▶️  Resuming thread {thread_id} with decision={decision}")
    print("-" * 60)

    resume_value = {"decision": decision, "feedback": feedback}

    result = None
    for event in graph.stream(
        Command(resume=resume_value), config, stream_mode="updates"
    ):
        for node_name, node_output in event.items():
            # Same guard as run_notebook: interrupt events are tuples
            if not isinstance(node_output, dict):
                print(f"⏸️  [{node_name}] — interrupt received")
                continue

            status = node_output.get("workflow_status", "")
            score = node_output.get("quality_score")
            gov = node_output.get("governance_status")
            icon = _get_node_icon(node_name)
            msg = f"{icon} [{node_name}] status={status}"
            if score is not None:
                msg += f" | quality={score:.2f}"
            if gov:
                msg += f" | governance={gov}"
            print(msg)
            result = node_output

    # Check state
    snapshot = graph.get_state(config)
    if snapshot.next:
        print("\n" + "=" * 60)
        print("⏸️  GRAPH PAUSED AGAIN — Another review required")
        print(f"   Thread ID: {thread_id}")
        print("   Use resume_with_feedback() to continue.")
        print("=" * 60)
        if snapshot.tasks:
            for task in snapshot.tasks:
                if hasattr(task, "interrupts") and task.interrupts:
                    for intr in task.interrupts:
                        print("\n📋 Review Payload:")
                        print(json.dumps(intr.value, indent=2, ensure_ascii=False))
        return {
            "status": "paused_for_review",
            "thread_id": thread_id,
            "state": dict(snapshot.values),
        }

    final_state = dict(snapshot.values)
    final_status = final_state.get("workflow_status", "unknown")
    print("\n" + "=" * 60)
    if "success" in final_status:
        print(f"✅ Workflow completed: {final_status}")
    else:
        print(f"❌ Workflow ended: {final_status}")
    print("=" * 60)

    return {"status": final_status, "thread_id": thread_id, "state": final_state}


def _get_node_icon(node_name: str) -> str:
    """Return an emoji icon for each node type."""
    icons = {
        "collect_context": "🔍",
        "generate_draft": "✍️",
        "evaluate_quality": "📊",
        "reflect_governance": "🔎",
        "human_review": "👤",
        "publish_uc": "📤",
        "finalize_success": "✅",
        "finalize_failed": "❌",
    }
    return icons.get(node_name, "⚙️")


# ── ResponsesAgent Wrapper (for future Model Serving) ────────────────


class MetadataGovernanceAgent(mlflow.pyfunc.PythonModel):
    """
    MLflow-compatible agent wrapper.

    For future deployment as a Model Serving endpoint:

    ```python
    import mlflow
    from agent import MetadataGovernanceAgent

    mlflow.pyfunc.set_model(MetadataGovernanceAgent())
    ```
    """

    def predict(self, context, model_input: dict[str, Any]) -> Generator[str, None, None]:
        """
        Process a metadata governance request via Databricks Model Serving.
        Supports streaming responses.

        Parameters
        ----------
        context : mlflow.pyfunc.PythonModelContext
            The MLflow context.
        model_input : dict
            Must contain ``messages`` (list of OpenAI-like messages) and
            optionally ``custom_inputs`` (thread_id, decision, feedback).

        Returns
        -------
        Generator[str, None, None]
            Streaming response of markdown chunks.
        """
        # Parse inputs
        messages = model_input.get("messages", [])
        custom_inputs = model_input.get("custom_inputs", {})
        
        thread_id = custom_inputs.get("thread_id")
        decision = custom_inputs.get("decision")
        feedback = custom_inputs.get("feedback")

        # Resume flow
        if thread_id and decision:
            yield from self._resume_stream(thread_id, decision, feedback)
            return

        # Initial flow: Extract FQN from the last user message
        if not messages:
            yield "Error: No messages provided."
            return
            
        last_message = messages[-1]
        fqn = last_message.get("content", "").strip()
        
        if not fqn:
            yield "Error: No FQN provided in the last message."
            return
            
        yield from self._run_stream(fqn, thread_id)

    def _run_stream(self, fqn: str, thread_id: str | None = None) -> Generator[str, None, None]:
        """Stream the metadata governance workflow for a given table."""
        from langgraph.types import Command
        import uuid

        graph = _get_graph()
        tid = thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": tid}}

        initial_state = {
            "asset_fqn": fqn,
            "request_id": str(uuid.uuid4()),
            "workflow_status": "started",
            "loop_count": 0,
            "retry_count": 0,
            "audit_log": [],
            "quality_findings": [],
            "governance_findings": [],
        }

        yield "Iniciando proceso de documentación inteligente...\n\n"
        
        yield from self._process_events(graph.stream(initial_state, config, stream_mode="updates"), config, tid)

    def _resume_stream(self, thread_id: str, decision: str, feedback: str = "") -> Generator[str, None, None]:
        """Stream the resumption of the graph after HITL interrupt."""
        from langgraph.types import Command
        
        graph = _get_graph()
        config = {"configurable": {"thread_id": thread_id}}
        resume_value = {"decision": decision, "feedback": feedback}
        
        yield f"Reanudando flujo con decisión: {decision}...\n\n"
        
        yield from self._process_events(graph.stream(Command(resume=resume_value), config, stream_mode="updates"), config, thread_id)

    def _process_events(self, stream_iterator, config, tid: str) -> Generator[str, None, None]:
        """Process events from the graph stream and format them into markdown blocks."""
        graph = _get_graph()
        
        for event in stream_iterator:
            for node_name, node_output in event.items():
                if not isinstance(node_output, dict):
                    continue

                # Emit pipeline progress
                yield f"```json:metabuilder-pipeline\n{{\n  \"currentStep\": \"{node_name}\"\n}}\n```\n\n"

                # If generate_draft completed, emit draft card
                if node_name == "generate_draft" and "metadata_draft" in node_output:
                    draft = node_output["metadata_draft"]
                    # Format for DraftReviewCard
                    cols = [{"name": c.get("name", ""), "type": c.get("type", ""), "comment": c.get("comment", "")} for c in draft.get("columns", [])]
                    card_data = {
                        "tableName": draft.get("table", ""),
                        "tableComment": draft.get("description", ""),
                        "columns": cols
                    }
                    yield f"```json:metabuilder-draft\n{json.dumps(card_data)}\n```\n\n"

                # If evaluate_quality completed, emit quality card
                elif node_name == "evaluate_quality" and "quality_score" in node_output:
                    card_data = {
                        "score": node_output["quality_score"],
                        "pillars": {
                            "clarity": node_output.get("quality_score", 0.8), # Mock pillars if not detailed
                            "purpose": node_output.get("quality_score", 0.8),
                            "detail": node_output.get("quality_score", 0.8),
                            "context": node_output.get("quality_score", 0.8)
                        },
                        "findings": node_output.get("quality_findings", [])
                    }
                    yield f"```json:metabuilder-quality\n{json.dumps(card_data)}\n```\n\n"

                # If reflect_governance completed, emit governance card
                elif node_name == "reflect_governance" and "governance_status" in node_output:
                    card_data = {
                        "status": node_output["governance_status"],
                        "findings": node_output.get("governance_findings", [])
                    }
                    yield f"```json:metabuilder-governance\n{json.dumps(card_data)}\n```\n\n"

        # Check if paused (HITL)
        try:
            snapshot = graph.get_state(config)
            is_paused = snapshot.next
        except Exception:
            is_paused = False

        if is_paused:
            yield f"```json:metabuilder-pipeline\n{{\n  \"currentStep\": \"human_review\"\n}}\n```\n\n"
            yield f"```json:metabuilder-hitl\n{{}}\n```\n\n"
        else:
            yield f"```json:metabuilder-pipeline\n{{\n  \"currentStep\": \"completed\"\n}}\n```\n\n"

