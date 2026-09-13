"""Offline audit of existing HMI observations for Phase 2; never downloads data.

Run from any directory with the repository's full Python environment.
NOAA text snapshots and their retrieval manifest must already be in sources/.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/auralis-phase2-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import onnxruntime as ort
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from src.models.active_model import load_release, ONNX_PATH, MANIFEST_PATH
from src.processing.model_input import prepare_model_input, processed_filename
from src.processing.observation_time import filename_time
from src.processing.scientific_split import load_split

OUT = ROOT / "reports/phase2_historical_case"
WINDOWS = [
    ("2017_sep", "2017-08-23", "2017-09-14", 12673),
    ("2022_mar", "2022-03-24", "2022-04-05", 12975),
    ("2023_dec", "2023-12-08", "2023-12-18", 13514),
    ("2024_may", "2024-05-01", "2024-05-16", 13664),
    ("2024_oct", "2024-09-25", "2024-10-10", 13842),
]
SELECTED_DAYS = ["2022-03-24", "2022-03-25", "2022-03-28", "2022-03-29", "2022-03-30"]
EVENT_ANCHORS = {
    "2017_sep": ("2017-09-06T12:02:00Z", "X9.3"),
    "2022_mar": ("2022-03-30T17:37:00Z", "X1.3"),
    "2023_dec": ("2023-12-14T17:02:00Z", "X2.8"),
    "2024_may": ("2024-05-14T16:51:00Z", "X8.7"),
    "2024_oct": ("2024-10-03T12:18:00Z", "X9.0"),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def srs(day, noaa):
    path = OUT / "sources" / (day.replace("-", "") + "SRS.txt")
    body = path.read_text()
    section = body.split("Nmbr Location")[1].split("IA.")[0]
    regions = []
    for line in section.splitlines():
        fields = line.split()
        if fields and re.fullmatch(r"\d{4}", fields[0]):
            regions.append(dict(noaa=10000 + int(fields[0]), location=fields[1],
                                carrington_longitude_deg=int(fields[2]),
                                area_millionths_hemisphere=int(fields[3]),
                                magnetic_type=fields[7], source_line=line))
    match = next((r for r in regions if r["noaa"] == noaa), None)
    harp_path = OUT / "sources/harp_mapping_attempt_0.txt"
    harp_matches = []
    for line in harp_path.read_text().splitlines()[1:]:
        harp, ars = line.split()
        if str(noaa) in ars.split(","):
            harp_matches.append((harp, ars))
    return dict(context_noaa=noaa, srs_region_present=match is not None,
                srs_location=match["location"] if match else "not_in_spotted_region_table",
                srs_magnetic_type=match["magnetic_type"] if match else "unknown",
                srs_area_msh=match["area_millionths_hemisphere"] if match else None,
                srs_valid_utc=day + "T00:00:00Z", srs_issued_utc=day + "T00:30:00Z",
                srs_other_regions=";".join(str(r["noaa"]) for r in regions if r["noaa"] != noaa),
                srs_path=str(path.relative_to(ROOT)), srs_sha256=sha(path),
                harp=";".join(h for h, ars in harp_matches),
                harp_noaa_lifetime_mapping=";".join(ars for h, ars in harp_matches),
                harp_scope="catalog_lifetime_association_not_exact_time_patch_assignment",
                spatial_assignment="full_disk_context_only_no_WCS_or_region_mask")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    load_release()
    metadata_path = ROOT / "data/processed/metadata_processed.csv"
    original = pd.read_csv(metadata_path)
    original["local_filename"] = original.apply(processed_filename, axis=1)
    assert original.groupby("local_filename").nunique(dropna=False).to_numpy().max() == 1
    unique = original.drop_duplicates("local_filename")
    split = load_split(ROOT / "models/split_indices_phase1_v1.json", metadata_path)
    train, val = set(split["train"]), set(split["val"] if "val" in split else split["validation"])
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(ONNX_PATH), sess_options=options, providers=["CPUExecutionProvider"])
    inventory, candidates = [], []
    for idx, row in unique.iterrows():
        name = row.local_filename
        t = filename_time(name)
        assert t["date_utc"] is not None
        day = t["date_original"][:10]
        path = ROOT / "data/processed" / name
        arr = np.load(path, allow_pickle=False)
        inp = prepare_model_input(arr)
        assert arr.shape == (512, 512) and arr.dtype == np.float32
        assert abs(float(arr.mean()) - float(row.mean_value)) < 1e-7
        item = dict(source_row=int(idx), metadata_rows=";".join(map(str, original.index[original.local_filename == name])),
                    local_file=str(path.relative_to(ROOT)), processed_file=name, sha256=sha(path),
                    record_tai=t["date_original"], record_utc=t["date_utc"], day=day,
                    csv_date_unknown_scale=row.date, target_si=float(row.sunspot_index),
                    target_provenance="stored_original_4096x4096_pixel_percentage_not_recomputed_from_npy",
                    split="train" if idx in train else "selection_validation" if idx in val else "unknown",
                    shape=str(arr.shape), dtype=str(arr.dtype))
        inventory.append(item)
        for label, start, end, noaa in WINDOWS:
            if start <= day <= end:
                pred = float(session.run(None, {session.get_inputs()[0].name: inp[None]})[0].reshape(-1)[0])
                anchor, goes_class = EVENT_ANCHORS[label]
                candidates.append(dict(item, candidate=label, prediction_onnx_si=pred,
                                       prediction_api_4dp=round(pred, 4), selected=day in SELECTED_DAYS,
                                       context_event_peak_utc=anchor, context_event_goes_class=goes_class,
                                       hours_before_context_event=(pd.Timestamp(anchor)-pd.Timestamp(t["date_utc"])).total_seconds()/3600,
                                       **srs(day, noaa)))
    inv = pd.DataFrame(inventory).sort_values("record_utc")
    cand = pd.DataFrame(candidates).sort_values("record_utc")
    seq = cand[cand.selected].copy()
    seq.insert(0, "state", range(1, len(seq) + 1))
    seq["delta_target_si_pp"] = seq.target_si.diff()
    seq["gap_hours"] = pd.to_datetime(seq.record_utc).diff().dt.total_seconds() / 3600
    peak = pd.Timestamp("2022-03-30T17:37:00Z")
    seq["hours_before_x13_peak"] = (peak - pd.to_datetime(seq.record_utc)).dt.total_seconds() / 3600
    inv.to_csv(OUT / "local_inventory.csv", index=False)
    cand.to_csv(OUT / "candidates.csv", index=False)
    seq.to_csv(OUT / "recommended_sequence.csv", index=False)
    appendix = ["# Candidatos locales auditados — Fase 2", "",
                "SI real = etiqueta original guardada; predicción = ONNX V3.1 determinista CPU.",
                "UTC convierte el tiempo de registro TAI; no sustituye T_OBS. NOAA y HARP son contexto externo, no una máscara del archivo.",
                "Las posiciones SRS son válidas a las 00:00 UTC del día. Ausente = no figura en la tabla I del boletín, no prueba de ausencia física absoluta.",
                "HARP es una asociación de catálogo a lo largo de su vida y puede incluir varias regiones.", ""]
    for label, start, end, noaa in WINDOWS:
        peak_time, cls = EVENT_ANCHORS[label]
        appendix.extend([f"## {label}: NOAA {noaa}; evento de contexto {cls}, {peak_time}", "",
                         "| Archivo local | Registro UTC | SI real | V3.1 ONNX | NOAA en SRS / posición | Tipo magnético | HARP | Split |",
                         "| --- | --- | ---: | ---: | --- | --- | --- | --- |"])
        for row in cand[cand.candidate == label].itertuples():
            location = row.srs_location if row.srs_region_present else "Ausente en tabla I"
            appendix.append(f"| [{row.processed_file}](../../{row.local_file}) | {row.record_utc} | {row.target_si:.6f} | {row.prediction_onnx_si:.6f} | [{noaa}: {location}](sources/{Path(row.srs_path).name}) | {row.srs_magnetic_type} | {row.harp} | {row.split} |")
        appendix.append("")
    appendix.extend(["Los CSV conservan precisión completa, hashes, filas originales, fecha CSV de escala desconocida, diferencias temporales al evento, otras regiones presentes y alcance de las asociaciones.", ""])
    (OUT / "candidates.md").write_text("\n".join(appendix))
    events = []
    pattern = re.compile(r"^\s*(\d+)\s+\+?\s*(\d{4})\s+(\d{4})\s+(\d{4})\s+(G\d+)\s+\d\s+XRA\s+1-8A\s+([MX][\d.]+)\s+\S+(?:\s+(\d{4}))?\s*$")
    for path in sorted((OUT / "sources").glob("*events.txt")):
        d = path.name[:8]
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            match = pattern.match(line)
            if not match:
                continue
            event, start, peak_time, end, obs, cls, region = match.groups()
            def stamp(hhmm):
                return f"{d[:4]}-{d[4:6]}-{d[6:]}T{hhmm[:2]}:{hhmm[2:]}:00Z"
            events.append(dict(catalog_id=d+"_"+event, begin_utc=stamp(start), peak_utc=stamp(peak_time),
                               end_hhmm_reported=end, goes_class=cls, satellite=obs,
                               noaa=10000+int(region) if region else None,
                               source_file=str(path.relative_to(ROOT)), source_line_number=lineno, raw_line=line))
    events = pd.DataFrame(events)
    events.to_csv(OUT / "cataloged_mx_events.csv", index=False)
    for label, start, end, region in WINDOWS:
        peak_time, cls = EVENT_ANCHORS[label]
        assert ((events.peak_utc == peak_time) & (events.goes_class == cls) & (events.noaa == region)).any()
    # Enumerate consecutive observations, without sorting on SI or deleting dips.
    rolling = []
    for i in range(len(inv) - 4):
        w = inv.iloc[i:i + 5]
        times = pd.to_datetime(w.record_utc)
        span = (times.iloc[-1] - times.iloc[0]).total_seconds() / 86400
        if span <= 10:
            delta = np.diff(w.target_si.to_numpy())
            rolling.append(dict(start=w.day.iloc[0], end=w.day.iloc[-1], span_days=span,
                                net_target_change_pp=float(w.target_si.iloc[-1] - w.target_si.iloc[0]),
                                decreases=int(np.sum(delta < 0)),
                                files=";".join(w.processed_file)))
    pd.DataFrame(rolling).to_csv(OUT / "five_state_windows_up_to_10_days.csv", index=False)
    # Verify serving parity on the candidates that already have a frozen result.
    frozen = pd.read_csv(ROOT / "reports/phase16_coronium_v3_1/coronium_v3_1_deterministic_predictions.csv")
    common = cand.merge(frozen[["processed_file", "onnx_si"]], on="processed_file")
    max_diff = float(np.max(np.abs(common.prediction_onnx_si - common.onnx_si)))
    assert max_diff < 2e-6
    repeat = []
    for name in seq.processed_file:
        inp = prepare_model_input(np.load(ROOT / "data/processed" / name, allow_pickle=False))[None]
        repeat.append(float(session.run(None, {session.get_inputs()[0].name: inp})[0].reshape(-1)[0]))
    assert np.array_equal(repeat, seq.prediction_onnx_si.to_numpy())
    assert len(seq) == 5 and seq.record_utc.is_monotonic_increasing
    assert seq.srs_region_present.all()
    assert set(inv.processed_file) == {p.name for p in (ROOT / "data/processed").glob("*.npy")}
    retrieval = json.loads((OUT / "sources/retrieval_manifest.json").read_text())
    for source in retrieval:
        if "sha256" in source:
            assert sha(OUT / "sources" / source["file"]) == source["sha256"]
    verification = dict(unique_observations=len(inv), csv_rows=len(original),
                        duplicates=len(original) - len(inv), candidates=len(cand),
                        five_state_windows_up_to_10_days=len(rolling), selected_states=len(seq),
                        frozen_comparison_count=len(common), frozen_max_abs_diff=max_diff,
                        deterministic_repeat_identical=True, source_hashes_verified=True,
                        selected_region_present_in_all_srs=True,
                        event_anchors_verified_against_noaa=True,
                        all_local_arrays_validated=True, all_local_files_have_metadata=True,
                        no_new_magnetograms=True, raw_fits_files=len(list((ROOT / "data/raw").glob("*"))),
                        date_range=[inv.day.min(), inv.day.max()],
                        selected_net_si_change_pp=float(seq.target_si.iloc[-1] - seq.target_si.iloc[0]),
                        selected_relative_change_percent=float((seq.target_si.iloc[-1]/seq.target_si.iloc[0]-1)*100),
                        selected_prediction_net_change_pp=float(seq.prediction_onnx_si.iloc[-1]-seq.prediction_onnx_si.iloc[0]))
    save_json("verification.json", verification)
    fig, axes = plt.subplots(1, 5, figsize=(16, 4.2), layout="constrained")
    for ax, row in zip(axes, seq.itertuples()):
        arr = np.load(ROOT / row.local_file, allow_pickle=False)
        im = ax.imshow(arr, cmap="RdBu_r", vmin=-1, vmax=1, origin="lower")
        ax.set_title(f"{row.day}\nSI {row.target_si:.4f} | ONNX {row.prediction_onnx_si:.4f}", fontsize=10)
        ax.set_axis_off()
    fig.colorbar(im, ax=axes, shrink=.65, label="Entrada normalizada [-1, 1]")
    fig.suptitle("HMI local: disco completo, orden de matriz (sin registro WCS ni identificación de píxeles NOAA)", fontsize=12)
    fig.savefig(OUT / "selected_magnetograms.png", dpi=180)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 4.8), layout="constrained")
    dates = pd.to_datetime(seq.record_utc)
    ax.plot(dates, seq.target_si, "o-", label="SI real guardado (disco completo)")
    ax.plot(dates, seq.prediction_onnx_si, "s--", label="Coronium V3.1: ONNX determinista CPU")
    ax.axvline(peak, color="firebrick", ls=":", label="GOES X1.3: 30 mar 17:37 UTC (posterior)")
    ax.set_ylabel("SI: porcentaje de píxeles originales con |B_LOS| > 200 G")
    ax.set_xlabel("UTC de registro; las líneas solo conectan observaciones, no reconstruyen huecos")
    ax.set_title("24–30 marzo 2022: aumento global con una caída real al final")
    ax.grid(alpha=.2)
    ax.legend(loc="lower right", fontsize=8)
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d mar\n%H:%M", tz=timezone.utc))
    fig.savefig(OUT / "activity_evolution.png", dpi=200)
    fig.savefig(OUT / "activity_evolution.svg")
    plt.close(fig)
    save_json("manifest.json", dict(created_utc=datetime.now(timezone.utc).isoformat(),
        model="Coronium V3.1", protocol="deterministic ONNX CPU, batch 1, four intra-op threads, no noise or MC",
        report_sha256=sha(ROOT.parent / "docs/phase2.md"),
        inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in [metadata_path, ONNX_PATH, MANIFEST_PATH,
            ROOT / "src/processing/model_input.py", ROOT / "src/processing/observation_time.py",
            ROOT / "models/split_indices_phase1_v1.json", Path(__file__)]},
        environment=dict(python=sys.version, platform=platform.platform(),
                         packages={n: importlib.metadata.version(n) for n in ["numpy", "pandas", "onnxruntime", "astropy", "matplotlib"]}),
        outputs_sha256={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name != "manifest.json"}))
    print(json.dumps(verification, indent=2))
    print(seq[["state", "day", "target_si", "prediction_onnx_si", "srs_location", "srs_magnetic_type", "split"]].to_string(index=False))


if __name__ == "__main__":
    main()
