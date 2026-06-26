"""Coordinator / Full Report Agent.

Runs the four read-only audit agents and composes their output into one
scientific audit brief: dataset health, model weaknesses, XAI caution, the
active-learning recommendation, an overall confidence, consolidated limitations,
and concrete next steps.

This agent performs no new computation of its own beyond aggregation.
"""

from __future__ import annotations

from typing import List

from .active_learning_agent import run_active_learning_agent
from .data_loader import AgentDataset, load_agent_dataset
from .data_quality_agent import run_data_quality_agent
from .error_analysis_agent import run_error_analysis_agent
from .schemas import AgentFinding, AgentLimitation, FullAgentReport
from .xai_review_agent import run_xai_review_agent

AGENT_NAME = "Research Coordinator Agent"


def build_full_report(dataset: AgentDataset | None = None) -> FullAgentReport:
    """Run all agents over the shared dataset and compose the audit brief."""
    if dataset is None:
        dataset = load_agent_dataset()

    dq = run_data_quality_agent(dataset)
    err = run_error_analysis_agent(dataset)
    xai = run_xai_review_agent(dataset)
    al = run_active_learning_agent(dataset, err, dq)

    # -- composed narrative summaries ---------------------------------------
    dataset_health = (
        f"{sum(b.count for b in dq.full_distribution.values())} samples; minority "
        f"bin '{dq.minority_bin}'"
        + (" (low activity underrepresented). " if dq.low_activity_underrepresented
           else ". ")
        + ("All bins present in train and validation." )
    )

    model_weakness = (
        ("Bin-level error is nearly flat" if err.error_is_flat
         else "Bin-level error is uneven")
        + f" (MAE spread={err.mae_spread}). "
        + (
            f"Primary weakness is the high-SI tail (SI>2.0, N={err.tail_extreme_count}, "
            f"MAE={err.tail_extreme_mae})."
            if err.tail_extreme_count
            else "No extreme-tail samples in this split."
        )
    )

    xai_caution = (
        "Grad-CAM assets exist but full sweep is deferred. Saliency is post-hoc and "
        "correlational — not causal proof of physical reasoning."
    )

    al_recommendation = (
        f"Prioritise {al.best_recommendation.action_id} "
        f"({al.best_recommendation.action_name}). Decision-support utility from the "
        "audit, not a guarantee of model improvement."
    )

    next_steps: List[str] = [
        f"{al.best_recommendation.action_id}: {al.best_recommendation.description}",
        "Review the top-10 high-error tail samples listed by the Error Analysis Agent.",
        (f"Phase 2 XAI: cache a sampled faithfulness sweep "
         f"({xai.sweep_status} now) over tail-weighted magnetograms."),
    ]
    if dq.low_activity_underrepresented:
        next_steps.append(
            "Collect more low-activity / solar-minimum samples to balance the corpus."
        )

    # -- consolidated findings (one headline per agent) ---------------------
    findings: List[AgentFinding] = [
        AgentFinding(
            key="dataset_health",
            label="Dataset health",
            detail=dataset_health,
            severity="notice" if dq.low_activity_underrepresented else "info",
        ),
        AgentFinding(
            key="model_weakness",
            label="Model weakness",
            detail=model_weakness,
            severity="warning" if err.tail_extreme_count else "info",
        ),
        AgentFinding(
            key="xai_caution",
            label="XAI caution",
            detail=xai_caution,
            severity="notice",
        ),
        AgentFinding(
            key="active_learning",
            label="Active-learning recommendation",
            detail=al_recommendation,
            severity="notice",
        ),
    ]

    # -- consolidated limitations (deduplicated across agents) --------------
    limitations: List[AgentLimitation] = []
    seen = set()
    for sub in (dq, err, xai, al):
        for lim in sub.limitations:
            if lim.key not in seen:
                seen.add(lim.key)
                limitations.append(lim)
    limitations.append(
        AgentLimitation(
            key="audit_not_improvement",
            detail=(
                "This is a read-only audit. No retraining occurs; nothing here "
                "measures or proves an improvement to Coronium V3 PRO."
            ),
        )
    )

    # Overall confidence = mean of sub-agent confidences (audit is only as strong
    # as its weakest, deferred component).
    confidence = round((dq.confidence + err.confidence + xai.confidence + al.confidence) / 4, 3)

    summary = (
        f"{dataset_health} {model_weakness} Recommended next data: "
        f"{al.best_recommendation.action_name}. Audit only — not a model improvement claim."
    )

    if dataset.warnings:
        findings.append(
            AgentFinding(
                key="loader_warnings",
                label="Data loader warnings",
                detail="; ".join(dataset.warnings),
                severity="notice",
            )
        )

    return FullAgentReport(
        agent_name=AGENT_NAME,
        summary=summary,
        confidence=confidence,
        findings=findings,
        limitations=limitations,
        dataset_health_summary=dataset_health,
        model_weakness_summary=model_weakness,
        xai_caution_summary=xai_caution,
        active_learning_recommendation=al_recommendation,
        recommended_next_steps=next_steps,
        data_quality=dq,
        error_analysis=err,
        xai_review=xai,
        active_learning=al,
    )
