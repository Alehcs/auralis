"""Active Learning Agent.

Builds a normalised "audit need" state vector from the Data Quality and Error
Analysis reports, then runs a deterministic epsilon-greedy contextual bandit to
recommend which kind of future data to prioritise.

The output is decision-support utility from the current audit signals. It is NOT
a measurement of model improvement, and the regret curve is heuristic regret
against the best utility, not against any real-world gain.
"""

from __future__ import annotations

from typing import Dict, List

from .data_loader import ACTIVITY_BINS, AgentDataset
from .policy.bandit import (
    ACTIONS,
    DEFAULT_EPSILON,
    DEFAULT_ROUNDS,
    DEFAULT_SEED,
    run_bandit,
)
from .schemas import (
    ActiveLearningReport,
    AgentFinding,
    AgentLimitation,
    BanditActionUtility,
    BanditRound,
    DataQualityReport,
    ErrorAnalysisReport,
)

AGENT_NAME = "Active Learning Agent"

# Phase-1 placeholder for XAI risk: no sampled faithfulness yet, so a neutral
# 0.5 is used and clearly labelled as a proxy.
XAI_RISK_PLACEHOLDER = 0.5


def _normalise(values: Dict[str, float]) -> Dict[str, float]:
    hi = max(values.values()) if values else 0.0
    if hi <= 0:
        return {k: 0.0 for k in values}
    return {k: round(v / hi, 4) for k, v in values.items()}


def build_state_vector(
    dataset: AgentDataset,
    error_report: ErrorAnalysisReport,
    dq_report: DataQualityReport,
) -> Dict[str, float]:
    """Assemble the normalised audit-need state vector in [0, 1]."""
    # --- error needs: MAE per bin + tail, normalised by the largest of them ----
    raw_error = {
        "low": error_report.mae_by_bin.get("low", 0.0),
        "medium": error_report.mae_by_bin.get("medium", 0.0),
        "high": error_report.mae_by_bin.get("high", 0.0),
        "tail": error_report.tail_extreme_mae or 0.0,
    }
    norm_error = _normalise(raw_error)

    # --- underrepresentation needs: 1 - count/max_count over the full corpus ---
    full_counts = {b: dq_report.full_distribution[b].count for b in ACTIVITY_BINS}
    max_count = max(full_counts.values()) or 1
    underrep = {
        b: round(1.0 - full_counts[b] / max_count, 4) for b in ACTIVITY_BINS
    }

    # --- uncertainty proxy: residual dispersion (RMSE>MAE gap), overall ---------
    rows = dataset.validation_rows
    overall_mae = sum(r.error for r in rows) / len(rows) if rows else 0.0
    overall_rmse = (
        (sum(r.error ** 2 for r in rows) / len(rows)) ** 0.5 if rows else 0.0
    )
    uncertainty_proxy = 0.0
    if overall_rmse > 0:
        uncertainty_proxy = round(
            max(0.0, min(1.0, (overall_rmse - overall_mae) / overall_rmse)), 4
        )

    return {
        "low_error_need": norm_error["low"],
        "medium_error_need": norm_error["medium"],
        "high_error_need": norm_error["high"],
        "tail_extreme_error_need": norm_error["tail"],
        "low_underrepresentation_need": underrep["low"],
        "medium_underrepresentation_need": underrep["medium"],
        "high_underrepresentation_need": underrep["high"],
        "uncertainty_need_proxy": uncertainty_proxy,
        "xai_risk_proxy": XAI_RISK_PLACEHOLDER,
    }


def run_active_learning_agent(
    dataset: AgentDataset,
    error_report: ErrorAnalysisReport,
    dq_report: DataQualityReport,
    *,
    epsilon: float = DEFAULT_EPSILON,
    seed: int = DEFAULT_SEED,
    n_rounds: int = DEFAULT_ROUNDS,
) -> ActiveLearningReport:
    state = build_state_vector(dataset, error_report, dq_report)
    result = run_bandit(state, epsilon=epsilon, seed=seed, n_rounds=n_rounds)

    spec_by_id = {spec.action_id: spec for spec in ACTIONS}

    action_utilities: List[BanditActionUtility] = [
        BanditActionUtility(
            action_id=spec.action_id,
            action_name=spec.name,
            description=spec.description,
            utility=result.utilities[spec.action_id],
        )
        for spec in ACTIONS
    ]
    action_utilities.sort(key=lambda a: a.utility, reverse=True)

    best_spec = spec_by_id[result.best_action_id]
    best = BanditActionUtility(
        action_id=best_spec.action_id,
        action_name=best_spec.name,
        description=best_spec.description,
        utility=result.utilities[best_spec.action_id],
    )

    rounds = [
        BanditRound(
            round_index=int(r["round_index"]),
            selected_action=str(r["selected_action"]),
            is_exploration=bool(r["is_exploration"]),
            reward=float(r["reward"]),
            regret=float(r["regret"]),
        )
        for r in result.rounds
    ]

    findings: List[AgentFinding] = []

    findings.append(
        AgentFinding(
            key="recommendation",
            label="Top recommended action",
            detail=(
                f"{best.action_id} — {best.action_name} "
                f"(utility={best.utility}). {best.description}"
            ),
            severity="notice",
            evidence={"best_utility": best.utility},
        )
    )

    n_explore = sum(1 for r in rounds if r.is_exploration)
    findings.append(
        AgentFinding(
            key="exploration",
            label="Exploration behaviour",
            detail=(
                f"{n_explore}/{n_rounds} rounds explored (epsilon={epsilon}); the "
                "remaining rounds exploited the best-utility action. Final "
                f"cumulative heuristic regret = {result.cumulative_regret[-1] if result.cumulative_regret else 0.0}."
            ),
            severity="info",
            evidence={"explore_rounds": float(n_explore)},
        )
    )

    # Surface the two emphasis rules explicitly.
    findings.append(
        AgentFinding(
            key="emphasis_rules",
            label="Policy emphasis",
            detail=(
                "A5 emphasises high-error tail extremes (SI>2.0); A1/A4 emphasise "
                "low-activity and solar-minimum underrepresentation. These reflect "
                "the audit's measured weak spots."
            ),
            severity="info",
        )
    )

    limitations = [
        AgentLimitation(
            key="not_real_improvement",
            detail=(
                "Reward is decision-support utility from current audit signals. It "
                "does NOT mean the model improves — nothing is retrained here."
            ),
        ),
        AgentLimitation(
            key="heuristic_regret",
            detail=(
                "Regret is measured against the best heuristic utility, not against "
                "any real-world model gain."
            ),
        ),
        AgentLimitation(
            key="xai_proxy",
            detail=(
                f"xai_risk_proxy is a neutral placeholder ({XAI_RISK_PLACEHOLDER}); "
                "no sampled faithfulness has been computed in Phase 1."
            ),
        ),
        AgentLimitation(
            key="uncertainty_proxy",
            detail=(
                "uncertainty_need_proxy uses residual dispersion (RMSE-MAE gap), not "
                "true per-sample MC-Dropout uncertainty."
            ),
        ),
    ]

    summary = (
        f"Bandit recommends {best.action_id} ({best.action_name}, utility="
        f"{best.utility}) over {n_rounds} epsilon-greedy rounds (epsilon={epsilon}, "
        f"seed={seed}). Decision-support utility only, not measured improvement."
    )

    confidence = 0.6

    return ActiveLearningReport(
        agent_name=AGENT_NAME,
        summary=summary,
        confidence=confidence,
        findings=findings,
        limitations=limitations,
        state_vector=state,
        action_utilities=action_utilities,
        rounds=rounds,
        action_distribution=result.distribution,
        best_recommendation=best,
        cumulative_regret=result.cumulative_regret,
        epsilon=epsilon,
        seed=seed,
        n_rounds=n_rounds,
    )
