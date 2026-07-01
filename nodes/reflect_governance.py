"""
reflect_governance — Cognitive node that validates the draft against the
7 mandatory governance principles.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import mlflow

from config.settings import SETTINGS
from prompts.governance_reflection import build_governance_prompt
from state.schema import MetadataAgentState

logger = logging.getLogger(__name__)


def _call_llm(system: str, user: str) -> str:
    """Call the Databricks Foundation Model endpoint."""
    from langchain_databricks import ChatDatabricks

    llm = ChatDatabricks(
        endpoint=SETTINGS.LLM_MODEL,
        temperature=0.0,
        max_tokens=SETTINGS.LLM_MAX_TOKENS,
    )
    response = llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ])
    return response.content


def _parse_json_response(text: str) -> dict[str, Any]:
    """Extract JSON from LLM response with robust fallback strategies."""
    import re

    clean = text.strip()

    # Remove markdown code fences
    if clean.startswith("```"):
        lines = clean.split("\n")
        start = 1
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip() == "```":
                end = i
                break
        clean = "\n".join(lines[start:end]).strip()

    # Try direct parse
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Find JSON object within mixed text
    json_match = re.search(r'\{[\s\S]*"governance_status"[\s\S]*\}', clean)
    if json_match:
        candidate = json_match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Try to repair truncated JSON
            repaired = candidate
            open_braces = repaired.count("{") - repaired.count("}")
            if open_braces > 0:
                last_quote = repaired.rfind('"')
                if last_quote > 0:
                    repaired = repaired[:last_quote + 1]
                    repaired += "}" * open_braces
                    try:
                        return json.loads(repaired)
                    except json.JSONDecodeError:
                        pass

    raise json.JSONDecodeError("Could not extract JSON", text, 0)


@mlflow.trace(name="node.reflect_governance")
def reflect_governance(state: MetadataAgentState) -> dict[str, Any]:
    """
    Validate the draft against governance principles.

    This node acts as the *Reflexion* agent — it critically examines
    the draft's compliance with organizational governance rules.
    """
    system_prompt, user_prompt = build_governance_prompt(
        draft_table_comment=state["draft_table_comment"],
        draft_column_comments=state.get("draft_column_comments", {}),
        quality_score=state.get("quality_score", 0.0),
        pillar_scores=state.get("pillar_scores", {}),
        table_info=state["table_info"],
        column_tags=state.get("column_tags"),
        profiling_summary=state.get("profiling_summary"),
    )

    raw_response = _call_llm(system_prompt, user_prompt)

    try:
        parsed = _parse_json_response(raw_response)
        governance_status = parsed.get("governance_status", "needs_review")
        findings = parsed.get("findings", [])
        recommendation = parsed.get("recommendation", "")

        # Validate status
        if governance_status not in ("pass", "fail", "needs_review"):
            governance_status = "needs_review"

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error("Failed to parse governance reflection: %s", e)
        governance_status = "needs_review"
        findings = [f"Error parsing governance reflection: {e}"]
        recommendation = "Cannot evaluate governance — review required."

    return {
        "governance_status": governance_status,
        "governance_findings": findings,
        "workflow_status": "governance_evaluated",
        "audit_log": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "node": "reflect_governance",
                "action": "governance_evaluated",
                "details": {
                    "governance_status": governance_status,
                    "findings_count": len(findings),
                    "quality_score": state.get("quality_score", 0.0),
                    "recommendation": recommendation,
                },
            }
        ],
    }
