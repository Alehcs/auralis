"""Interpretabilidad de CoroniumV3 PRO mediante Grad-CAM nativo en PyTorch.

Implementa Gradient-weighted Class Activation Mapping (Selvaraju et al., 2017)
sin dependencias externas de XAI (captum, pytorch-grad-cam), utilizando
únicamente los hooks de autograd de PyTorch. La implementación es
documentable directamente en tesis como derivación matemática propia.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Matemáticas de Grad-CAM para un regresor escalar
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sea A^k ∈ ℝ^{H×W}  la activación del k-ésimo canal de la última capa
convolucional (stage4, k=1…128, H=W=64).

Sea y ∈ ℝ  la predicción escalar del modelo (índice proxy normalizado).

(1) Pesos de importancia por canal — Global Average Pooling sobre gradientes:

        α_k = (1/Z) · Σ_{i,j}  ∂y/∂A^k_{ij}       Z = H · W

    Los gradientes ∂y/∂A^k son capturados por un backward_hook registrado
    sobre el módulo stage4. Esta ponderación refleja cuánto influye en
    promedio cada posición espacial del mapa k en la predicción final y.

(2) Mapa de calor Grad-CAM — combinación lineal ponderada + ReLU:

        L_GradCAM = ReLU( Σ_k  α_k · A^k )

    La ReLU elimina regiones con contribución negativa a y (regiones que
    suprimen la predicción de actividad solar), reteniendo sólo las zonas
    que elevan el índice proxy: típicamente regiones activas bipolares.

(3) Redimensionado bilineal desde (64, 64) hasta (512, 512) para alineación
    con el espacio de entrada original del magnetograma.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Capa objetivo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    model.stage4  →  V3ResidualBlock(96 → 128)
    Salida: (N, 128, 64, 64) — máxima riqueza semántica con resolución
    espacial antes del GlobalAvgPool que colapsa dimensiones espaciales.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Uso (desde la raíz auralis-back/):
    python src/models/explain_model.py

Salida:
    reports/figures/gradcam_sample.png
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ---------------------------------------------------------------------------
# Importación del modelo desde train_model.py (sin instalación del paquete)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_model import CoroniumV3  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rutas (relativas al directorio de trabajo auralis-back/)
# ---------------------------------------------------------------------------
WEIGHTS_PATH  = Path("models/best_coronium_v3_pro.pth")
DATA_DIR      = Path("data/processed")
OUTPUT_FIGURE = Path("reports/figures/gradcam_sample.png")

# Atributo de CoroniumV3 que corresponde a la última etapa convolucional.
# stage4 = V3ResidualBlock(64 → 96) — salida (N, 96, 64, 64) antes del pool4.
TARGET_LAYER_NAME = "stage4"

# Dropout rate idéntico al usado durante el entrenamiento del checkpoint (exp_004).
DROPOUT_RATE = 0.2


# ===========================================================================
# Sistema de Hooks — captura de activaciones y gradientes
# ===========================================================================

class GradCAMHookManager:
    """Gestor de hooks de PyTorch para la captura de activaciones y gradientes.

    Registra dos hooks sobre el módulo ``target_layer``:

    forward_hook:
        Invocado automáticamente al final del forward pass del módulo.
        Almacena la salida del módulo (activaciones A^k) en
        ``self.activations`` con shape (N, C, H, W).

    full_backward_hook:
        Invocado durante la fase de retropropagación al pasar el gradiente
        a través del módulo. ``grad_output[0]`` contiene ∂L/∂output del
        módulo, es decir, los gradientes ∂y/∂A^k necesarios para Grad-CAM.
        Se almacenan en ``self.gradients`` con shape (N, C, H, W).

    El uso de ``register_full_backward_hook`` (en lugar del deprecated
    ``register_backward_hook``) garantiza que el tensor completo de
    gradientes de salida esté disponible, incluso en presencia de in-place
    operations dentro del módulo (BN + ReLU en V3ResidualBlock).

    Args:
        model:      Instancia de CoroniumV3 inicializada y cargada.
        layer_name: Nombre del atributo de primer nivel de ``model`` que
                    corresponde a la capa objetivo (p.ej. ``"stage4"``).

    Raises:
        AttributeError: Si ``model`` no tiene el atributo ``layer_name``.
    """

    def __init__(self, model: nn.Module, layer_name: str) -> None:
        self.activations: Optional[torch.Tensor] = None
        self.gradients:   Optional[torch.Tensor] = None
        self._handles: list = []

        if not hasattr(model, layer_name):
            raise AttributeError(
                f"El modelo no tiene el atributo '{layer_name}'. "
                f"Atributos disponibles: {[n for n, _ in model.named_children()]}"
            )

        target_layer: nn.Module = getattr(model, layer_name)

        def _save_activations(
            module: nn.Module,
            inp: Tuple[torch.Tensor, ...],
            output: torch.Tensor,
        ) -> None:
            # Detach para no contaminar el grafo computacional con la copia.
            # Shape: (N, 128, 64, 64) para stage4 con entrada (N, 2, 512, 512)
            self.activations = output.detach().cpu()

        def _save_gradients(
            module: nn.Module,
            grad_input: Tuple[Optional[torch.Tensor], ...],
            grad_output: Tuple[torch.Tensor, ...],
        ) -> None:
            # grad_output[0]: gradiente respecto a la salida del módulo.
            # Shape: (N, 128, 64, 64) — idéntica a las activaciones.
            self.gradients = grad_output[0].detach().cpu()

        self._handles.append(
            target_layer.register_forward_hook(_save_activations)
        )
        self._handles.append(
            target_layer.register_full_backward_hook(_save_gradients)
        )
        logger.info(
            "Hooks registrados — capa objetivo: '%s' (%s)",
            layer_name,
            type(target_layer).__name__,
        )

    def remove(self) -> None:
        """Elimina ambos hooks del modelo para no interferir con inferencias posteriores."""
        for handle in self._handles:
            handle.remove()
        self._handles.clear()
        logger.info("Hooks eliminados del modelo.")


# ===========================================================================
# Cómputo de Grad-CAM
# ===========================================================================

def compute_gradcam(
    model: nn.Module,
    input_tensor: torch.Tensor,
    hook_manager: GradCAMHookManager,
    target_size: Tuple[int, int] = (512, 512),
) -> Tuple[np.ndarray, float]:
    """Calcula el mapa de calor Grad-CAM para la predicción de manchas solares.

    Implementación nativa de los pasos matemáticos de Grad-CAM:

        Paso 1 — Forward pass:
            y = f(x; θ)                              [escalar de predicción]

        Paso 2 — Backward pass:
            ∂y/∂A^k_{ij} capturado por full_backward_hook sobre stage4

        Paso 3 — Importancia por canal (GAP sobre gradientes):
            α_k = (1/Z) · Σ_{i,j} ∂y/∂A^k_{ij}     Z = H · W = 64² = 4096

        Paso 4 — Mapa de calor + ReLU:
            L_GC = ReLU( Σ_k α_k · A^k )

        Paso 5 — Redimensionado bilineal:
            L_GC: (64, 64) → (512, 512)

        Paso 6 — Normalización min-max a [0, 1]:
            L_GC_norm = (L_GC − min) / (max − min + ε)

    Args:
        model:        CoroniumV3 en modo evaluación (model.eval() activo).
                      Los parámetros deben tener requires_grad=True (por defecto
                      en PyTorch) para que el grafo de la retropropagación
                      se construya a través de los pesos del modelo.
        input_tensor: Tensor de entrada shape (1, 2, 512, 512), float32.
                      Se espera que el device del tensor coincida con el del modelo.
        hook_manager: GradCAMHookManager con hooks activos sobre el modelo.
        target_size:  Dimensiones finales (H, W) del mapa de calor. Por
                      defecto (512, 512) para alineación con la entrada.

    Returns:
        Tupla:
            - heatmap:    Array float32 normalizado a [0, 1], shape (H, W).
            - prediction: Valor escalar de la predicción (índice normalizado).

    Raises:
        RuntimeError: Si los hooks no capturaron datos (capa objetivo inválida).
    """
    model.eval()

    # ── Paso 1: Forward pass ──────────────────────────────────────────────────
    # El input_tensor no requiere grad; el grafo se construye desde los pesos.
    output = model(input_tensor)   # shape: (1, 1)
    prediction_scalar: float = output.item()
    logger.info(
        "Predicción del modelo: %.6f (índice proxy normalizado)", prediction_scalar
    )

    # ── Paso 2: Backward pass sobre la predicción escalar ─────────────────────
    # Para un regresor, se retropropaga directamente sobre y (sin one-hot).
    # Los hooks capturan ∂y/∂A^k en stage4 durante esta llamada.
    model.zero_grad()
    output.squeeze().backward()   # backward sobre el escalar y

    # ── Recuperar datos de los hooks ──────────────────────────────────────────
    activations: Optional[torch.Tensor] = hook_manager.activations   # (1, 128, 64, 64)
    gradients:   Optional[torch.Tensor] = hook_manager.gradients     # (1, 128, 64, 64)

    if activations is None or gradients is None:
        raise RuntimeError(
            "Los hooks no capturaron datos tras el backward pass. "
            f"Verifica que TARGET_LAYER_NAME='{TARGET_LAYER_NAME}' sea un "
            "atributo válido de CoroniumV3 con salida tensorial."
        )

    logger.info(
        "Activaciones capturadas — shape: %s | Gradientes — shape: %s",
        tuple(activations.shape),
        tuple(gradients.shape),
    )

    # ── Paso 3: Importancia por canal via GAP sobre los gradientes ────────────
    # α_k = mean_{i,j}(∂y/∂A^k_{ij})   →   shape: (1, 128, 1, 1)
    alpha_k: torch.Tensor = gradients.mean(dim=(2, 3), keepdim=True)

    # ── Paso 4: Combinación lineal ponderada y ReLU ───────────────────────────
    # Σ_k α_k · A^k → shape: (1, 128, 64, 64)
    # .sum(dim=1, keepdim=True) → (1, 1, 64, 64)  [colapsa la dimensión de canales]
    weighted_sum: torch.Tensor = (alpha_k * activations).sum(dim=1, keepdim=True)
    cam: torch.Tensor = F.relu(weighted_sum)   # ReLU: sólo regiones que elevan y

    # ── Paso 5: Redimensionado bilineal hasta target_size ────────────────────
    cam_resized: torch.Tensor = F.interpolate(
        cam,
        size=target_size,
        mode="bilinear",
        align_corners=False,
    )  # (1, 1, 512, 512)

    cam_np: np.ndarray = cam_resized.squeeze().numpy()   # (512, 512)

    # ── Paso 6: Normalización min-max a [0, 1] ───────────────────────────────
    cam_min = float(cam_np.min())
    cam_max = float(cam_np.max())
    if cam_max - cam_min > 1e-8:
        cam_np = (cam_np - cam_min) / (cam_max - cam_min)
    else:
        cam_np = np.zeros_like(cam_np)
        logger.warning(
            "Mapa Grad-CAM constante (max ≈ min). "
            "La muestra puede corresponder a sol quieto (índice ≈ 0) o "
            "el checkpoint no ha convergido suficientemente."
        )

    logger.info(
        "Mapa Grad-CAM calculado — activaciones: %s → redimensionado a %s",
        tuple(activations.shape[2:]),
        target_size,
    )
    return cam_np.astype(np.float32), prediction_scalar


# ===========================================================================
# Carga de muestra
# ===========================================================================

def load_sample(data_dir: Path) -> Tuple[torch.Tensor, np.ndarray, str]:
    """Carga la primera muestra *_processed.npy disponible en data_dir.

    Gestiona tanto el formato V3 PRO (2, H, W) como el formato V2 (H, W)
    mediante la misma lógica de separación B+/B- que emplea SolarDataset.
    El primer archivo en orden lexicográfico se selecciona como muestra
    representativa para la explicabilidad.

    Args:
        data_dir: Directorio que contiene archivos *_processed.npy.

    Returns:
        Tupla:
            - input_tensor: shape (1, 2, H, W), float32, listo para el modelo.
            - raw_channels: shape (2, H, W) — canal 0 = B+, canal 1 = B−.
            - sample_name:  Stem del archivo (sin extensión) para el título.

    Raises:
        FileNotFoundError: Si data_dir no contiene archivos *_processed.npy.
    """
    npy_files = sorted(data_dir.glob("*_processed.npy"))
    if not npy_files:
        raise FileNotFoundError(
            f"No se encontraron archivos *_processed.npy en: {data_dir}\n"
            "Ejecuta prepare_dataset.py para generar los datos procesados."
        )

    sample_path = npy_files[0]
    image: np.ndarray = np.load(str(sample_path))
    logger.info(
        "Muestra seleccionada: %s  |  shape original: %s  |  dtype: %s",
        sample_path.name,
        image.shape,
        image.dtype,
    )

    # V2-compatibility: array (H, W) con normalización sign-preserving → (2, H, W)
    if image.ndim == 2:
        b_pos = np.maximum(0.0, image)
        b_neg = np.maximum(0.0, -image)
        image = np.stack([b_pos, b_neg], axis=0).astype(np.float32)
        logger.info(
            "Formato V2 detectado — separación B+/B- aplicada → shape: %s",
            image.shape,
        )

    # input_tensor: añade dimensión de batch → (1, 2, H, W)
    input_tensor = torch.from_numpy(image).float().unsqueeze(0)

    return input_tensor, image, sample_path.stem


# ===========================================================================
# Visualización científica
# ===========================================================================

def plot_gradcam(
    raw_channels: np.ndarray,
    heatmap: np.ndarray,
    prediction: float,
    sample_name: str,
    output_path: Path,
) -> None:
    """Genera figura de tres subplots para tesis: B+, B−, Grad-CAM sobre |B|.

    Diseño del panel:

        ┌─────────────────┬─────────────────┬──────────────────────────────┐
        │  Magnetograma   │  Magnetograma   │  Grad-CAM superpuesto        │
        │  B+ (cmap=hot)  │  B− (cmap=cool) │  sobre |B| (cmap=jet + gray) │
        └─────────────────┴─────────────────┴──────────────────────────────┘

    La magnitud combinada |B| = B+ + B− en el subplot derecho preserva la
    escala física del campo magnético total, permitiendo verificar visualmente
    que el modelo focaliza en regiones de alta actividad (manchas bipolares,
    regiones activas de clase β o βγδ en la clasificación de Mount Wilson).

    La superposición del mapa Grad-CAM con alpha=0.55 sobre el fondo gris
    de |B| garantiza que las estructuras magnéticas subyacentes sigan siendo
    legibles, lo cual es un requisito estándar de visualización en XAI
    aplicada a datos de teledetección solar.

    Args:
        raw_channels: Array shape (2, H, W) — canal 0 = B+, canal 1 = B−.
        heatmap:      Array shape (H, W), float32 en [0, 1] — mapa Grad-CAM.
        prediction:   Valor escalar de la predicción (índice normalizado).
        sample_name:  Nombre de la muestra para el supertítulo de la figura.
        output_path:  Ruta de destino del archivo .png.
    """
    b_pos: np.ndarray = raw_channels[0]          # (H, W) — polaridad positiva
    b_neg: np.ndarray = raw_channels[1]          # (H, W) — polaridad negativa
    b_mag: np.ndarray = b_pos + b_neg            # (H, W) — magnitud total |B|

    # Normalización de |B| a [0, 1] para fondo de contraste del subplot Grad-CAM
    b_mag_norm: np.ndarray = b_mag / (b_mag.max() + 1e-8)

    DARK_BG = "#0d0d0d"

    fig = plt.figure(figsize=(19, 6.5), facecolor=DARK_BG)
    fig.suptitle(
        f"Grad-CAM  ·  Coronium V3 PRO\n"
        f"Muestra: {sample_name}     "
        f"Predicción (índice proxy norm.): {prediction:+.5f}",
        fontsize=12,
        color="white",
        fontweight="bold",
        y=1.03,
    )

    gs = gridspec.GridSpec(
        1, 3, figure=fig, wspace=0.10, left=0.04, right=0.97
    )

    # ── Subplot 1: Magnetograma B+ ────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0])
    im1 = ax1.imshow(
        b_pos,
        cmap="hot",
        origin="lower",
        aspect="equal",
        interpolation="nearest",
    )
    ax1.set_title(
        "Magnetograma  B+\n(Lóbulo de Polaridad Positiva)",
        color="white",
        fontsize=10,
        pad=7,
    )
    ax1.set_xlabel("Píxel X  [HMI Level-1.5]", color="#aaaaaa", fontsize=8)
    ax1.set_ylabel("Píxel Y  [HMI Level-1.5]", color="#aaaaaa", fontsize=8)
    ax1.tick_params(colors="#aaaaaa", labelsize=7)
    for spine in ax1.spines.values():
        spine.set_edgecolor("#444444")
    ax1.set_facecolor(DARK_BG)
    cbar1 = fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.set_label("Flujo B+  [u.a. log-norm.]", color="#aaaaaa", fontsize=7)
    cbar1.ax.yaxis.set_tick_params(color="#aaaaaa", labelsize=7)
    plt.setp(cbar1.ax.yaxis.get_ticklabels(), color="#aaaaaa")

    # ── Subplot 2: Magnetograma B− ────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[1])
    im2 = ax2.imshow(
        b_neg,
        cmap="cool",
        origin="lower",
        aspect="equal",
        interpolation="nearest",
    )
    ax2.set_title(
        "Magnetograma  B−\n(Lóbulo de Polaridad Negativa)",
        color="white",
        fontsize=10,
        pad=7,
    )
    ax2.set_xlabel("Píxel X  [HMI Level-1.5]", color="#aaaaaa", fontsize=8)
    ax2.tick_params(colors="#aaaaaa", labelsize=7)
    for spine in ax2.spines.values():
        spine.set_edgecolor("#444444")
    ax2.set_facecolor(DARK_BG)
    cbar2 = fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label("Flujo B−  [u.a. log-norm.]", color="#aaaaaa", fontsize=7)
    cbar2.ax.yaxis.set_tick_params(color="#aaaaaa", labelsize=7)
    plt.setp(cbar2.ax.yaxis.get_ticklabels(), color="#aaaaaa")

    # ── Subplot 3: Grad-CAM superpuesto sobre |B| ─────────────────────────────
    ax3 = fig.add_subplot(gs[2])

    # Capa base: magnitud total del campo magnético en escala de grises
    ax3.imshow(
        b_mag_norm,
        cmap="gray",
        origin="lower",
        aspect="equal",
        interpolation="nearest",
        alpha=1.0,
    )

    # Superposición: mapa de calor Grad-CAM con colormap jet y transparencia
    im3 = ax3.imshow(
        heatmap,
        cmap="jet",
        origin="lower",
        aspect="equal",
        interpolation="bilinear",
        alpha=0.55,
        vmin=0.0,
        vmax=1.0,
    )
    ax3.set_title(
        "Grad-CAM  sobre  |B| = B+ + B−\n"
        "(Regiones relevantes para la predicción del modelo)",
        color="white",
        fontsize=10,
        pad=7,
    )
    ax3.set_xlabel("Píxel X  [HMI Level-1.5]", color="#aaaaaa", fontsize=8)
    ax3.tick_params(colors="#aaaaaa", labelsize=7)
    for spine in ax3.spines.values():
        spine.set_edgecolor("#444444")
    ax3.set_facecolor(DARK_BG)
    cbar3 = fig.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)
    cbar3.set_label(
        "Importancia Grad-CAM  [0 = irrelevante · 1 = máxima activación]",
        color="#aaaaaa",
        fontsize=7,
    )
    cbar3.ax.yaxis.set_tick_params(color="#aaaaaa", labelsize=7)
    plt.setp(cbar3.ax.yaxis.get_ticklabels(), color="#aaaaaa")

    # Anotación metodológica en el subplot Grad-CAM
    ax3.text(
        0.01, 0.01,
        "L_GC = ReLU(Σ_k α_k · A^k)   |   α_k = GAP(∂y/∂A^k)",
        transform=ax3.transAxes,
        fontsize=6.5,
        color="#888888",
        verticalalignment="bottom",
        fontfamily="monospace",
    )

    fig.patch.set_facecolor(DARK_BG)

    # ── Guardado ──────────────────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(
        str(output_path),
        dpi=200,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    logger.info("Figura Grad-CAM guardada: %s", output_path)


# ===========================================================================
# Selección del backend de cómputo
# ===========================================================================

def get_device() -> torch.device:
    """Selecciona el backend de cómputo disponible: CUDA > MPS > CPU.

    Nota sobre MPS (Apple Silicon):
        register_full_backward_hook funciona correctamente en PyTorch >= 2.0
        con backend MPS. Si se produce un error de gradiente, establece
        PYTORCH_ENABLE_MPS_FALLBACK=1 en el entorno antes de ejecutar.
    """
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


# ===========================================================================
# Punto de entrada
# ===========================================================================

def main() -> None:
    """Pipeline completo de explicabilidad Grad-CAM para CoroniumV3 PRO.

    Secuencia de ejecución:
        1. Validar artefactos requeridos (checkpoint, directorio de datos).
        2. Cargar modelo en modo evaluación con gradientes habilitados.
        3. Cargar una muestra procesada de data/processed/.
        4. Registrar forward_hook y full_backward_hook sobre stage4.
        5. Ejecutar forward + backward para capturar activaciones y gradientes.
        6. Calcular el mapa Grad-CAM (pasos 3–6 de la derivación matemática).
        7. Generar figura científica de tres paneles y guardarla.
        8. Eliminar hooks para dejar el modelo en estado limpio.
    """
    # ── 1. Validar artefactos ─────────────────────────────────────────────────
    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(
            f"Checkpoint no encontrado: {WEIGHTS_PATH}\n"
            "Ejecuta train_model.py primero para generar el archivo de pesos."
        )
    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"Directorio de datos no encontrado: {DATA_DIR}\n"
            "Ejecuta prepare_dataset.py para generar los magnetogramas procesados."
        )

    device = get_device()

    # ── 2. Cargar modelo ──────────────────────────────────────────────────────
    model = CoroniumV3(in_channels=2, dropout_rate=DROPOUT_RATE)
    state_dict = torch.load(WEIGHTS_PATH, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    # Los parámetros mantienen requires_grad=True por defecto en PyTorch.
    # Esto es necesario para que autograd construya el grafo durante el backward.
    total_params = sum(p.numel() for p in model.parameters())
    logger.info(
        "CoroniumV3 PRO cargado — %d parámetros  |  modo eval activo  |  device: %s",
        total_params,
        device,
    )

    # ── 3. Cargar muestra procesada ───────────────────────────────────────────
    input_tensor, raw_channels, sample_name = load_sample(DATA_DIR)
    input_tensor = input_tensor.to(device)

    # ── 4. Registrar hooks sobre la capa objetivo ─────────────────────────────
    hook_manager = GradCAMHookManager(model, TARGET_LAYER_NAME)

    try:
        # ── 5–6. Forward + backward + cómputo Grad-CAM ────────────────────────
        heatmap, prediction = compute_gradcam(
            model=model,
            input_tensor=input_tensor,
            hook_manager=hook_manager,
            target_size=(512, 512),
        )
    finally:
        # ── 8. Eliminar hooks (incluso si compute_gradcam lanzó excepción) ────
        hook_manager.remove()

    # ── 7. Visualización y guardado ───────────────────────────────────────────
    plot_gradcam(
        raw_channels=raw_channels,
        heatmap=heatmap,
        prediction=prediction,
        sample_name=sample_name,
        output_path=OUTPUT_FIGURE,
    )

    logger.info("=" * 62)
    logger.info("Pipeline Grad-CAM completado exitosamente.")
    logger.info("Capa objetivo     : model.%s (V3ResidualBlock 96→128)", TARGET_LAYER_NAME)
    logger.info("Resolución CAM    : (64, 64) → redimensionado a (512, 512)")
    logger.info("Figura guardada   : %s", OUTPUT_FIGURE)
    logger.info("=" * 62)


if __name__ == "__main__":
    main()
