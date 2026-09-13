#!/usr/bin/env python3
"""Offline, read-only consumer of Phase 3. No training, inference or source writes."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

PROBE = Path(__file__).resolve().parents[1]
ROOT = PROBE.parents[1]
BACK = ROOT / 'auralis-back'
CONTRACT = BACK / 'reports/phase3_temporal_model/noaa12975.sequence.v1.json'
sys.path.insert(0, str(BACK))
from src.processing.model_input import prepare_model_input


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(a):
    out = io.BytesIO()
    Image.fromarray(a, 'L').convert('RGBA').save(out, format='PNG', optimize=False)
    return out.getvalue()


def build():
    contract = json.loads(CONTRACT.read_bytes())
    assert contract['schema_version'] == '1.0.0'
    state = min(contract['states'], key=lambda s: s['order'])
    assert state['id'] == 'hmi-2022-03-24' and state['order'] == 1
    assert state['observation']['time']['record_utc'].startswith('2022-03-24T')
    refs = {a['id']: a for a in contract['artifacts']}
    input_ref = state['observation']['magnetogram']['artifact_ref']
    # Check all referenced source artifacts without publishing their files.
    sources = [input_ref, contract['preprocessing']['source_ref'], *[
        contract['model'][k] for k in ['manifest_ref', 'checkpoint_ref', 'onnx_ref']],
        state['observation']['target_si']['source_ref'], state['coronium_results']['source_ref']]
    for ref in sources:
        assert sha((BACK / refs[ref]['path']).read_bytes()) == refs[ref]['sha256'], ref
    x = np.load(BACK / input_ref, allow_pickle=False)
    assert x.shape == (512, 512) and x.dtype == np.float32
    assert np.isfinite(x).all() and np.max(np.abs(x)) <= 1
    channels = prepare_model_input(x)
    if hasattr(channels, 'numpy'):
        channels = channels.numpy()
    channels = np.asarray(channels)
    assert channels.shape == (2, 512, 512)
    plus, minus = channels
    assert np.array_equal(plus - minus, x)
    assert not np.any((plus > 0) & (minus > 0))
    means = [float(a.mean(dtype=np.float64)) for a in channels]
    polarity = state['derived']['polarity']
    assert np.allclose(means, [polarity['b_plus_mean'], polarity['b_minus_magnitude_mean']], rtol=0, atol=1e-12)
    # Row zero stays TOP. No flip, transpose, crop, inferred disk mask or registration.
    arrays = {
        'magnetogram': np.rint((x.astype(np.float64) + 1) * 127.5).astype('uint8'),
        'bplus': np.rint(plus.astype(np.float64) * 255).astype('uint8'),
        'bminus': np.rint(minus.astype(np.float64) * 255).astype('uint8'),
    }
    files = {f'{k}.png': encode(v) for k, v in arrays.items()}
    layers = {}
    for k in arrays:
        layers[k] = {'url': f'./assets/{k}.png', 'sha256': sha(files[f'{k}.png']),
            'width': 512, 'height': 512, 'range': [-1, 1] if k == 'magnetogram' else [0, 1],
            'encoding': 'round(255*(x+1)/2)' if k == 'magnetogram' else 'round(255*channel)',
            'unit': 'dimensionless_clip400', 'origin': 'upper_left_array_row0',
            'geometry': 'flat_reference_only', 'interpolation': 'nearest_in_2d_linear_mipmap_in_3d'}
    manifest = {
        'schema_version': 'auralis.phase5.v1', 'contract_schema_version': contract['schema_version'],
        'sequence_id': contract['sequence_id'], 'contract_sha256': sha(CONTRACT.read_bytes()),
        'state': state, 'model': contract['model'], 'preprocessing': contract['preprocessing'],
        'sources': [refs[ref] for ref in sources], 'layers': layers,
        'limitations': contract['limitations'],
        'visual': {'kind': 'illustrative_only', 'data_projection': 'none',
            'solar_surface': 'Unity-authored continuous sphere with multiscale 3D noise; visual recreation inspired by EUV imagery, not observed features',
            'back_surface': 'illustrative_continuation_not_observed', 'corona': 'camera-facing illustrative radial wisps, not measured'},
        'generation': {'generator': 'scripts/build-phase5-assets.py',
            'generator_sha256': sha(Path(__file__).read_bytes()), 'numpy': np.__version__,
            'quantization': '8-bit linear, signed max error 1/255; channels max error 0.5/255',
            'orientation': 'PNG[row,column] = array[row,column]; no certified solar north/east'},
    }
    files['state.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    # Asymmetric source witnesses detect accidental mirror/sign inversion.
    witnesses = []
    for row, col in [np.unravel_index(np.argmax(x), x.shape), np.unravel_index(np.argmin(x), x.shape), (123, 317), (381, 114)]:
        witnesses.append({'row': int(row), 'column': int(col), 'x': float(x[row, col]),
            **{k: int(a[row, col]) for k, a in arrays.items()}})
    report = {'state_id': state['id'], 'source_hash_verified': True, 'shape': list(x.shape),
        'channel_means': means, 'channels_match_contract': True, 'reconstruction_exact': True,
        'png_pixels_match_all_262144_positions': all(np.array_equal(np.array(Image.open(io.BytesIO(files[k+'.png'])).convert('L')), a) for k, a in arrays.items()),
        'witnesses': witnesses, 'output_hashes': {k: sha(v) for k, v in files.items()}}
    return files, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files, report = build()
    public = PROBE / 'web/public/phase5'
    for name, data in files.items():
        path = public / ('assets' if name.endswith('.png') else '') / name
        if args.check:
            assert path.read_bytes() == data, f'Changed derived artifact: {path.name}'
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            if name.endswith('.png'):
                unity = PROBE / 'unity/Assets/Phase5/Data' / name
                unity.parent.mkdir(parents=True, exist_ok=True)
                unity.write_bytes(data)
    if not args.check:
        path = PROBE / 'evidence/visual-polish/asset-verification.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
