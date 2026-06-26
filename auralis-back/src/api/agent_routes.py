"""Additive Agent Lab routes (read-only).

These endpoints expose the Auralis Agent Lab audit layer. They are mounted on a
separate ``APIRouter`` and included from ``main.py`` with a single
``include_router`` call, so no existing route handler is touched.

Every handler shares the dataset loader, catches :class:`AgentDataError`, and
returns a structured 503 when a required artifact is missing — the existing API
keeps working regardless of the Agent Lab's state.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from agents.active_learning_agent import run_active_learning_agent
from agents.data_loader import AgentDataError, load_agent_dataset
from agents.data_quality_agent import run_data_quality_agent
from agents.error_analysis_agent import run_error_analysis_agent
from agents.report_agent import build_full_report
from agents.schemas import (
    ActiveLearningReport,
    DataQualityReport,
    ErrorAnalysisReport,
    FullAgentReport,
    XAIReviewReport,
)
from agents.xai_review_agent import run_xai_review_agent

logger = logging.getLogger("auralis.api.agents")

router = APIRouter(prefix="/api/agents", tags=["Agent Lab"])


def _load_or_503():
    """Load the shared dataset or raise a structured 503 on missing artifacts."""
    try:
        return load_agent_dataset()
    except AgentDataError as exc:
        logger.warning("Agent Lab data unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=exc.to_dict()) from exc


@router.get("/data-quality", response_model=DataQualityReport)
async def agent_data_quality():
    """Dataset-composition audit: bin balance, low-activity coverage, outliers."""
    return run_data_quality_agent(_load_or_503())


@router.get("/error-analysis", response_model=ErrorAnalysisReport)
async def agent_error_analysis():
    """Hold-out error audit: MAE/RMSE by bin, residuals, top-error tail samples."""
    return run_error_analysis_agent(_load_or_503())


@router.get("/xai-review", response_model=XAIReviewReport)
async def agent_xai_review():
    """Lightweight XAI inventory + sampled-sweep strategy (full sweep deferred)."""
    return run_xai_review_agent(_load_or_503())


@router.get("/active-learning", response_model=ActiveLearningReport)
async def agent_active_learning():
    """Deterministic epsilon-greedy bandit recommendation (decision-support only)."""
    dataset = _load_or_503()
    err = run_error_analysis_agent(dataset)
    dq = run_data_quality_agent(dataset)
    return run_active_learning_agent(dataset, err, dq)


@router.get("/full-report", response_model=FullAgentReport)
async def agent_full_report():
    """Coordinator audit brief combining all four agents."""
    return build_full_report(_load_or_503())
