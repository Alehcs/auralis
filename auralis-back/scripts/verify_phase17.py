"""Verify final/repeated Phase 1.7 artifacts and preserve the pre-audit inventory.

python scripts/verify_phase17.py --report-dir <run> --repeat-dir <repeat> --output <new.json>
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'auralis-back/reports/phase17_coronium_v3_1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classification(name):
    if '/sources/' in name or '/epochs/' in name or '/phase16_coronium_v3_1/' in name or '/phase1_v1/' in name:
        return 'válido y reutilizable', 'Proveniencia/evidencia congelada; se conserva, no es por sí sola evidencia de generalización.'
    if name.endswith(('plot_final_scatter.py', 'plot_r2_diagnostic.py', 'plot_architecture_diagram.py', 'plot_gradcam_overlay.py', 'src/visualization/app.py', 'RESEARCH_DOSSIER_MASTER.md')):
        return 'incorrecto/desactualizado', 'Contenía etiquetas de versión, log-SI/SSN, hold-out o cifras sin respaldo vigente; corregido o señalado como archivo histórico.'
    if name.endswith(('evaluate_final.py', 'run_external_baselines.py', 'train_model.py', 'learning_curve.png')):
        return 'necesita adaptación a V3.1', 'Cálculo/datos reutilizados; salida de publicación adaptada. Entrenador congelado por el manifiesto de promoción.'
    if '/experiments/exp_' in name or name.endswith('results_benchmarking.json') or name.endswith('reports/results_comparison.csv'):
        return 'necesita adaptación a V3.1', 'Histórico: distinto split/protocolo, posibles etiquetas antiguas. Conservado sin reemplazar ni usar como comparación controlada.'
    if '/reports/figures/' in name or name.endswith(('final_coronium_scatter_tesis.png', 'r2_diagnostic.png')):
        return 'necesita adaptación a V3.1', 'Imagen histórica preservada. No es figura de resultados V3.1; usar el catálogo Phase 1.7.'
    if name.endswith(('architecture-comparison.tsx', 'xai-faithfulness.tsx', 'experiment-log.tsx', 'model-metrics.tsx')):
        return 'incorrecto/desactualizado', 'Se corrigieron comparación sin control, unidades, afirmaciones XAI, estado inferido o rango temporal hardcodeado.'
    if name.endswith(('global-metrics.tsx', 'predicted-vs-actual.tsx', 'api/main.py', 'lib/api.ts', 'lib/types.ts')):
        return 'necesita adaptación a V3.1', 'Se reutiliza el contrato y se añade separación explícita MC/determinista, unidades y metadatos; compatibilidad conservada.'
    if name.endswith('kfold-results.tsx'):
        return 'válido y reutilizable', 'Únicamente como ilustración ya rotulada; no son resultados científicos ni se incorporan al reporte V3.1.'
    if name.endswith(('best_coronium_v3_pro_augmented.pth', 'best_coronium_v3_pro.onnx', 'best_coronium_v3_pro.onnx.data', 'target_scaler.json', 'split_indices.json')):
        return 'válido y reutilizable', 'Archivo histórico preservado para diagnóstico; excluido de métricas vigentes.'
    if 'evaluation_clean_repeat_v1' in name:
        return 'válido y reutilizable', 'Repetición deliberada para reproducibilidad; no redundancia eliminable.'
    return 'válido y reutilizable', 'Fuente/infraestructura conservada; interpretar con el alcance y protocolo documentados en el inventario narrativo.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir', type=Path, required=True)
    parser.add_argument('--repeat-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    before = json.loads((BASE / 'audit_before.json').read_text())
    preserved, protected, changed, inventory = [], [], [], []
    for name, old_hash in before.items():
        path = ROOT / name
        assert path.exists(), f'Pre-existing file removed: {name}'
        new_hash = digest(path)
        frozen = name.startswith(('auralis-back/experiments/', 'auralis-back/models/', 'auralis-back/reports/'))
        is_protected = any(token in name.lower() for token in ('unity', 'webar', 'timeline', '/simulation/', 'digital-twin', 'agent-lab', 'src/agents/', 'agent_routes'))
        if frozen or is_protected:
            assert new_hash == old_hash, f'Protected/frozen file modified: {name}'
        if frozen: preserved.append(name)
        if is_protected: protected.append(name)
        if new_hash != old_hash: changed.append(name)
        if not is_protected:
            status, reason = classification(name)
            inventory.append({'path': name, 'classification_before': status, 'reason_and_action': reason,
                              'sha256_before': old_hash, 'sha256_after': new_hash, 'changed': old_hash != new_hash})
    missing = [
        ('Métricas/CSV por banda y casos extremos de V3.1', 'metrics_by_activity.csv y worst_cases.csv'),
        ('Residuos vs target/predicción y errores absolutos de ambos protocolos', 'figuras 02–05'),
        ('Comparación pareada MC/determinista con sesgo y percentiles', 'metrics.json y figura 07'),
        ('Baseline de media de train en split limpio', 'train_mean_si y figura 08'),
        ('Latencia V3.1 reproducible con tiempos crudos', 'latency.json, latency_samples.csv y figura 11'),
        ('Catálogo de publicación versionado PNG/PDF/SVG', 'figure_catalog.json, report.md, manifest.json'),
        ('Errores por año del registro TAI', 'metrics_by_record_year.csv y figura 10')]
    inventory += [{'path': name, 'classification_before': 'faltante', 'reason_and_action': action, 'changed': True} for name, action in missing]
    inventory += [{'path': 'Scatter repetido en antiguos gráficos final/R2', 'classification_before': 'redundante',
                   'reason_and_action': 'Helper draw_scatter reutilizado; diagnóstico de residuos separado. Scripts e imágenes históricos preservados.', 'changed': True}]
    manifests = []
    for folder in (args.report_dir, args.repeat_dir):
        manifest = json.loads((folder / 'manifest.json').read_text())
        assert manifest['status'] == 'completed' and manifest['model_version'] == '3.1'
        for name, expected in manifest['outputs_sha256'].items():
            assert digest(folder / name) == expected, name
        for name, expected in manifest['sources_sha256'].items():
            assert digest(ROOT / 'auralis-back' / name) == expected, name
        manifests.append(manifest)
    repeat_files = ['metrics.json', 'metrics.csv', 'predictions.csv', 'metrics_by_activity.csv',
                    'worst_cases.csv', 'training_history.csv', 'metrics_by_record_year.csv',
                    'historical_protocol_comparison.csv', 'latency.json', 'latency_samples.csv']
    for name in repeat_files:
        assert digest(args.report_dir / name) == digest(args.repeat_dir / name), name
    png_equal = {str(p.relative_to(args.report_dir)): digest(p) == digest(args.repeat_dir / p.relative_to(args.report_dir))
                 for p in sorted((args.report_dir / 'figures').glob('*.png'))}
    assert all(png_equal.values()), 'PNG reproduction differs'
    results = {'status': 'verified', 'final_report': str(args.report_dir.resolve()),
               'repeat_report': str(args.repeat_dir.resolve()), 'repeated_data_files_byte_identical': repeat_files,
               'png_byte_identical': png_equal, 'frozen_artifacts_unchanged': len(preserved),
               'protected_files_unchanged': len(protected), 'preexisting_files_removed': 0,
               'modified_files_this_phase': changed, 'inventory_counts': dict(Counter(x['classification_before'] for x in inventory))}
    with args.output.open('x') as stream:
        json.dump(results, stream, indent=2, ensure_ascii=False); stream.write('\n')
    with (args.output.parent / 'inventory.json').open('x') as stream:
        json.dump(inventory, stream, indent=2, ensure_ascii=False); stream.write('\n')
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
