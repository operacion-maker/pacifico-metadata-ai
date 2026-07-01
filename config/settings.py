"""
Global settings for the Metadata Governance Agent.

Defines thresholds, model configuration, and operational parameters
for the state machine.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """Immutable configuration for the governance agent pipeline."""

    # ── LLM Model ──────────────────────────────────────────────────────
    # Primary model (cost-efficient for MVP)
    LLM_MODEL: str = "databricks-meta-llama-3-1-8b-instruct"
    # Future upgrade path
    LLM_MODEL_UPGRADE: str = "databricks-gemma-3-12b"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 8192

    # ── Quality Thresholds ─────────────────────────────────────────────
    # score < AUTO_REFLEXION_CEILING → automatic reflexion loop (no human)
    AUTO_REFLEXION_CEILING: float = 0.4
    # score >= HITL_TRIGGER → escalate to Data Steward
    HITL_TRIGGER: float = 0.7
    # score >= PUBLISH_READY → ready for UC publication post-HITL governance
    PUBLISH_READY: float = 0.9

    # ── Loop Control ───────────────────────────────────────────────────
    MAX_REFLEXION_LOOPS: int = 3
    MAX_PUBLISH_RETRIES: int = 2

    # ── Profiling ──────────────────────────────────────────────────────
    PROFILING_SAMPLE_ROWS: int = 1000
    PROFILING_NULL_THRESHOLD: float = 0.5  # flag columns with >50% nulls

    # ── Unity Catalog Sources ──────────────────────────────────────────
    # Table with UC object + column metadata
    UC_OBJETOS_COLUMNAS: str = (
        "ctl_lakehouse_modelamiento_desa"
        ".sch_ctl_modelamiento_silver_tb"
        ".md_objetos_uc_columnas"
    )
    # Table with column tags (DAC, EDC, etc.)
    UC_COLUMNAS_TAGS: str = (
        "ctl_lakehouse_modelamiento_desa"
        ".sch_ctl_modelamiento_silver_tb"
        ".ud_columnas_tags"
    )
    # Lineage function
    UC_LINEAGE_FUNCTION: str = (
        "ctl_lakehouse_modelamiento_desa"
        ".sch_ctl_modelamiento_gold_fn"
        ".fn_get_specific_lineage_in_lakehouse"
    )


# Singleton settings instance
SETTINGS = Settings()
