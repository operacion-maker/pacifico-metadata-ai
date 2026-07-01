"""
evaluate_quality — Cognitive node (LLM-as-Judge) that scores the draft
against the 4 governance pillars.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import mlflow

from config.settings import SETTINGS
from prompts.quality_evaluation import build_quality_prompt
from state.schema import MetadataAgentState

logger = logging.getLogger(__name__)


def _call_llm(system: str, user: str) -> str:
    """Call the Databricks Foundation Model endpoint."""
    from langchain_databricks import ChatDatabricks

    llm = ChatDatabricks(
        endpoint=SETTINGS.LLM_MODEL,
        temperature=0.0,  # Deterministic for evaluation
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
    json_match = re.search(r'\{[\s\S]*"pillar_scores"[\s\S]*\}', clean)
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


@mlflow.trace(name="node.evaluate_quality")
def evaluate_quality(state: MetadataAgentState) -> dict[str, Any]:
    """
    Evaluate the metadata draft against governance quality pillars.

    Returns pillar scores, overall quality score, and actionable findings.
    """
    system_prompt, user_prompt = build_quality_prompt(
        draft_table_comment=state["draft_table_comment"],
        draft_column_comments=state.get("draft_column_comments", {}),
        table_info=state["table_info"],
        column_tags=state.get("column_tags"),
        profiling_summary=state.get("profiling_summary"),
    )

    raw_response = _call_llm(system_prompt, user_prompt)

    try:
        parsed = _parse_json_response(raw_response)
        pillar_scores = parsed.get("pillar_scores", {})
        quality_score = parsed.get("quality_score", 0.0)
        findings = parsed.get("findings", [])

        # Validate and clamp scores
        for key in ["clarity", "purpose", "detail", "context"]:
            if key not in pillar_scores:
                pillar_scores[key] = 0.0
            pillar_scores[key] = max(0.0, min(1.0, float(pillar_scores[key])))

        # Recalculate quality_score as safety check
        quality_score = sum(pillar_scores.values()) / max(len(pillar_scores), 1)
        quality_score = round(quality_score, 3)

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error("Failed to parse quality evaluation: %s", e)
        pillar_scores = {"clarity": 0.0, "purpose": 0.0, "detail": 0.0, "context": 0.0}
        quality_score = 0.0
        findings = [f"Error parsing quality evaluation: {e}"]

    return {
        "quality_score": quality_score,
        "pillar_scores": pillar_scores,
        "quality_findings": findings,
        "workflow_status": "quality_evaluated",
        "audit_log": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "node": "evaluate_quality",
                "action": "quality_scored",
                "details": {
                    "quality_score": quality_score,
                    "pillar_scores": pillar_scores,
                    "findings_count": len(findings),
                    "loop_iteration": state.get("loop_count", 0),
                },
            }
        ],
    }
