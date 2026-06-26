"""XAI Review Agent (Phase 1 — lightweight).

This agent deliberately does NOT run a full-dataset Grad-CAM sweep. Grad-CAM and
the deletion-curve faithfulness metric are expensive (many forward passes per
image), so Phase 1 only inventories what XAI assets exist and recommends a
sampled/cached strategy for a later phase.

It is explicit that Grad-CAM is post-hoc and correlational, never causal proof.
"""

from __future__ import annotations

from typing import List

from .data_loader import AgentDataset
from .schemas import AgentFinding, AgentLimitation, XAIReviewReport

AGENT_NAME = "XAI Review Agent"

# Existing XAI surfaces in the backend (src/api/main.py). Listed by route so the
# frontend/coordinator can point at them without this agent calling them.
_XAI_ASSETS = [
    "GET /api/xai/faithfulness  — Grad-CAM deletion curve + AUC (cached per file)",
    "GET /api/explain-panels/{filename}  — 3-panel B+ | B- | Grad-CAM figure",
    "GET /api/explain-layers/{filename}  — stage2/3/4 Grad-CAM heatmaps + activation %",
]


def run_xai_review_agent(dataset: AgentDataset) -> XAIReviewReport:
    n_val = len(dataset.validation_rows)
    # A defensible sampled budget: ~5% of the hold-out set, capped, deterministic.
    suggested_sample = max(10, min(20, round(n_val * 0.05)))

    findings: List[AgentFinding] = []

    findings.append(
        AgentFinding(
            key="xai_assets_available",
            label="XAI assets already exist",
            detail=(
                "The backend exposes Grad-CAM faithfulness, multi-panel overlays, "
                "and per-stage heatmaps. The Agent Lab can consume these rather "
                "than reimplementing saliency."
            ),
            severity="info",
            evidence={"asset_count": float(len(_XAI_ASSETS))},
        )
    )

    findings.append(
        AgentFinding(
            key="sweep_deferred",
            label="Full XAI sweep deferred",
            detail=(
                "A full-dataset Grad-CAM sweep is intentionally not run in Phase 1: "
                "the deletion-curve metric needs ~22 forward passes per image. "
                f"Recommended next step: a deterministic sample of ~{suggested_sample} "
                "hold-out magnetograms (favouring high-SI tail samples), cached, to "
                "estimate a mean faithfulness AUC and flag weak-alignment cases."
            ),
            severity="notice",
            evidence={"suggested_sample": float(suggested_sample)},
        )
    )

    findings.append(
        AgentFinding(
            key="post_hoc_caution",
            label="Grad-CAM is post-hoc, not causal",
            detail=(
                "Saliency aligning with strong-field / active-region zones is "
                "consistent with sensible behaviour but is NOT proof of causal "
                "physical reasoning. Treat alignment as supporting evidence only."
            ),
            severity="warning",
        )
    )

    recommendation = (
        f"Phase 2: sample ~{suggested_sample} hold-out magnetograms (bias toward "
        "SI>2.0 tail events), call /api/xai/faithfulness per sample, cache the "
        "AUCs, and flag any sample where guided occlusion degrades the prediction "
        "no faster than random occlusion (weak alignment). Do not sweep the full "
        "corpus."
    )

    limitations = [
        AgentLimitation(
            key="no_sampled_xai_yet",
            detail=(
                "Phase 1 computes no saliency values; this report is an inventory "
                "and strategy, not a faithfulness measurement."
            ),
        ),
        AgentLimitation(
            key="post_hoc",
            detail="Grad-CAM is post-hoc and correlational; it is not causal proof.",
        ),
        AgentLimitation(
            key="cost",
            detail=(
                "The faithfulness endpoint is expensive per image; any future sweep "
                "must be sampled and cached to keep endpoints responsive."
            ),
        ),
    ]

    summary = (
        "XAI assets exist (Grad-CAM faithfulness, panels, per-stage heatmaps). "
        f"Full sweep deferred; recommend a cached sample of ~{suggested_sample} "
        "tail-weighted magnetograms in Phase 2. Grad-CAM remains post-hoc, not "
        "causal proof."
    )

    # Confidence is modest: this is a strategy/inventory, not a measurement.
    confidence = 0.5

    return XAIReviewReport(
        agent_name=AGENT_NAME,
        summary=summary,
        confidence=confidence,
        findings=findings,
        limitations=limitations,
        faithfulness_endpoint_available=True,
        available_assets=_XAI_ASSETS,
        sampled_strategy_recommendation=recommendation,
        sweep_status="deferred",
    )
