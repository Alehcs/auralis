"""
Dataset Preparation Module for HeliosPipeline

Este módulo procesa magnetogramas HMI del SDO para prepararlos para entrenamiento
de modelos de Machine Learning/Deep Learning.

Pipeline de Procesamiento:
=========================
1. Carga masiva de archivos .fits desde data/raw/
2. Resample a 512x512 píxeles (reducción de resolución para ML)
3. Normalización: truncar a ±400 G y escalar a [-1, 1]
4. Almacenamiento como archivos .npy en data/processed/
5. Generación de metadata CSV con índice de manchas solares

Author: HeliosPipeline Team
Date: 2026-02-13
"""

import os
import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict
import warnings

import numpy as np
import sunpy.map
from skimage.transform import resize
from tqdm import tqdm


# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


def load_and_process_magnetogram(
    fits_path: Path,
    target_size: int = 512,
    clip_value: float = 400.0,
    sunspot_threshold: float = 200.0
) -> Tuple[np.ndarray, Dict[str, any]]:
    """
    Carga y procesa un magnetograma individual.
    
    Parameters
    ----------
    fits_path : Path
        Ruta al archivo FITS
    target_size : int
        Tamaño objetivo para redimensionar (default: 512x512)
    clip_value : float
        Valor de truncamiento en Gauss (default: ±400 G)
    sunspot_threshold : float
        Umbral para detectar manchas solares en Gauss (default: 200 G)
        
    Returns
    -------
    Tuple[np.ndarray, Dict]
        - Array procesado normalizado a [-1, 1]
        - Diccionario con metadatos (fecha, sunspot_index)
        
    Raises
    ------
    Exception
        Si hay error al cargar o procesar el archivo
    """
    try:
        # 1. Cargar magnetograma con SunPy
        solar_map = sunpy.map.Map(str(fits_path))
        data = solar_map.data
        
        # IMPORTANTE: Reemplazar NaN con 0 (ocurren en regiones fuera del disco solar)
        data = np.nan_to_num(data, nan=0.0)
        
        # 2. Calcular Sunspot Index ANTES de procesar
        # (porcentaje de píxeles con |B| > threshold)
        strong_field = np.abs(data) > sunspot_threshold
        sunspot_index = (np.sum(strong_field) / data.size) * 100
        
        # 3. Resample a target_size x target_size
        # Nota: resize de skimage preserva el rango de valores
        data_resampled = resize(
            data,
            (target_size, target_size),
            mode='reflect',
            anti_aliasing=True,
            preserve_range=True
        )
        
        # Asegurar que no haya NaN después del resample
        data_resampled = np.nan_to_num(data_resampled, nan=0.0)
        
        # 4. Normalización:
        # a) Truncar valores extremos (clip a ±clip_value G)
        data_clipped = np.clip(data_resampled, -clip_value, clip_value)
        
        # b) Escalar linealmente al rango [-1, 1]
        data_normalized = data_clipped / clip_value
        
        # 5. Extraer metadatos
        metadata = {
            'filename': fits_path.stem,
            'date': solar_map.date.iso,
            'sunspot_index': sunspot_index,
            'original_shape': data.shape,
            'processed_shape': data_normalized.shape,
            'min_value': np.min(data_normalized),
            'max_value': np.max(data_normalized),
            'mean_value': np.mean(data_normalized)
        }
        
        return data_normalized.astype(np.float32), metadata
        
    except Exception as e:
        logger.error(f"Error procesando {fits_path.name}: {str(e)}")
        raise


def prepare_dataset(
    raw_dir: str = "data/raw",
    processed_dir: str = "data/processed",
    target_size: int = 512,
    clip_value: float = 400.0,
    sunspot_threshold: float = 200.0
) -> List[Dict]:
    """
    Procesa todos los magnetogramas de forma masiva.
    
    Parameters
    ----------
    raw_dir : str
        Directorio con archivos .fits sin procesar
    processed_dir : str
        Directorio de salida para archivos .npy
    target_size : int
        Tamaño objetivo de las imágenes procesadas
    clip_value : float
        Valor de truncamiento en Gauss
    sunspot_threshold : float
        Umbral para calcular el sunspot index
        
    Returns
    -------
    List[Dict]
        Lista con metadatos de todas las imágenes procesadas
    """
    # Crear directorio de salida si no existe
    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)
    
    # Buscar todos los archivos .fits
    raw_path = Path(raw_dir)
    fits_files = sorted(list(raw_path.glob('*.fits')))
    
    if not fits_files:
        logger.warning(f"No se encontraron archivos .fits en {raw_dir}")
        return []
    
    logger.info(f"Encontrados {len(fits_files)} archivos para procesar")
    logger.info(f"Configuración: {target_size}x{target_size} px, clip: ±{clip_value} G")
    
    # Procesar cada archivo con barra de progreso
    all_metadata = []
    errors = []
    
    for fits_file in tqdm(fits_files, desc="Procesando magnetogramas", unit="archivo"):
        try:
            # Procesar imagen
            processed_data, metadata = load_and_process_magnetogram(
                fits_file,
                target_size=target_size,
                clip_value=clip_value,
                sunspot_threshold=sunspot_threshold
            )
            
            # Guardar como .npy
            output_filename = f"{fits_file.stem}_processed.npy"
            output_path = processed_path / output_filename
            np.save(str(output_path), processed_data)
            
            # Agregar ruta de salida al metadata
            metadata['processed_file'] = output_filename
            all_metadata.append(metadata)
            
        except Exception as e:
            logger.error(f"Error fatal con {fits_file.name}: {str(e)}")
            errors.append({
                'filename': fits_file.name,
                'error': str(e)
            })
            continue
    
    # Resumen de procesamiento
    logger.info(f"\n{'='*70}")
    logger.info(f"Procesamiento completado:")
    logger.info(f"  ✓ Archivos procesados exitosamente: {len(all_metadata)}")
    logger.info(f"  ✗ Archivos con errores: {len(errors)}")
    logger.info(f"  → Directorio de salida: {processed_path.absolute()}")
    logger.info(f"{'='*70}\n")
    
    if errors:
        logger.warning(f"Archivos con errores:")
        for error in errors:
            logger.warning(f"  - {error['filename']}: {error['error']}")
    
    return all_metadata


def save_metadata_csv(
    metadata_list: List[Dict],
    output_path: str = "data/processed/metadata_processed.csv"
) -> None:
    """
    Guarda los metadatos en formato CSV.
    
    Parameters
    ----------
    metadata_list : List[Dict]
        Lista de diccionarios con metadatos
    output_path : str
        Ruta del archivo CSV de salida
    """
    if not metadata_list:
        logger.warning("No hay metadatos para guardar")
        return
    
    # Asegurar que el directorio existe
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Definir columnas clave para el CSV
    fieldnames = [
        'filename',
        'date',
        'sunspot_index',
        'processed_file',
        'original_shape',
        'processed_shape',
        'min_value',
        'max_value',
        'mean_value'
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for metadata in metadata_list:
            # Convertir tuplas a strings para CSV
            metadata['original_shape'] = str(metadata['original_shape'])
            metadata['processed_shape'] = str(metadata['processed_shape'])
            writer.writerow(metadata)
    
    logger.info(f"✓ Metadata guardada en: {output_path}")
    logger.info(f"  Total de registros: {len(metadata_list)}")


def main():
    """
    Función principal para ejecutar el pipeline de pre-procesamiento.
    """
    logger.info("="*70)
    logger.info("HeliosPipeline - Dataset Preparation")
    logger.info("="*70)
    
    # Ejecutar pipeline de procesamiento
    metadata = prepare_dataset(
        raw_dir="data/raw",
        processed_dir="data/processed",
        target_size=512,
        clip_value=400.0,
        sunspot_threshold=200.0
    )
    
    # Guardar metadata como CSV
    if metadata:
        save_metadata_csv(
            metadata,
            output_path="data/processed/metadata_processed.csv"
        )
        
        # Mostrar estadísticas del dataset
        sunspot_indices = [m['sunspot_index'] for m in metadata]
        logger.info(f"\n{'='*70}")
        logger.info("Estadísticas del Dataset Procesado:")
        logger.info(f"  Total de imágenes: {len(metadata)}")
        logger.info(f"  Sunspot Index promedio: {np.mean(sunspot_indices):.3f}%")
        logger.info(f"  Sunspot Index min/max: {np.min(sunspot_indices):.3f}% / {np.max(sunspot_indices):.3f}%")
        logger.info(f"  Tamaño por imagen: 512x512 px")
        logger.info(f"  Rango de valores: [-1.0, 1.0]")
        logger.info(f"{'='*70}")
    else:
        logger.error("No se procesó ningún archivo exitosamente")


if __name__ == "__main__":
    main()
