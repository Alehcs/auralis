"""Pydantic models for the Auralis Agent Lab.

These schemas describe the read-only audit output of the scientific agents.
Every agent report shares a common envelope (``agent_name``, ``summary``,
``confidence``, ``findings``, ``limitations``, ``generated_at``) so the frontend
can render any agent with one component and so the coordinator can compose them
uniformly.

Nothing here touches the model, the ONNX artifact, or any training state. The
agents only summarise artifacts that already exist on disk.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


def _utc_now() -> str:
    """ISO-8601 UTC timestamp used as the default ``generated_at`` value."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------

class AgentFinding(BaseModel):
    """A single observation produced by an agent.

    ``severity`` is advisory only: ``info`` (neutral fact), ``notice`` (worth
    attention), or ``warning`` (a weakness the researcher should act on).
    """

    key: str
    label: str
    detail: str
    severity: str = "info"            # "info" | "notice" | "warning"
    evidence: Dict[str, float] = Field(default_factory=dict)


class AgentLimitation(BaseModel):
    """An explicit caveat that bounds how far a finding can be trusted."""

    key: str
    detail: str


class AgentReportBase(BaseModel):
    """Common envelope shared by every agent report."""

    agent_name: str
    summary: str
    confidence: float                 # heuristic self-confidence in [0, 1]
    findings: List[AgentFinding] = Field(default_factory=list)
    limitations: List[AgentLimitation] = Field(default_factory=list)
    generated_at: str = Field(default_factory=_utc_now)


# ---------------------------------------------------------------------------
# Per-sample helpers
# ---------------------------------------------------------------------------

class ErrorSample(BaseModel):
    """One hold-out sample, used for the top-error tables."""

    filename: str
    date: Optional[str] = None
    real: float
    predicted: float
    error: float
    residual: float
    activity_bin: str


class BinStat(BaseModel):
    """Count + share for one activity bin."""

    count: int
    share: float                      # fraction of the parent population in [0, 1]


# ---------------------------------------------------------------------------
# Data Quality Agent
# ---------------------------------------------------------------------------

class DataQualityReport(AgentReportBase):
    full_distribution: Dict[str, BinStat]
    train_distribution: Dict[str, BinStat]
    val_distribution: Dict[str, BinStat]
    low_activity_underrepresented: bool
    minority_bin: str
    date_coverage: Dict[str, str] = Field(default_factory=dict)
    outlier_indicators: Dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Error Analysis Agent
# ---------------------------------------------------------------------------

class ErrorAnalysisReport(AgentReportBase):
    mae_by_bin: Dict[str, float]
    rmse_by_bin: Dict[str, float]
    residual_mean_by_bin: Dict[str, float]
    top_errors: List[ErrorSample]
    tail_extreme_count: int
    tail_extreme_mae: Optional[float] = None
    error_is_flat: bool
    mae_spread: float                 # max(MAE_bin) - min(MAE_bin)


# ---------------------------------------------------------------------------
# XAI Review Agent
# ---------------------------------------------------------------------------

class XAIReviewReport(AgentReportBase):
    faithfulness_endpoint_available: bool
    available_assets: List[str] = Field(default_factory=list)
    sampled_strategy_recommendation: str
    sweep_status: str                 # e.g. "deferred"


# ---------------------------------------------------------------------------
# Active Learning Agent (contextual bandit)
# ---------------------------------------------------------------------------

class BanditActionUtility(BaseModel):
    action_id: str
    action_name: str
    description: str
    utility: float                    # decision-support utility, NOT measured gain


class BanditRound(BaseModel):
    round_index: int
    selected_action: str
    is_exploration: bool
    reward: float                     # heuristic reward of the selected action
    regret: float                     # best_utility - utility(selected), heuristic


class ActiveLearningReport(AgentReportBase):
    state_vector: Dict[str, float]
    action_utilities: List[BanditActionUtility]
    rounds: List[BanditRound]
    action_distribution: Dict[str, int]
    best_recommendation: BanditActionUtility
    cumulative_regret: List[float]
    epsilon: float
    seed: int
    n_rounds: int


# ---------------------------------------------------------------------------
# Coordinator / Full Report
# ---------------------------------------------------------------------------

class FullAgentReport(AgentReportBase):
    dataset_health_summary: str
    model_weakness_summary: str
    xai_caution_summary: str
    active_learning_recommendation: str
    recommended_next_steps: List[str]
    data_quality: DataQualityReport
    error_analysis: ErrorAnalysisReport
    xai_review: XAIReviewReport
    active_learning: ActiveLearningReport
