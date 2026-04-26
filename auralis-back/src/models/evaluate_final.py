"""Evaluación definitiva de Coronium V3 PRO para tesis.

Carga el checkpoint final (models/coronium_v3_pro.pth), ejecuta inferencia sobre
el conjunto de validación (último 20 % del dataset, sin augmentación), y genera:

    1. Reporte de métricas de tesis en consola:
         MAE, RMSE, R² (coeficiente de determinación), MAPE

    2. CSV de comparación (reports/results_comparison.csv):
         Real_SSN | Predicted_SSN | Error_Absoluto

NOTA SOBRE UNIDADES:
    El target que Coronium aprende es el índice proxy de manchas solares
    normalizado via Z-Score (prepare_dataset.normalize_sunspot_targets).
    Los parámetros del escalador se leen de models/target_scaler.json y se
    usan para aplicar la transformada inversa antes de calcular métricas:

        y_real_norm, y_pred_norm  →  × std + mean  →  escala original (% área activa)

    Todas las métricas y el CSV resultante están en la escala real del índice
    proxy (porcentaje de píxeles con |B| > 200 G).

Uso (desde la raíz del repo auralis-back/):
    python src/models/evaluate_final.py
"""

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Subset
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Asegura que train_model.py sea importable sin instalación del paquete.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_model import SolarDataset, CoroniumV3  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración de rutas  (relativas al directorio auralis-back/)
# ---------------------------------------------------------------------------
WEIGHTS_PATH  = Path("models/coronium_v3_pro.pth")
SCALER_PATH   = Path("models/target_scaler.json")
DATA_DIR      = Path("data/processed")
METADATA_CSV  = Path("data/processed/metadata_processed.csv")
REPORT_CSV    = Path("reports/results_comparison.csv")

# Debe coincidir exactamente con lo usado en train_model.main()
VAL_SPLIT    = 0.2
BATCH_SIZE   = 32
DROPOUT_RATE = 0.2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_device() -> torch.device:
    """Selecciona el backend de cómputo disponible (CUDA > MPS > CPU)."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info("Backend: CUDA — %s", torch.cuda.get_device_name(0))
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("Backend: MPS (Apple Silicon)")
    else:
        device = torch.device("cpu")
        logger.info("Backend: CPU")
    return device


def load_scaler(scaler_path: Path) -> tuple[float, float]:
    """Lee mean y std del escalador Z-Score guardado por prepare_dataset.

    Args:
        scaler_path: Ruta a models/target_scaler.json.

    Returns:
        Tupla (mean, std) como floats.

    Raises:
        FileNotFoundError: Si el archivo no existe — indica que el pipeline
            de datos no ha sido ejecutado con normalización activada.
    """
    if not scaler_path.exists():
        raise FileNotFoundError(
            f"Escalador no encontrado: {scaler_path}\n"
            "Ejecuta prepare_dataset.py con normalize_sunspot_targets() "
            "para generar este archivo antes de evaluar."
        )
    with open(scaler_path) as f:
        data = json.load(f)
    mean: float = float(data["mean"])
    std: float  = float(data["std"])
    logger.info("Escalador cargado — mean=%.4f  std=%.4f", mean, std)
    return mean, std


def build_val_loader() -> DataLoader:
    """Reconstruye el split de validación idéntico al usado en entrenamiento.

    Usa la misma fracción determinista (últimos VAL_SPLIT del dataset) y sin
    augmentación, replicando la lógica de train_model.main().
    """
    full_dataset = SolarDataset(
        data_dir=str(DATA_DIR),
        metadata_csv=str(METADATA_CSV),
        transform=None,
    )
    total   = len(full_dataset)
    val_n   = int(total * VAL_SPLIT)
    train_n = total - val_n

    val_indices = list(range(train_n, total))
    val_subset  = Subset(full_dataset, val_indices)
    logger.info("Split validación: %d muestras de %d totales", len(val_subset), total)

    return DataLoader(val_subset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)


def run_inference(
    model: torch.nn.Module,
    loader: DataLoader,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    """Ejecuta inferencia determinista (sin MC Dropout) sobre todo el loader.

    Returns:
        y_real (N,): valores reales del índice proxy.
        y_pred (N,): predicciones del modelo.
    """
    model.eval()
    y_real_list, y_pred_list = [], []

    with torch.no_grad():
        for images, targets in tqdm(loader, desc="Inferencia", unit="batch"):
            images = images.to(device)
            outputs = model(images)                         # (B, 1)
            y_pred_list.extend(outputs.squeeze(1).cpu().numpy())
            y_real_list.extend(targets.squeeze(1).numpy())

    return np.array(y_real_list), np.array(y_pred_list)


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------

def compute_metrics(y_real: np.ndarray, y_pred: np.ndarray) -> dict:
    """Calcula MAE, RMSE, R² y MAPE.

    MAPE excluye muestras donde y_real == 0 para evitar división por cero
    (frecuente en días de sol quieto con índice proxy ≈ 0 %).

    Args:
        y_real: Valores reales, shape (N,).
        y_pred: Predicciones alineadas con y_real, shape (N,).

    Returns:
        Diccionario con claves mae, rmse, r2, mape.
    """
    residuals = y_pred - y_real

    mae  = float(np.mean(np.abs(residuals)))
    rmse = float(np.sqrt(np.mean(residuals ** 2)))

    # R² = 1 - SS_res / SS_tot
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y_real - y_real.mean()) ** 2))
    r2     = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else float("nan")

    # MAPE sólo sobre muestras con actividad real > 0
    nonzero_mask = y_real != 0.0
    if nonzero_mask.sum() > 0:
        mape = float(np.mean(np.abs(residuals[nonzero_mask] / y_real[nonzero_mask])) * 100)
    else:
        mape = float("nan")

    return {"mae": mae, "rmse": rmse, "r2": r2, "mape": mape}


def print_thesis_report(metrics: dict, n_samples: int, mean: float, std: float) -> None:
    """Imprime el reporte de métricas con formato para tesis."""
    sep = "=" * 62
    print(f"\n{sep}")
    print("  Coronium V3 PRO — Reporte de Evaluación Definitiva")
    print(sep)
    print(f"  Muestras evaluadas : {n_samples:>8,}")
    print(f"  MAE                : {metrics['mae']:>10.4f}  [% área activa]")
    print(f"  RMSE               : {metrics['rmse']:>10.4f}  [% área activa]")
    print(f"  R²                 : {metrics['r2']:>10.4f}  [-]")
    print(f"  MAPE               : {metrics['mape']:>10.2f}  [%]  (excluye y=0)")
    print(sep)
    print("  Escala: índice proxy de área activa (% píxeles con |B| > 200 G)")
    print(f"  Transformada inversa Z-Score aplicada — μ={mean:.4f}  σ={std:.4f}")
    print(sep + "\n")


# ---------------------------------------------------------------------------
# Exportación CSV
# ---------------------------------------------------------------------------

def export_comparison_csv(
    y_real: np.ndarray,
    y_pred: np.ndarray,
    output_path: Path,
) -> None:
    """Guarda Real_SSN, Predicted_SSN y Error_Absoluto en un CSV.

    Args:
        y_real:      Valores reales del índice proxy.
        y_pred:      Predicciones del modelo.
        output_path: Ruta destino del CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame({
        "Real_SSN":       np.round(y_real, 6),
        "Predicted_SSN":  np.round(y_pred, 6),
        "Error_Absoluto": np.round(np.abs(y_pred - y_real), 6),
    })

    df.to_csv(output_path, index=False)
    logger.info("CSV exportado → %s  (%d filas)", output_path, len(df))


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def main() -> None:
    # ── Validar artefactos requeridos ─────────────────────────────────────────
    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"Checkpoint no encontrado: {WEIGHTS_PATH}\n"
            "Ejecuta train_model.py primero para generar los pesos."
        )

    # ── Cargar escalador Z-Score ──────────────────────────────────────────────
    mean, std = load_scaler(SCALER_PATH)

    device = get_device()

    # ── Cargar modelo ─────────────────────────────────────────────────────────
    model = CoroniumV3(in_channels=2, dropout_rate=DROPOUT_RATE)
    state = torch.load(WEIGHTS_PATH, map_location=device, weights_only=True)
    model.load_state_dict(state)
    model.to(device)
    logger.info("Pesos cargados desde %s", WEIGHTS_PATH)

    # ── Construir DataLoader de validación ────────────────────────────────────
    val_loader = build_val_loader()

    # ── Inferencia (espacio normalizado) ──────────────────────────────────────
    y_real_norm, y_pred_norm = run_inference(model, val_loader, device)

    # ── Transformada inversa Z-Score → escala real (solo predicciones) ───────
    # y_real_norm ya viene en escala física desde SolarDataset; no se toca.
    # Solo y_pred sale del modelo en espacio Z-Score y debe desnormalizarse.
    y_real = y_real_norm
    y_pred = (y_pred_norm * std) + mean

    # ── Métricas en escala real ───────────────────────────────────────────────
    metrics = compute_metrics(y_real, y_pred)
    print_thesis_report(metrics, n_samples=len(y_real), mean=mean, std=std)

    # ── Exportar CSV con valores reales ───────────────────────────────────────
    export_comparison_csv(y_real, y_pred, REPORT_CSV)


if __name__ == "__main__":
    main()
