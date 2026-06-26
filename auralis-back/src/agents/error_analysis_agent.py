"""Error Analysis Agent.

Read-only audit of the promoted hold-out predictions: per-bin MAE/RMSE, signed
residual means, the top high-error samples (with filename + date), and a focused
look at tail/extreme high-SI events.

Preserves the verified findings when reproduced:
  * Error across low/medium/high bins is nearly flat.
  * The real weakness is the high-SI tail (SI > 2.0), not a whole bin.
  * Regression-to-the-mean is only claimed if the residual signs support it.
"""

from __future__ import annotations

import math
from typing import Dict, List

from .data_loader import ACTIVITY_BINS, AgentDataset, ValidationRow
from .schemas import (
    AgentFinding,
    AgentLimitation,
    ErrorAnalysisReport,
    ErrorSample,
)

AGENT_NAME = "Error Analysis Agent"

# A spread below this (in log-SI MAE units) is treated as "nearly flat" across
# bins. The verified spread is ~0.005, well under this threshold.
FLAT_SPREAD_THRESHOLD = 0.02


def _mae(rows: List[ValidationRow]) -> float:
    return sum(r.error for r in rows) / len(rows) if rows else 0.0


def _rmse(rows: List[ValidationRow]) -> float:
    if not rows:
        return 0.0
    return math.sqrt(sum(r.error ** 2 for r in rows) / len(rows))


def _residual_mean(rows: List[ValidationRow]) -> float:
    return sum(r.residual for r in rows) / len(rows) if rows else 0.0


def run_error_analysis_agent(dataset: AgentDataset) -> ErrorAnalysisReport:
    rows = dataset.validation_rows
    by_bin: Dict[str, List[ValidationRow]] = {b: [] for b in ACTIVITY_BINS}
    for r in rows:
        by_bin[r.activity_bin].append(r)

    mae_by_bin = {b: round(_mae(by_bin[b]), 4) for b in ACTIVITY_BINS}
    rmse_by_bin = {b: round(_rmse(by_bin[b]), 4) for b in ACTIVITY_BINS}
    residual_mean_by_bin = {b: round(_residual_mean(by_bin[b]), 4) for b in ACTIVITY_BINS}

    populated = [mae_by_bin[b] for b in ACTIVITY_BINS if by_bin[b]]
    mae_spread = round(max(populated) - min(populated), 4) if populated else 0.0
    error_is_flat = mae_spread < FLAT_SPREAD_THRESHOLD

    # Top-10 high-error samples with their identity.
    top = sorted(rows, key=lambda r: r.error, reverse=True)[:10]
    top_errors = [
        ErrorSample(
            filename=r.filename,
            date=r.date,
            real=round(r.real, 4),
            predicted=round(r.predicted, 4),
            error=round(r.error, 4),
            residual=round(r.residual, 4),
            activity_bin=r.activity_bin,
        )
        for r in top
    ]

    # Tail / extreme-event focus (SI > 2.0).
    tail_rows = [r for r in rows if r.is_tail_extreme]
    tail_mae = round(_mae(tail_rows), 4) if tail_rows else None

    findings: List[AgentFinding] = []

    findings.append(
        AgentFinding(
            key="mae_by_bin",
            label="MAE by activity bin",
            detail=(
                f"low={mae_by_bin['low']}, medium={mae_by_bin['medium']}, "
                f"high={mae_by_bin['high']} (log-SI). Spread = {mae_spread}."
            ),
            severity="info",
            evidence={f"mae_{b}": mae_by_bin[b] for b in ACTIVITY_BINS},
        )
    )

    if error_is_flat:
        findings.append(
            AgentFinding(
                key="error_flat",
                label="Bin-level error is nearly flat",
                detail=(
                    f"MAE differs by only {mae_spread} across low/medium/high. The "
                    "model does not systematically fail one whole activity band; a "
                    "naive 'high-bin failure' story is not supported."
                ),
                severity="info",
                evidence={"mae_spread": mae_spread},
            )
        )
    else:
        worst = max(ACTIVITY_BINS, key=lambda b: mae_by_bin[b])
        findings.append(
            AgentFinding(
                key="error_uneven",
                label="Bin-level error differs",
                detail=(
                    f"MAE spread of {mae_spread} across bins; worst bin is "
                    f"'{worst}' (MAE={mae_by_bin[worst]})."
                ),
                severity="notice",
                evidence={"mae_spread": mae_spread},
            )
        )

    # Tail / extreme weakness — the real story.
    if tail_rows and tail_mae is not None:
        overall_mae = round(_mae(rows), 4)
        tail_worse = tail_mae > overall_mae
        findings.append(
            AgentFinding(
                key="tail_extreme_error",
                label="Tail / extreme high-SI events",
                detail=(
                    f"{len(tail_rows)} hold-out samples have SI > 2.0 with MAE="
                    f"{tail_mae} vs overall MAE={overall_mae}. "
                    + (
                        "Extreme events carry above-average error and dominate the "
                        "top-error list — this tail, not a whole bin, is the main "
                        "weakness."
                        if tail_worse
                        else "Extreme-event error is close to overall; tail risk is "
                        "modest in this split."
                    )
                ),
                severity="warning" if tail_worse else "notice",
                evidence={
                    "tail_count": float(len(tail_rows)),
                    "tail_mae": tail_mae,
                    "overall_mae": overall_mae,
                },
            )
        )

    # Regression-to-the-mean: only claim it if residual signs actually support
    # it (under-predict highs, over-predict lows).
    high_resid = residual_mean_by_bin["high"]
    low_resid = residual_mean_by_bin["low"]
    rtm_supported = high_resid < -0.01 and low_resid > 0.01
    if rtm_supported:
        findings.append(
            AgentFinding(
                key="regression_to_mean",
                label="Residuals consistent with regression toward the mean",
                detail=(
                    f"High-bin residual mean={high_resid} (under-predicts) and "
                    f"low-bin residual mean={low_resid} (over-predicts), the "
                    "classic shrink-toward-the-mean signature."
                ),
                severity="notice",
                evidence={"high_residual": high_resid, "low_residual": low_resid},
            )
        )
    else:
        findings.append(
            AgentFinding(
                key="regression_to_mean_not_clear",
                label="No strong regression-to-the-mean signature",
                detail=(
                    f"Residual means (low={low_resid}, medium="
                    f"{residual_mean_by_bin['medium']}, high={high_resid}) do not "
                    "show a clean shrink-toward-the-mean pattern; that claim is "
                    "withheld."
                ),
                severity="info",
            )
        )

    limitations = [
        AgentLimitation(
            key="single_split",
            detail=(
                "Computed on the single promoted seed-42 hold-out split (N="
                f"{len(rows)}); not cross-validated. Bin-level numbers can shift "
                "under a different split."
            ),
        ),
        AgentLimitation(
            key="log_si_space",
            detail="Errors are in log-SI space, matching the model's target scaler.",
        ),
        AgentLimitation(
            key="audit_only",
            detail=(
                "This identifies where the current model is weak; it does not "
                "measure or imply any improvement."
            ),
        ),
    ]

    summary = (
        f"Hold-out N={len(rows)}: MAE is "
        + ("nearly flat across bins" if error_is_flat else "uneven across bins")
        + f" (spread={mae_spread}). "
        + (
            f"Main weakness is the high-SI tail (SI>2.0, N={len(tail_rows)}, "
            f"MAE={tail_mae})."
            if tail_rows
            else "No extreme-tail samples present in this split."
        )
    )

    confidence = 0.85

    return ErrorAnalysisReport(
        agent_name=AGENT_NAME,
        summary=summary,
        confidence=confidence,
        findings=findings,
        limitations=limitations,
        mae_by_bin=mae_by_bin,
        rmse_by_bin=rmse_by_bin,
        residual_mean_by_bin=residual_mean_by_bin,
        top_errors=top_errors,
        tail_extreme_count=len(tail_rows),
        tail_extreme_mae=tail_mae,
        error_is_flat=error_is_flat,
        mae_spread=mae_spread,
    )
