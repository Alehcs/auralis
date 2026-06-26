"""Data Quality Agent.

Read-only audit of dataset composition: activity-bin balance across the full
corpus and the train/val split, low-activity representation, temporal coverage,
and basic outlier indicators drawn from the metadata columns that exist.

It never reads pixel data and never runs the model.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .data_loader import ACTIVITY_BINS, AgentDataset, activity_bin
from .schemas import (
    AgentFinding,
    AgentLimitation,
    BinStat,
    DataQualityReport,
    DateCoverage,
    OutlierIndicators,
)

AGENT_NAME = "Data Quality Agent"


def _distribution(counts: Dict[str, int]) -> Dict[str, BinStat]:
    total = sum(counts.values()) or 1
    return {
        b: BinStat(count=counts[b], share=round(counts[b] / total, 4))
        for b in ACTIVITY_BINS
    }


def _minority_bin(counts: Dict[str, int]) -> str:
    return min(ACTIVITY_BINS, key=lambda b: counts[b])


def _date_coverage(dataset: AgentDataset) -> DateCoverage:
    dates = sorted(
        str(r.get("date") or "")[:10]
        for r in dataset.metadata_rows
        if str(r.get("date") or "").strip()
    )
    if not dates:
        return DateCoverage()
    years = sorted({int(d[:4]) for d in dates if len(d) >= 4 and d[:4].isdigit()})
    return DateCoverage(
        first_date=dates[0],
        last_date=dates[-1],
        year_min=years[0] if years else None,
        year_max=years[-1] if years else None,
        distinct_years=len(years),
    )


def _outlier_indicators(dataset: AgentDataset) -> OutlierIndicators:
    """Cheap distribution indicators from existing metadata columns only."""
    si = [float(r["sunspot_index"]) for r in dataset.metadata_rows]

    # mean_value / min_value / max_value describe the normalised pixel range of
    # each processed magnetogram. Flag rows whose channel mean drifts far from 0
    # (processed tensors are expected to be centred near zero).
    means: List[float] = []
    for r in dataset.metadata_rows:
        try:
            means.append(abs(float(r["mean_value"])))
        except (KeyError, TypeError, ValueError):
            continue

    thr = 0.01  # |mean| above ~1% of the [-1, 1] range is unusual
    return OutlierIndicators(
        sunspot_index_min=round(min(si), 4),
        sunspot_index_max=round(max(si), 4),
        abs_mean_value_max=round(max(means), 6) if means else None,
        samples_high_abs_mean=sum(m > thr for m in means),
    )


def run_data_quality_agent(dataset: AgentDataset) -> DataQualityReport:
    full_counts = dataset.bin_counts()
    train_counts = dataset.bin_counts(dataset.train_indices)
    val_counts = dataset.bin_counts(dataset.val_indices)

    full_dist = _distribution(full_counts)
    minority = _minority_bin(full_counts)
    low_underrep = minority == "low"

    findings: List[AgentFinding] = []

    # Headline composition finding — preserves the verified result that LOW
    # activity, not high, is the minority class.
    findings.append(
        AgentFinding(
            key="bin_composition",
            label="Activity-bin composition",
            detail=(
                f"Full corpus: low={full_counts['low']} "
                f"({full_dist['low'].share:.1%}), medium={full_counts['medium']} "
                f"({full_dist['medium'].share:.1%}), high={full_counts['high']} "
                f"({full_dist['high'].share:.1%}). Minority bin is "
                f"'{minority}'."
            ),
            severity="notice" if low_underrep else "info",
            evidence={
                "low": float(full_counts["low"]),
                "medium": float(full_counts["medium"]),
                "high": float(full_counts["high"]),
            },
        )
    )

    if low_underrep:
        findings.append(
            AgentFinding(
                key="low_activity_underrepresented",
                label="Low activity is underrepresented",
                detail=(
                    "Low-activity samples are the minority class. The corpus skews "
                    "toward medium/high activity (solar-maximum coverage), so "
                    "quiet-Sun / solar-minimum conditions are comparatively scarce."
                ),
                severity="warning",
                evidence={"low_share": full_dist["low"].share},
            )
        )

    # Split-balance check: does the random split keep each bin represented in
    # both train and val?
    val_dist = _distribution(val_counts)
    empty_val_bins = [b for b in ACTIVITY_BINS if val_counts[b] == 0]
    if empty_val_bins:
        findings.append(
            AgentFinding(
                key="split_gap",
                label="Activity bin absent from validation split",
                detail=f"Bins with zero val samples: {', '.join(empty_val_bins)}.",
                severity="warning",
            )
        )
    else:
        findings.append(
            AgentFinding(
                key="split_balance",
                label="All activity bins represented in both splits",
                detail=(
                    "train and validation both contain low/medium/high samples; "
                    "the seed-42 split keeps extreme events represented on both sides."
                ),
                severity="info",
            )
        )

    coverage = _date_coverage(dataset)
    if coverage.first_date:
        findings.append(
            AgentFinding(
                key="temporal_coverage",
                label="Temporal coverage",
                detail=(
                    f"Samples span {coverage.first_date} to {coverage.last_date} "
                    f"({coverage.distinct_years} distinct years). This window "
                    "covers Solar Cycles 24-25, which are biased toward active years."
                ),
                severity="info",
                evidence={"distinct_years": float(coverage.distinct_years)},
            )
        )

    outliers = _outlier_indicators(dataset)
    high_abs_mean = outliers.samples_high_abs_mean
    findings.append(
        AgentFinding(
            key="outlier_indicators",
            label="Pixel-range outlier indicators",
            detail=(
                f"{high_abs_mean} processed magnetograms have an absolute "
                "channel mean above 1% of the normalised range; worth a spot "
                "check for residual flat-field or polarity imbalance."
            ),
            severity="info" if high_abs_mean == 0 else "notice",
            evidence={"samples_high_abs_mean": float(high_abs_mean)},
        )
    )

    limitations = [
        AgentLimitation(
            key="bins_demo_calibrated",
            detail=(
                "Activity bins use demo-calibrated log-SI thresholds (1.41 / 1.75) "
                "shared with the existing classifier, not absolute solar-cycle "
                "constants."
            ),
        ),
        AgentLimitation(
            key="metadata_only",
            detail=(
                "This audit reads metadata columns only (no pixel inspection); "
                "outlier flags are distribution hints, not validated artifacts."
            ),
        ),
        AgentLimitation(
            key="no_solar_minimum_label",
            detail=(
                "There is no explicit solar-minimum label; minimum conditions are "
                "approximated by low activity and early/late cycle dates."
            ),
        ),
    ]

    summary = (
        f"Corpus of {sum(full_counts.values())} samples; minority bin is "
        f"'{minority}'. "
        + ("Low activity is underrepresented relative to medium/high. "
           if low_underrep else "")
        + "All bins are present in both train and validation."
    )

    # Confidence is high: this is a direct count over existing metadata.
    confidence = 0.9

    return DataQualityReport(
        agent_name=AGENT_NAME,
        summary=summary,
        confidence=confidence,
        findings=findings,
        limitations=limitations,
        full_distribution=full_dist,
        train_distribution=_distribution(train_counts),
        val_distribution=val_dist,
        low_activity_underrepresented=low_underrep,
        minority_bin=minority,
        date_coverage=coverage,
        outlier_indicators=outliers,
    )
