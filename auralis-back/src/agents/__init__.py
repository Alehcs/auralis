"""Auralis Agent Lab — read-only scientific audit layer.

This package adds a multi-agent audit/recommendation layer on top of the
existing Coronium V3 PRO system. It is strictly additive and read-only: it never
modifies the model, ONNX artifact, checkpoints, metrics, preprocessing, split
files, CSVs, or experiment JSONs. The agents only summarise artifacts that
already exist on disk and produce decision-support recommendations — they do not
retrain and do not claim to improve the model.
"""

from .data_loader import AgentDataError, AgentDataset, load_agent_dataset
from .data_quality_agent import run_data_quality_agent
from .error_analysis_agent import run_error_analysis_agent
from .xai_review_agent import run_xai_review_agent
from .active_learning_agent import run_active_learning_agent
from .report_agent import build_full_report

__all__ = [
    "AgentDataError",
    "AgentDataset",
    "load_agent_dataset",
    "run_data_quality_agent",
    "run_error_analysis_agent",
    "run_xai_review_agent",
    "run_active_learning_agent",
    "build_full_report",
]
