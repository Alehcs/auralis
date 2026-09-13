"""Deduplicated observation split with original row indices and content binding."""

import hashlib
import json
from pathlib import Path

import pandas as pd

from processing.model_input import processed_filename


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_split(metadata_csv: Path, legacy_path: Path) -> dict:
    from sklearn.model_selection import train_test_split

    frame = pd.read_csv(metadata_csv)
    identities = frame.apply(processed_filename, axis=1)
    # Deduplication is justified only when ALL metadata agree for each file.
    if frame.groupby(identities).nunique(dropna=False).to_numpy().max() != 1:
        raise ValueError("Conflicting duplicate metadata: scientific review required")
    representatives = frame.index[~identities.duplicated()].tolist()
    train, val = train_test_split(representatives, test_size=0.2, random_state=42)
    legacy = json.loads(legacy_path.read_text())
    old_train = set(identities.iloc[legacy["train"]])
    old_val = set(identities.iloc[legacy["val"]])
    result = {
        "schema_version": 1, "strategy": "exact_duplicate_observations_first_row",
        "random_state": 42, "test_size": 0.2,
        "metadata_sha256": sha256(metadata_csv),
        "legacy_split": legacy_path.name, "legacy_split_sha256": sha256(legacy_path),
        "legacy_overlap_observations": len(old_train & old_val),
        "legacy_validation_leaked_rows": int(identities.iloc[legacy["val"]].isin(old_train).sum()),
        "train": train, "val": val,
        "source_rows": len(frame), "unique_observations": len(representatives),
        "observation_rows": {name: group.index.tolist()
                             for name, group in frame.groupby(identities, sort=False)},
        "status": "split_only_no_checkpoint_trained",
    }
    validate_split(result, metadata_csv)
    return result


def validate_split(split: dict, metadata_csv: Path) -> None:
    if split.get("metadata_sha256") != sha256(metadata_csv):
        raise ValueError("CSV differs from the split manifest")
    frame = pd.read_csv(metadata_csv)
    ids = frame.apply(processed_filename, axis=1)
    train, val = split["train"], split["val"]
    combined = train + val
    if (not train or not val or len(set(combined)) != len(combined)
            or any(type(i) is not int or not 0 <= i < len(frame) for i in combined)):
        raise ValueError("Invalid, repeated or overlapping split row indices")
    if set(ids.iloc[train]) & set(ids.iloc[val]):
        raise ValueError("Train/validation observation overlap")
    if len(combined) != ids.nunique() or ids.iloc[combined].nunique() != ids.nunique():
        raise ValueError("Split must contain exactly one row per observation")


def load_split(path: Path, metadata_csv: Path) -> dict:
    split = json.loads(path.read_text())
    validate_split(split, metadata_csv)
    return split
