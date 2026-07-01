"""
evaluate_quality — Cognitive node (LLM-as-Judge) that scores the draft
against the 4 governance pillars.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

import mlflow

from config.settings import SETTINGS
from prompts.quality_evaluation import build_quality_prompt
from state.schema import MetadataAgentState

logger = logging.getLogger(__name__)


def _call_llm(system: str, user: str) -> str:
    """Call the Databricks Foundation Model endpoint."""
    # Actualizado para silenciar el LangChainDeprecationWarning
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
    clean = text.strip()

    # 1. Búsqueda robusta con Regex (Solución principal al error de parseo)
    # Extrae exclusivamente lo que esté entre llaves, ignorando texto coloquial o markdowns
    json_match = re.search(r'\{.*\}', clean, re.DOTALL)
    
    if json_match:
        candidate = json_match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass  # Si el JSON interno está mal formado, pasamos a las siguientes estrategias

    # 2. Limpieza clásica de bloques Markdown
    if clean.startswith("```"):
        clean = re.sub(r'\n```$', '', clean)
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # 3. Reparación de JSON truncado (Última línea de defensa original)
    json_match_fallback = re.search(r'\{[\s\S]*"pillar_scores"[\s\S]*\}', clean)
    if json_match_fallback:
        repaired = json_match_fallback.group(0)
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
        # 💡 Este debug te salvará la vida si el modelo alguna vez alucina muy feo
        logger.debug("Raw LLM response was: %s", raw_response) 
        
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