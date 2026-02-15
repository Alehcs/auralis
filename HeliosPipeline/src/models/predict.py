import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Tuple, Optional
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import sunpy.map
from skimage.transform import resize

# Importar arquitectura del modelo
from train_model import SolarNet, get_device


# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


# ============================================================================
# PRE-PROCESAMIENTO AL VUELO
# ============================================================================

def preprocess_fits_image(
    fits_path: Path,
    target_size: int = 512,
    clip_value: float = 400.0
) -> torch.Tensor:
    logger.info(f"Pre-procesando: {fits_path.name}")
    
    # 1. Cargar con SunPy
    solar_map = sunpy.map.Map(str(fits_path))
    data = solar_map.data
    
    # 2. Reemplazar NaN con 0 (regiones fuera del disco solar)
    data = np.nan_to_num(data, nan=0.0)
    
    logger.info(f"  Original: {data.shape}, Min: {np.min(data):.2f} G, Max: {np.max(data):.2f} G")
    
    # 3. Resample a target_size x target_size
    data_resampled = resize(
        data,
        (target_size, target_size),
        mode='reflect',
        anti_aliasing=True,
        preserve_range=True
    )
    
    # Asegurar que no haya NaN después del resample
    data_resampled = np.nan_to_num(data_resampled, nan=0.0)
    
    # 4. Normalización: clip a ±clip_value y escala a [-1, 1]
    data_clipped = np.clip(data_resampled, -clip_value, clip_value)
    data_normalized = data_clipped / clip_value
    
    logger.info(f"  Procesado: {data_normalized.shape}, Rango: [{np.min(data_normalized):.3f}, {np.max(data_normalized):.3f}]")
    
    # 5. Convertir a tensor PyTorch
    # Forma: (512, 512) -> (1, 512, 512) -> (1, 1, 512, 512)
    #        (H, W)     -> (C, H, W)     -> (B, C, H, W)
    tensor = torch.from_numpy(data_normalized).float()
    tensor = tensor.unsqueeze(0)  # Añadir canal: (1, 512, 512)
    tensor = tensor.unsqueeze(0)  # Añadir batch: (1, 1, 512, 512)
    
    logger.info(f"  Tensor shape: {tensor.shape}")
    
    return tensor, solar_map


# ============================================================================
# CARGA DEL MODELO
# ============================================================================

def load_model(
    model_path: str = "models/helios_best.pth",
    device: Optional[torch.device] = None
) -> SolarNet:

    if device is None:
        device = get_device()
    
    # Verificar que existe el archivo
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
    
    logger.info(f"Cargando modelo desde: {model_path}")
    
    # Instanciar arquitectura
    model = SolarNet(dropout_rate=0.3)
    
    # Cargar pesos
    model.load_state_dict(torch.load(model_path, map_location=device))
    
    # Modo evaluación (desactiva dropout y batchnorm)
    model.eval()
    
    # Mover al dispositivo
    model = model.to(device)
    
    # Contar parámetros
    total_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Modelo cargado: {total_params:,} parámetros")
    logger.info(f"Dispositivo: {device}")
    
    return model, device


# ============================================================================
# INFERENCIA
# ============================================================================

def predict_sunspot_index(
    model: SolarNet,
    image_tensor: torch.Tensor,
    device: torch.device
) -> float:
    
    # Mover tensor al dispositivo
    image_tensor = image_tensor.to(device)
    
    # Inferencia (sin calcular gradientes)
    with torch.no_grad():
        prediction = model(image_tensor)
    
    # Convertir a escalar de Python
    predicted_index = prediction.item()
    
    logger.info(f"Predicción: {predicted_index:.4f}%")
    
    return predicted_index


# ============================================================================
# OBTENER VALOR REAL DEL CSV
# ============================================================================

def get_real_sunspot_index(
    filename: str,
    metadata_csv: str = "data/processed/metadata_processed.csv"
) -> Optional[float]:

    if not Path(metadata_csv).exists():
        logger.warning(f"Metadata CSV no encontrado: {metadata_csv}")
        return None
    
    metadata = pd.read_csv(metadata_csv)
    
    # Buscar el archivo en el metadata
    match = metadata[metadata['filename'] == filename]
    
    if len(match) == 0:
        logger.warning(f"Archivo '{filename}' no encontrado en metadata")
        return None
    
    real_index = match.iloc[0]['sunspot_index']
    logger.info(f"Valor real: {real_index:.4f}%")
    
    return real_index


# ============================================================================
# VISUALIZACIÓN
# ============================================================================

def visualize_prediction(
    solar_map: sunpy.map.Map,
    predicted_index: float,
    real_index: Optional[float] = None,
    output_path: str = "reports/figures/prediction_result.png"
):
    # Crear directorio si no existe
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection=solar_map)
    
    # Plotear magnetograma
    from matplotlib.colors import Normalize
    norm = Normalize(vmin=-200, vmax=200)
    
    solar_map.plot(
        axes=ax,
        cmap='hmimag',
        norm=norm
    )
    
    # Grid heliográfico
    solar_map.draw_grid(axes=ax, color='white', alpha=0.4, linewidth=0.5)
    
    # Título con resultados
    if real_index is not None:
        error = abs(predicted_index - real_index)
        error_pct = (error / real_index) * 100 if real_index > 0 else 0
        
        title = f'Magnetograma SDO/HMI - {solar_map.date.strftime("%Y-%m-%d %H:%M:%S")} UTC\n'
        title += f'Sunspot Index Real: {real_index:.4f}% | Predicho (IA): {predicted_index:.4f}%\n'
        title += f'Error Absoluto: {error:.4f}% ({error_pct:.2f}% error relativo)'
        
        ax.set_title(title, fontsize=11, fontweight='bold')
    else:
        title = f'Magnetograma SDO/HMI - {solar_map.date.strftime("%Y-%m-%d %H:%M:%S")} UTC\n'
        title += f'Sunspot Index Predicho (IA): {predicted_index:.4f}%'
        
        ax.set_title(title, fontsize=11, fontweight='bold')
    
    # Colorbar
    cbar = plt.colorbar(ax.images[0], ax=ax, fraction=0.046, pad=0.08)
    cbar.set_label('Campo Magnético (Gauss)', rotation=270, labelpad=25)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"✓ Visualización guardada en: {output_path}")
    plt.close()


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(
        description="Predicción de Sunspot Index usando SolarNet"
    )
    parser.add_argument(
        '--image',
        type=str,
        default=None,
        help='Ruta al archivo .fits (si no se especifica, usa el primero de data/raw/)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='models/helios_best.pth',
        help='Ruta al modelo entrenado (default: models/helios_best.pth)'
    )
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("HeliosPipeline - Inferencia de Sunspot Index")
    logger.info("="*70)
    
    # 1. Determinar imagen a procesar
    if args.image:
        image_path = Path(args.image)
    else:
        # Usar el primer archivo de data/raw/
        raw_files = sorted(list(Path("data/raw").glob("*.fits")))
        if not raw_files:
            logger.error("No se encontraron archivos .fits en data/raw/")
            return
        image_path = raw_files[0]
        logger.info(f"Usando imagen por defecto: {image_path.name}")
    
    if not image_path.exists():
        logger.error(f"Archivo no encontrado: {image_path}")
        return
    
    # 2. Cargar modelo
    model, device = load_model(args.model)
    
    # 3. Pre-procesar imagen
    image_tensor, solar_map = preprocess_fits_image(image_path)
    
    # 4. Realizar predicción
    predicted_index = predict_sunspot_index(model, image_tensor, device)
    
    # 5. Obtener valor real (si existe)
    filename = image_path.stem  # Nombre sin extensión
    real_index = get_real_sunspot_index(filename)
    
    # 6. Visualizar resultado
    visualize_prediction(solar_map, predicted_index, real_index)
    
    # 7. Resumen
    logger.info("\n" + "="*70)
    logger.info("RESULTADO DE LA PREDICCIÓN")
    logger.info("="*70)
    logger.info(f"Archivo: {image_path.name}")
    logger.info(f"Sunspot Index Predicho: {predicted_index:.4f}%")
    
    if real_index is not None:
        error = abs(predicted_index - real_index)
        error_pct = (error / real_index) * 100 if real_index > 0 else 0
        logger.info(f"Sunspot Index Real: {real_index:.4f}%")
        logger.info(f"Error Absoluto: {error:.4f}%")
        logger.info(f"Error Relativo: {error_pct:.2f}%")
    
    logger.info("="*70)
    logger.info("\n✅ Inferencia completada exitosamente")


if __name__ == "__main__":
    main()
