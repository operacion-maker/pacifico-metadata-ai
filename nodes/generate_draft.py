"""
generate_draft — Cognitive node that produces metadata drafts via LLM.

Uses the evidence collected by ``collect_context`` and the governance pillar
prompts to generate functional descriptions for the table and its columns.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import mlflow

from config.settings import SETTINGS
from prompts.draft_generation import build_draft_prompt
from state.schema import MetadataAgentState

logger = logging.getLogger(__name__)


def _call_llm(system: str, user: str) -> str:
    """Call the Databricks Foundation Model endpoint."""
    from langchain_databricks import ChatDatabricks

    llm = ChatDatabricks(
        endpoint=SETTINGS.LLM_MODEL,
        temperature=SETTINGS.LLM_TEMPERATURE,
        max_tokens=SETTINGS.LLM_MAX_TOKENS,
    )
    response = llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
    return response.content


def _parse_json_response(text: str) -> dict[str, Any]:
    """
    Extract JSON from LLM response.

    Handles multiple common failure modes from smaller LLMs:
    1. Response wrapped in markdown code fences
    2. JSON embedded within prose/markdown text
    3. Truncated JSON (token limit hit)
    4. Non-JSON response (returns raw text as fallback)
    """
    import re

    clean = text.strip()

    # Strategy 1: Remove markdown code fences
    if clean.startswith("```"):
        lines = clean.split("\n")
        start = 1  # skip ```json or ```
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip() == "```":
                end = i
                break
        clean = "\n".join(lines[start:end]).strip()

    # Strategy 2: Try direct parse
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Find JSON object within mixed text using regex
    json_match = re.search(r'\{[\s\S]*"table_comment"[\s\S]*\}', clean)
    if json_match:
        candidate = json_match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Strategy 4: Try to repair truncated JSON (close open brackets)
            repaired = candidate
            open_braces = repaired.count("{") - repaired.count("}")
            if open_braces > 0:
                # Find last complete value (ends with " or number)
                last_quote = repaired.rfind('"')
                if last_quote > 0:
                    repaired = repaired[:last_quote + 1]
                    repaired += "}" * open_braces
                    try:
                        return json.loads(repaired)
                    except json.JSONDecodeError:
                        pass

    # Strategy 5: Fallback — return structure with raw text
    logger.warning("Could not parse JSON from LLM response (%d chars). Using raw text as table_comment.", len(text))
    return {"table_comment": text, "column_comments": {}, "governance_indicator": {"status": "warn", "compliance_notes": ["Error parsing response"]}}


@mlflow.trace(name="node.generate_draft")
def generate_draft(state: MetadataAgentState) -> dict[str, Any]:
    """
    Generate metadata draft using LLM.

    This is a **cognitive** node — calls the LLM with evidence context.
    On rework iterations, includes human feedback to guide improvements
    (Prompt Anchoring).
    """
    system_prompt, user_prompt = build_draft_prompt(
        table_info=state["table_info"],
        column_details=state.get("column_details", []),
        profiling_summary=state.get("profiling_summary"),
        lineage_info=state.get("lineage_info"),
        column_tags=state.get("column_tags"),
        human_feedback=state.get("human_feedback"),
    )

    raw_response = _call_llm(system_prompt, user_prompt)

    try:
        parsed = _parse_json_response(raw_response)
        draft_table_comment = parsed.get("table_comment", "")
        draft_column_comments = parsed.get("column_comments", {})
        governance_indicator = parsed.get("governance_indicator", {"status": "warn", "compliance_notes": []})
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to parse draft response: %s", e)
        draft_table_comment = raw_response
        draft_column_comments = {}
        governance_indicator = {"status": "warn", "compliance_notes": [f"Parse error: {str(e)}"]}

    loop_count = state.get("loop_count", 0)

    return {
        "draft_table_comment": draft_table_comment,
        "draft_column_comments": draft_column_comments,
        "governance_indicator": governance_indicator,
        "workflow_status": "draft_generated",
        "loop_count": loop_count + 1,
        # Clear previous human feedback after consuming it
        "human_feedback": None,
        "human_decision": None,
        "audit_log": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "node": "generate_draft",
                "action": "draft_created",
                "details": {
                    "iteration": loop_count + 1,
                    "table_comment_length": len(draft_table_comment),
                    "columns_commented": len(draft_column_comments),
                    "model": SETTINGS.LLM_MODEL,
                    "had_human_feedback": bool(state.get("human_feedback")),
                },
            }
        ],
    }
