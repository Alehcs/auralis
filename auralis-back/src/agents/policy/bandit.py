"""Deterministic epsilon-greedy bandit over a fixed weighted audit-need reward; not a model-gain measure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

import numpy as np

# Reward weights (must sum to 1.0).
W_ERROR = 0.40
W_UNDERREP = 0.30
W_UNCERTAINTY = 0.20
W_XAI = 0.10

DEFAULT_EPSILON = 0.1
DEFAULT_SEED = 42
DEFAULT_ROUNDS = 50


@dataclass(frozen=True)
class ActionSpec:
    """Maps an action to the specific need-keys it draws each reward term from."""

    action_id: str
    name: str
    description: str
    error_key: str
    underrep_key: str
    uncertainty_key: str
    xai_key: str


# Each action draws its reward terms from named needs (e.g. A5: tail error; A1/A4: low-activity underrep).
ACTIONS: List[ActionSpec] = [
    ActionSpec(
        "A1", "collect_more_low_activity",
        "Collect more low-activity magnetograms to balance the minority bin.",
        error_key="low_error_need",
        underrep_key="low_underrepresentation_need",
        uncertainty_key="uncertainty_need_proxy",
        xai_key="zero",
    ),
    ActionSpec(
        "A2", "collect_more_medium_activity",
        "Collect more medium-activity magnetograms.",
        error_key="medium_error_need",
        underrep_key="medium_underrepresentation_need",
        uncertainty_key="uncertainty_need_proxy",
        xai_key="zero",
    ),
    ActionSpec(
        "A3", "collect_more_high_activity",
        "Collect more high-activity magnetograms.",
        error_key="high_error_need",
        underrep_key="high_underrepresentation_need",
        uncertainty_key="uncertainty_need_proxy",
        xai_key="zero",
    ),
    ActionSpec(
        "A4", "collect_more_solar_minimum",
        "Collect more solar-minimum / quiet-Sun samples (emphasise low-activity gap).",
        error_key="low_error_need",
        underrep_key="low_underrepresentation_need",
        uncertainty_key="uncertainty_need_proxy",
        xai_key="zero",
    ),
    ActionSpec(
        "A5", "review_high_error_tail_samples",
        "Review / add high-error tail extreme (SI>2.0) samples — the measured weak spot.",
        error_key="tail_extreme_error_need",
        underrep_key="high_underrepresentation_need",
        uncertainty_key="uncertainty_need_proxy",
        xai_key="zero",
    ),
    ActionSpec(
        "A6", "review_high_uncertainty_samples",
        "Review / add high-uncertainty samples.",
        error_key="high_error_need",
        underrep_key="medium_underrepresentation_need",
        uncertainty_key="uncertainty_need_proxy",
        xai_key="zero",
    ),
    ActionSpec(
        "A7", "inspect_weak_xai_alignment_samples",
        "Manually inspect samples with weak XAI alignment.",
        error_key="zero",
        underrep_key="zero",
        uncertainty_key="uncertainty_need_proxy",
        xai_key="xai_risk_proxy",
    ),
]


def _need(state: Dict[str, float], key: str) -> float:
    if key == "zero":
        return 0.0
    return float(state.get(key, 0.0))


def action_utility(state: Dict[str, float], spec: ActionSpec) -> float:
    """Transparent weighted reward proxy for one action given the state vector."""
    return (
        W_ERROR * _need(state, spec.error_key)
        + W_UNDERREP * _need(state, spec.underrep_key)
        + W_UNCERTAINTY * _need(state, spec.uncertainty_key)
        + W_XAI * _need(state, spec.xai_key)
    )


@dataclass
class BanditResult:
    utilities: Dict[str, float]                 # action_id -> utility
    rounds: List[Dict[str, object]]             # per-round selection record
    distribution: Dict[str, int]                # action_id -> times selected
    best_action_id: str
    cumulative_regret: List[float]


def run_bandit(
    state: Dict[str, float],
    *,
    epsilon: float = DEFAULT_EPSILON,
    seed: int = DEFAULT_SEED,
    n_rounds: int = DEFAULT_ROUNDS,
    utility_fn: Callable[[Dict[str, float], ActionSpec], float] = action_utility,
) -> BanditResult:
    """Epsilon-greedy simulation over fixed utilities; regret = best utility - selected utility."""
    utilities = {spec.action_id: round(utility_fn(state, spec), 6) for spec in ACTIONS}
    best_action_id = max(utilities, key=lambda a: utilities[a])
    best_utility = utilities[best_action_id]

    rng = np.random.default_rng(seed)
    action_ids = [spec.action_id for spec in ACTIONS]

    rounds: List[Dict[str, object]] = []
    distribution: Dict[str, int] = {a: 0 for a in action_ids}
    cumulative_regret: List[float] = []
    running_regret = 0.0

    for t in range(n_rounds):
        explore = bool(rng.random() < epsilon)
        if explore:
            selected = action_ids[int(rng.integers(len(action_ids)))]
        else:
            selected = best_action_id

        reward = utilities[selected]
        regret = round(best_utility - reward, 6)
        running_regret = round(running_regret + regret, 6)

        distribution[selected] += 1
        rounds.append(
            {
                "round_index": t,
                "selected_action": selected,
                "is_exploration": explore,
                "reward": reward,
                "regret": regret,
            }
        )
        cumulative_regret.append(running_regret)

    return BanditResult(
        utilities=utilities,
        rounds=rounds,
        distribution=distribution,
        best_action_id=best_action_id,
        cumulative_regret=cumulative_regret,
    )
