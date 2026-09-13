#!/usr/bin/env python3
"""Build/check the frozen Phase 3 case offline; paths in JSON are backend-relative."""
import argparse
import copy
import csv
import hashlib
import importlib.metadata
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

import jsonschema
import numpy as np

BACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACK))
from src.processing.model_input import INPUT_CONTRACT, TARGET_CONTRACT, prepare_model_input
from src.processing.observation_time import filename_time

PHASE2 = BACK / 'reports/phase2_historical_case'
OUT = BACK / 'reports/phase3_temporal_model'
SCHEMA = BACK / 'contracts/temporal-sequence-v1.schema.json'
DATA = OUT / 'noaa12975.sequence.v1.json'
DAYS = ['2022-03-24', '2022-03-25', '2022-03-28', '2022-03-29', '2022-03-30']
EVENT_IDS = ['20220328_3390', '20220328_3570', '20220329_3630', '20220329_3990', '20220330_4220', '20220331_4520']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def rows(path):
    with Path(path).open(newline='') as f:
        return list(csv.DictReader(f))


def utc(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def build():
    manifest = read_json(PHASE2 / 'manifest.json')
    # Check the upstream frozen dependencies before using their values.
    for rel, expected in manifest['inputs_sha256'].items():
        require(sha(BACK / rel) == expected, f'Phase 2 input changed: {rel}')
    for name in ['recommended_sequence.csv', 'candidates.csv', 'cataloged_mx_events.csv']:
        require(sha(PHASE2 / name) == manifest['outputs_sha256'][name], f'Phase 2 output changed: {name}')
    model_manifest = read_json(BACK / 'models/coronium_v3_1_manifest.json')
    for rel in ['models/best_coronium_v3_1.pth', 'models/best_coronium_v3_1.onnx']:
        require(sha(BACK / rel) == model_manifest['artifacts_sha256'][rel], f'Model changed: {rel}')
    retrieval = {x['file']: x for x in read_json(PHASE2 / 'sources/retrieval_manifest.json') if 'file' in x}
    artifacts = {}

    def artifact(rel):
        path = BACK / rel
        if rel not in artifacts:
            info = retrieval.get(path.name, {}) if path.parent == PHASE2 / 'sources' else {}
            digest = sha(path)
            if info.get('sha256'):
                require(digest == info['sha256'], f'Snapshot changed: {rel}')
            artifacts[rel] = dict(id=rel, path=rel, sha256=digest,
                                  url=info.get('url'), retrieved_utc=info.get('retrieved_utc'))
        return rel

    selection_ref = artifact('reports/phase2_historical_case/recommended_sequence.csv')
    candidates_ref = artifact('reports/phase2_historical_case/candidates.csv')
    events_ref = artifact('reports/phase2_historical_case/cataloged_mx_events.csv')
    metadata_ref = artifact('data/processed/metadata_processed.csv')
    for rel in ['reports/phase2_historical_case/manifest.json', 'reports/phase2_historical_case/sources/retrieval_manifest.json',
                'scripts/select_phase2_history.py', 'src/processing/observation_time.py',
                'models/split_indices_phase1_v1.json', 'scripts/build_phase3_temporal.py',
                'contracts/temporal-sequence-v1.schema.json']:
        artifact(rel)
    selected = rows(BACK / selection_ref)
    require([r['day'] for r in selected] == DAYS, 'Only the five approved states are allowed')
    states = []
    for order, r in enumerate(selected, 1):
        time = filename_time(r['processed_file'])
        require(time['date_original'] == r['record_tai'] and time['date_utc'] == r['record_utc'], 'TAI/UTC mismatch')
        require(sha(BACK / r['local_file']) == r['sha256'], 'Magnetogram hash mismatch')
        require(r['context_noaa'] == '12975' and r['harp'] == '8088', 'Wrong region')
        require(sha(BACK / r['srs_path']) == r['srs_sha256'], 'SRS hash mismatch')
        a = np.load(BACK / r['local_file'], allow_pickle=False)
        require(a.shape == (512, 512) and a.dtype == np.float32, 'Wrong matrix contract')
        channels = prepare_model_input(a)
        srs_lines = (BACK / r['srs_path']).read_text().splitlines()
        matches = [(i + 1, line) for i, line in enumerate(srs_lines) if line.split() and line.split()[0] == '2975']
        require(len(matches) == 1 and r['srs_location'] in matches[0][1], 'SRS location mismatch')
        target = float(r['target_si'])
        prediction = float(r['prediction_onnx_si'])
        sid = 'hmi-' + r['day']
        states.append(dict(
            id=sid, order=order,
            observation=dict(
                id=sid + '-observation', kind='observational', scope='full_disk',
                magnetogram=dict(artifact_ref=artifact(r['local_file']), filename=r['processed_file'], shape=[512, 512], dtype='float32', unit='dimensionless_clip400'),
                time=dict(record_tai=r['record_tai'], record_utc=r['record_utc'], source='filename_record_time',
                          exposure_utc=None, csv_date_unknown_scale=r['csv_date_unknown_scale']),
                region_context=dict(noaa=12975, harp=8088, harp_scope=r['harp_scope'],
                    harp_noaa_lifetime_mapping=[int(n) for n in r['harp_noaa_lifetime_mapping'].split(',')],
                    harp_source_ref=artifact('reports/phase2_historical_case/sources/harp_mapping_attempt_0.txt'),
                    location=dict(reported=r['srs_location'], coordinate_system='SRS_heliographic_cardinal_text',
                                  valid_utc=r['srs_valid_utc'], issued_utc=r['srs_issued_utc'], source_ref=artifact(r['srs_path']),
                                  source_line=matches[0][0], raw_line=matches[0][1], pixel_position=None),
                    magnetic_type=r['srs_magnetic_type'], area_millionths_solar_hemisphere=float(r['srs_area_msh']),
                    other_noaa_regions=[int(n) for n in r['srs_other_regions'].split(';')],
                    wcs=None, region_mask=None, magnetic_field_3d=None),
                target_si=dict(value=target, unit='percent_original_full_disk_pixels', contract=TARGET_CONTRACT,
                               provenance=r['target_provenance'], source_ref=metadata_ref,
                               metadata_row_indices=[int(n) for n in r['metadata_rows'].split(';')]),
                split=r['split'], source_ref=selection_ref, source_csv_row_1based=order),
            coronium_results=dict(
                kind='model_inference', model_ref='coronium-3.1', preprocessing_ref=INPUT_CONTRACT,
                protocol='deterministic_onnx_cpu_eval_batch1_threads4_no_noise_no_mc',
                prediction_si=prediction, unit='SI_percentage_points', api_display_4dp=float(r['prediction_api_4dp']),
                source_ref=selection_ref,
                grad_cam=dict(status='not_available', artifact_ref=None,
                              reason='No frozen Grad-CAM artifact with matching state/model provenance was found; not generated in Phase 3.',
                              interpretation='Model attribution, not a region mask, probability, magnetic field or flare measurement.')),
            derived=dict(kind='observation_derived', preprocessing_ref=INPUT_CONTRACT,
                polarity=dict(unit='dimensionless_clip400', scope='full_512x512_array', shape=[2, 512, 512],
                    channel_order=['B_plus', 'B_minus_magnitude'], recipe='B_plus=max(x,0); B_minus_magnitude=max(-x,0)',
                    b_plus_mean=float(channels[0].mean(dtype=np.float64)),
                    b_minus_magnitude_mean=float(channels[1].mean(dtype=np.float64)),
                    channel_storage='reconstruct_from_magnetogram', physical_flux=None),
                delta_target_si_pp=None if not states else target - states[-1]['observation']['target_si']['value'],
                gap_seconds=None if not states else int((utc(r['record_utc']) - utc(states[-1]['observation']['time']['record_utc'])).total_seconds())),
            visual=dict(kind='visual_only', assets=[], spatial_registration='unavailable', interpolation='none')))
    events = []
    catalog = rows(BACK / events_ref)
    for eid in EVENT_IDS:
        found = [r for r in catalog if r['catalog_id'] == eid]
        require(len(found) == 1, f'Event not unique: {eid}')
        r = found[0]
        require(float(r['noaa']) == 12975, 'Wrong event region')
        line = (BACK / r['source_file']).read_text().splitlines()[int(r['source_line_number']) - 1]
        require(line == r['raw_line'], 'Event source line mismatch')
        peak = utc(r['peak_utc'])
        before = [s for s in states if utc(s['observation']['time']['record_utc']) < peak]
        after = [s for s in states if utc(s['observation']['time']['record_utc']) > peak]
        end = utc(r['begin_utc']).replace(hour=int(r['end_hhmm_reported'][:2]), minute=int(r['end_hhmm_reported'][2:]))
        if end < utc(r['begin_utc']):
            end += timedelta(days=1)
        events.append(dict(id=eid, kind='observational_event', type='GOES_XRA_1_8A', noaa=12975,
            goes_class=r['goes_class'], satellite=r['satellite'], start_utc=r['begin_utc'], peak_utc=r['peak_utc'],
            end_utc=end.isoformat().replace('+00:00', 'Z'), source_ref=artifact(r['source_file']),
            source_line=int(r['source_line_number']), raw_line=r['raw_line'], catalog_ref=events_ref,
            temporal_relation=dict(basis='peak_utc', placement='between_states' if before and after else 'after_last_state',
                preceding_state_id=before[-1]['id'] if before else None, following_state_id=after[0]['id'] if after else None,
                seconds_after_preceding_state=int((peak - utc(before[-1]['observation']['time']['record_utc'])).total_seconds()) if before else None,
                captured_by_state_id=None), association='NOAA_catalog_region_context_not_model_prediction'))
    reserve = [r for r in rows(BACK / candidates_ref) if r['day'] == '2022-04-01']
    require(len(reserve) == 1, 'Missing April 1 reserve')
    r = reserve[0]
    require(sha(BACK / r['local_file']) == r['sha256'], 'Reserve hash mismatch')
    data = dict(schema_version='1.0.0', sequence_id='noaa12975-20220324-20220330-v1',
        title='NOAA 12975 context / full-disk HMI historical SI', path_base='auralis-back',
        scope='full_disk_SI_with_regional_catalog_context', independent_test=False,
        event_catalog_scope='Six selected Phase 2 NOAA 12975 M/X events; not exhaustive; includes post-sequence context.',
        model=dict(id='coronium-3.1', name='Coronium V3.1', version='3.1',
                   manifest_ref=artifact('models/coronium_v3_1_manifest.json'),
                   checkpoint_ref=artifact('models/best_coronium_v3_1.pth'), onnx_ref=artifact('models/best_coronium_v3_1.onnx')),
        preprocessing=dict(id=INPUT_CONTRACT, version='1', source_ref=artifact('src/processing/model_input.py'),
            stored_input='clip(resize(B_LOS),-400,400)/400', input_transform='[max(x,0),max(-x,0)]',
            target_contract=TARGET_CONTRACT, target_transform='none',
            target_definition='100 * count(abs(original B_LOS)>200 G) / original_pixel_count'),
        states=states, events=events,
        optional_reserve=dict(enabled=False, date='2022-04-01', magnetogram_ref=artifact(r['local_file']),
            record_tai=r['record_tai'], record_utc=r['record_utc'], source_ref=candidates_ref,
            reason='Optional existing observation only; not a sixth state or an event boundary.'),
        limitations=['No original FITS, exposure time, WCS, HARP masks or certified pixel orientation.',
            'SRS coordinates describe the regional catalog at its own valid time, not registered image pixels.',
            'HARP 8088 is a lifetime association shared with NOAA 12976, 12977 and 12984.',
            'SI labels are stored original measurements; cannot be recovered exactly from resized/clipped arrays.',
            'B+/B- are nonnegative normalized channel magnitudes, not regional or deprojected magnetic flux.',
            'Four training states and one selection-validation state; no independent temporal validation.',
            'Irregular sampling; no observed state at the X1.3 event and no validated physical interpolation.',
            'Coronium estimates current full-disk SI; it does not predict GOES flares or future activity.'],
        artifacts=[])
    data['artifacts'] = sorted(artifacts.values(), key=lambda x: x['id'])
    return data


def validate(data, expected):
    schema = read_json(SCHEMA)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(data)
    require(data == expected, 'Case content differs from independently rebuilt, hash-checked Phase 2 inputs')
    ids = [s['id'] for s in data['states']]
    require(len(ids) == len(set(ids)) == 5, 'State ID/count mismatch')
    for e in data['events']:
        require(utc(e['start_utc']) <= utc(e['peak_utc']) <= utc(e['end_utc']), 'Invalid event interval')
    x = next(e for e in data['events'] if e['goes_class'] == 'X1.3')
    require(x['temporal_relation']['seconds_after_preceding_state'] == 63367, 'X1.3 offset mismatch')
    refs = {a['id'] for a in data['artifacts']}
    def walk(value):
        if isinstance(value, dict):
            for key, val in value.items():
                if key.endswith('_ref') and val is not None and key not in ['model_ref', 'preprocessing_ref']:
                    require(val in refs, f'Unresolved artifact: {val}')
                walk(val)
        elif isinstance(value, list):
            for val in value:
                walk(val)
    walk(data)
    for a in data['artifacts']:
        path = (BACK / a['path']).resolve()
        require(path.is_relative_to(BACK) and sha(path) == a['sha256'], f'Invalid artifact: {a["path"]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate saved output without rewriting it')
    args = parser.parse_args()
    expected = build()
    data = read_json(DATA) if args.check else expected
    if args.check:
        verification = read_json(OUT / 'verification.json')
        for field, path in [('sequence_sha256', DATA), ('schema_sha256', SCHEMA), ('builder_sha256', Path(__file__))]:
            require(verification[field] == sha(path), f'Phase 3 output changed: {path.name}')
    validate(data, expected)
    import onnxruntime as ort
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(BACK / data['model']['onnx_ref']), sess_options=options, providers=['CPUExecutionProvider'])
    differences = []
    for state in data['states']:
        a = np.load(BACK / state['observation']['magnetogram']['artifact_ref'], allow_pickle=False)
        pred = float(session.run(None, {session.get_inputs()[0].name: prepare_model_input(a)[None]})[0].reshape(-1)[0])
        differences.append(abs(pred - state['coronium_results']['prediction_si']))
    require(max(differences) <= 1e-6, 'ONNX predictions differ from Phase 2')
    mutations = {
        'false_utc': lambda d: d['states'][0]['observation']['time'].__setitem__('record_utc', '2022-03-24T00:01:30Z'),
        'duplicate_state': lambda d: d['states'][1].__setitem__('id', d['states'][0]['id']),
        'sixth_state': lambda d: d['states'].append(copy.deepcopy(d['states'][-1])),
        'wrong_hash': lambda d: d['artifacts'][0].__setitem__('sha256', '0' * 64),
        'invented_wcs': lambda d: d['states'][0]['observation']['region_context'].__setitem__('wcs', {}),
        'negative_b_minus': lambda d: d['states'][0]['derived']['polarity'].__setitem__('b_minus_magnitude_mean', -1),
        'false_flare_capture': lambda d: d['events'][4]['temporal_relation'].__setitem__('captured_by_state_id', d['states'][-1]['id']),
        'reserve_enabled': lambda d: d['optional_reserve'].__setitem__('enabled', True),
        'unknown_version': lambda d: d.__setitem__('schema_version', '2.0.0'),
        'lost_final_decline': lambda d: d['states'][-1]['derived'].__setitem__('delta_target_si_pp', 0.01),
        'broken_reference': lambda d: d['states'][0]['coronium_results'].__setitem__('model_ref', 'missing'),
    }
    for name, mutate in mutations.items():
        bad = copy.deepcopy(data)
        mutate(bad)
        try:
            validate(bad, expected)
        except (ValueError, jsonschema.ValidationError):
            continue
        raise ValueError(f'Negative check failed: {name}')
    if not args.check:
        OUT.mkdir(parents=True, exist_ok=True)
        write_json(DATA, data)
        write_json(OUT / 'verification.json', dict(status='passed', states=5, events=6, reserve_enabled=False,
            artifact_hashes_checked=len(data['artifacts']), schema='JSON Schema Draft 2020-12 + frozen-case semantic validation',
            onnx_max_absolute_difference=max(differences), negative_checks=list(mutations),
            sequence_sha256=sha(DATA), schema_sha256=sha(SCHEMA), builder_sha256=sha(__file__),
            environment={p: importlib.metadata.version(p) for p in ['numpy', 'jsonschema', 'astropy', 'onnxruntime']}))
    print(json.dumps(dict(status='passed', mode='check' if args.check else 'build', states=5, events=6,
                         hashes=len(data['artifacts']), onnx_max_absolute_difference=max(differences), negative_checks=len(mutations))))


if __name__ == '__main__':
    main()
