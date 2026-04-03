import { useState, useEffect } from 'react';
import { FlaskConical, Loader2, ChevronDown, ChevronUp, ExternalLink, CheckCircle2 } from 'lucide-react';
import { getExperiments, getExperimentMetadata } from '@/lib/api';
import type { ExperimentEntry } from '@/lib/types';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('es-MX', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  });
}

function maeColor(mae: number): string {
  if (mae < 0.16) return 'text-green-400';
  if (mae < 0.22) return 'text-yellow-400';
  return 'text-red-400';
}

// ---------------------------------------------------------------------------
// Metadata modal
// ---------------------------------------------------------------------------

interface MetadataModalProps {
  filename: string;
  onClose: () => void;
}

function MetadataModal({ filename, onClose }: MetadataModalProps) {
  const [data, setData] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getExperimentMetadata(filename)
      .then((raw) => setData(JSON.stringify(raw, null, 2)))
      .catch((err) => setError(err.message));
  }, [filename]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-neutral-900 border border-neutral-700 w-full max-w-2xl max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800 bg-neutral-950">
          <div className="flex items-center gap-2">
            <ExternalLink className="w-3.5 h-3.5 text-neutral-400" />
            <span className="text-xs font-mono text-white">{filename}</span>
          </div>
          <button
            onClick={onClose}
            className="text-neutral-500 hover:text-white text-xs transition-colors"
          >
            ✕ cerrar
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {error ? (
            <p className="text-xs text-red-400">{error}</p>
          ) : data === null ? (
            <div className="flex items-center gap-2 text-neutral-500 text-xs">
              <Loader2 className="w-4 h-4 animate-spin" />
              Cargando metadatos…
            </div>
          ) : (
            <pre className="text-[11px] font-mono text-neutral-300 whitespace-pre-wrap leading-relaxed">
              {data}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Expanded detail row
// ---------------------------------------------------------------------------

function ExperimentDetail({ exp }: { exp: ExperimentEntry }) {
  const hp = exp.hyperparameters;
  const ds = exp.dataset;
  const env = exp.environment;

  return (
    <div className="grid grid-cols-3 gap-4 px-4 pb-4 pt-1 text-[11px]">
      {/* Hyperparameters */}
      <div className="space-y-1.5">
        <div className="text-[10px] text-neutral-500 uppercase tracking-widest mb-2">Hiperparámetros</div>
        {[
          ['Optimizer', hp.optimizer],
          ['Scheduler', hp.scheduler],
          ['Batch Size', String(hp.batch_size)],
          ['Max Epochs', String(hp.max_epochs)],
          ['Early Stop', `patience=${hp.early_stopping_patience}`],
          ['Epochs run', String(hp.epochs_run)],
        ].map(([k, v]) => (
          <div key={k} className="flex justify-between gap-2">
            <span className="text-neutral-500">{k}</span>
            <span className="font-mono text-neutral-300 text-right truncate max-w-[140px]" title={v}>{v}</span>
          </div>
        ))}
      </div>

      {/* Dataset */}
      <div className="space-y-1.5">
        <div className="text-[10px] text-neutral-500 uppercase tracking-widest mb-2">Dataset</div>
        {[
          ['Total', String(ds.total_samples)],
          ['Train', String(ds.train_samples)],
          ['Val', String(ds.val_samples)],
          ['Augmentation', ds.augmentation ? 'Sí' : 'No'],
          ['Device', env.device.toUpperCase()],
          ['Framework', env.framework],
        ].map(([k, v]) => (
          <div key={k} className="flex justify-between gap-2">
            <span className="text-neutral-500">{k}</span>
            <span className="font-mono text-neutral-300">{v}</span>
          </div>
        ))}
      </div>

      {/* Notes */}
      <div>
        <div className="text-[10px] text-neutral-500 uppercase tracking-widest mb-2">Notas</div>
        <p className="text-neutral-400 leading-relaxed">{exp.notes}</p>
        <div className="mt-3 space-y-1">
          <div className="flex justify-between">
            <span className="text-neutral-500">Best epoch</span>
            <span className="font-mono text-neutral-300">{exp.metrics.best_epoch}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-neutral-500">Best val loss</span>
            <span className="font-mono text-neutral-300">{exp.metrics.best_val_loss.toFixed(4)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-neutral-500">Weights</span>
            <span className="font-mono text-neutral-300 truncate max-w-[130px]" title={exp.weights_file}>
              {exp.weights_file}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ExperimentLog() {
  const [experiments, setExperiments] = useState<ExperimentEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [modalFile, setModalFile] = useState<string | null>(null);

  useEffect(() => {
    getExperiments()
      .then(setExperiments)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const toggle = (id: string) => setExpanded((prev) => (prev === id ? null : id));

  // Best run by MAE
  const bestRunId = experiments.length
    ? experiments.reduce((best, e) =>
        e.metrics.final_mae < best.metrics.final_mae ? e : best
      ).run_id
    : null;

  return (
    <>
      {modalFile && (
        <MetadataModal filename={modalFile} onClose={() => setModalFile(null)} />
      )}

      <div className="bg-neutral-950 border border-neutral-800">
        {/* Header */}
        <div className="border-b border-neutral-800 px-4 py-2.5 bg-neutral-900">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FlaskConical className="w-4 h-4 text-neutral-400" />
              <div>
                <h3 className="text-sm font-semibold text-white">Registro de Experimentos</h3>
                <p className="text-[11px] text-neutral-500 mt-0.5">
                  Ciclo de vida reproducible · Metadatos completos por corrida
                </p>
              </div>
            </div>
            {!loading && !error && (
              <span className="text-[10px] font-mono text-neutral-500 border border-neutral-700 px-2 py-0.5">
                {experiments.length} corrida{experiments.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>

        {/* Table header */}
        {!loading && !error && experiments.length > 0 && (
          <div className="grid grid-cols-[1fr_90px_90px_70px_80px_36px] gap-x-3 px-4 py-1.5 border-b border-neutral-800 bg-neutral-900/50">
            {['Corrida', 'LR', 'Dropout', 'Seed', 'MAE final', ''].map((h) => (
              <div key={h} className="text-[10px] text-neutral-500 uppercase tracking-widest font-medium">
                {h}
              </div>
            ))}
          </div>
        )}

        {/* Body */}
        <div>
          {loading ? (
            <div className="flex items-center gap-2 px-4 py-6 text-neutral-500 text-xs">
              <Loader2 className="w-4 h-4 animate-spin" />
              Cargando experimentos…
            </div>
          ) : error ? (
            <div className="px-4 py-4 text-xs text-red-400 bg-red-950 border-t border-red-900">
              {error}
            </div>
          ) : experiments.length === 0 ? (
            <div className="px-4 py-6 text-xs text-neutral-600">
              No se encontraron archivos de experimento en experiments/.
            </div>
          ) : (
            experiments.map((exp) => {
              const isExpanded = expanded === exp.run_id;
              const isBest = exp.run_id === bestRunId;

              return (
                <div
                  key={exp.run_id}
                  className={`border-b border-neutral-800 last:border-b-0 ${isBest ? 'bg-green-950/10' : ''}`}
                >
                  {/* Main row */}
                  <div
                    className="grid grid-cols-[1fr_90px_90px_70px_80px_36px] gap-x-3 px-4 py-3 items-center cursor-pointer hover:bg-white/[0.02] transition-colors"
                    onClick={() => toggle(exp.run_id)}
                  >
                    {/* Run name */}
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        {isBest && (
                          <CheckCircle2 className="w-3 h-3 text-green-500 flex-shrink-0" />
                        )}
                        <span className="text-xs text-white font-medium truncate">
                          {exp.run_name}
                        </span>
                      </div>
                      <span className="text-[10px] text-neutral-500 font-mono mt-0.5 block">
                        {formatDate(exp.date)} · {exp.run_id}
                      </span>
                    </div>

                    {/* LR */}
                    <div className="font-mono text-xs text-neutral-300">
                      {exp.hyperparameters.learning_rate}
                    </div>

                    {/* Dropout */}
                    <div className="font-mono text-xs text-neutral-300">
                      {exp.hyperparameters.dropout_rate}
                    </div>

                    {/* Seed */}
                    <div className="font-mono text-xs text-neutral-300">
                      {exp.hyperparameters.seed}
                    </div>

                    {/* MAE */}
                    <div className={`font-mono text-xs font-bold ${maeColor(exp.metrics.final_mae)}`}>
                      {exp.metrics.final_mae.toFixed(4)}
                    </div>

                    {/* Expand toggle */}
                    <div className="flex items-center justify-center">
                      {isExpanded
                        ? <ChevronUp className="w-3.5 h-3.5 text-neutral-500" />
                        : <ChevronDown className="w-3.5 h-3.5 text-neutral-500" />}
                    </div>
                  </div>

                  {/* Expanded detail */}
                  {isExpanded && (
                    <div className="border-t border-neutral-800 bg-neutral-900/30">
                      <ExperimentDetail exp={exp} />

                      {/* Metadata button */}
                      <div className="px-4 pb-4">
                        <button
                          onClick={() => setModalFile(exp.metadata_file)}
                          className="flex items-center gap-1.5 text-[11px] text-blue-400 hover:text-blue-300 border border-blue-500/30 bg-blue-500/5 hover:bg-blue-500/10 px-3 py-1.5 transition-colors"
                        >
                          <ExternalLink className="w-3 h-3" />
                          Ver metadatos completos ({exp.metadata_file})
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        {!loading && !error && experiments.length > 0 && (
          <div className="border-t border-neutral-800 px-4 py-2 bg-neutral-900/30 flex items-center gap-4 text-[10px] text-neutral-500">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3 h-3 text-green-500" />
              Mejor corrida destacada
            </div>
            <span className="text-neutral-700">·</span>
            <span>Haz clic en una fila para ver detalles</span>
            <span className="text-neutral-700">·</span>
            <span className="text-green-400">MAE &lt; 0.16</span>
            <span className="text-yellow-400">MAE &lt; 0.22</span>
            <span className="text-red-400">MAE ≥ 0.22</span>
          </div>
        )}
      </div>
    </>
  );
}
