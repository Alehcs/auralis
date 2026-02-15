import os
import sys
import time
import random
import logging
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
import warnings

import numpy as np
import pandas as pd
import sunpy.map
from sunpy.net import Fido
from sunpy.net import attrs as a
from skimage.transform import resize
from tqdm import tqdm


# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('massive_ingest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

class Config:
    """Configuración centralizada del pipeline."""
    
    # MODO PRODUCCIÓN: 2000 imágenes con tiempos anti-baneo incrementados
    TOTAL_IMAGES = 2000
    
    # Distribución por ciclo solar CORREGIDA (sin 2014 que da errores)
    # Períodos estables seleccionados:
    PERIOD_1 = {
        'name': '2011-2013',
        'start': '2011-01-01',
        'end': '2013-12-31',
        'samples': int(TOTAL_IMAGES * 0.25)  # 25% = 500 imágenes
    }
    
    PERIOD_2 = {
        'name': '2015-2018',
        'start': '2015-01-01',
        'end': '2018-12-31',
        'samples': int(TOTAL_IMAGES * 0.25)  # 25% = 500 imágenes
    }
    
    PERIOD_3 = {
        'name': '2021-2025',
        'start': '2021-01-01',
        'end': '2025-12-31',
        'samples': TOTAL_IMAGES - int(TOTAL_IMAGES * 0.25) - int(TOTAL_IMAGES * 0.25)  # 50% = 1000 imágenes
    }
    
    # Procesamiento
    BATCH_SIZE = 50
    TARGET_SIZE = 512
    CLIP_VALUE = 400.0
    SUNSPOT_THRESHOLD = 200.0
    
    # Anti-baneo (TIEMPOS INCREMENTADOS PARA MÁXIMA SEGURIDAD)
    SLEEP_MIN = 2.0  # segundos (antes: 1.0)
    SLEEP_MAX = 5.0  # segundos (antes: 3.0)
    BATCH_SLEEP_MIN = 30.0  # segundos (antes: 15.0)
    BATCH_SLEEP_MAX = 60.0  # segundos (antes: 30.0)
    
    # Retry con exponential backoff
    MAX_RETRIES = 5
    BACKOFF_BASE = 2  # 2^n segundos
    
    # Directorios
    RAW_DIR = Path("data/raw")
    PROCESSED_DIR = Path("data/processed")
    METADATA_CSV = PROCESSED_DIR / "metadata_processed.csv"


# ============================================================================
# GENERACIÓN DE FECHAS (MUESTREO CIENTÍFICO)
# ============================================================================

def generate_sampling_dates(config: Config) -> List[datetime]:
    """
    Genera fechas de muestreo distribuidas científicamente.
    
    Distribuye las fechas proporcionalmente entre períodos estables:
    - 2011-2013: 25%
    - 2015-2018: 25%
    - 2021-2025: 50%
    
    Returns
    -------
    List[datetime]
        Lista de fechas ordenadas cronológicamente
    """
    logger.info("Generando fechas de muestreo científico...")
    
    all_dates = []
    
    # Período 1: 2011-2013
    start_p1 = datetime.strptime(config.PERIOD_1['start'], '%Y-%m-%d')
    end_p1 = datetime.strptime(config.PERIOD_1['end'], '%Y-%m-%d')
    delta_p1 = (end_p1 - start_p1).days
    
    for _ in range(config.PERIOD_1['samples']):
        random_days = random.randint(0, delta_p1)
        random_date = start_p1 + timedelta(days=random_days)
        all_dates.append(random_date)
    
    # Período 2: 2015-2018
    start_p2 = datetime.strptime(config.PERIOD_2['start'], '%Y-%m-%d')
    end_p2 = datetime.strptime(config.PERIOD_2['end'], '%Y-%m-%d')
    delta_p2 = (end_p2 - start_p2).days
    
    for _ in range(config.PERIOD_2['samples']):
        random_days = random.randint(0, delta_p2)
        random_date = start_p2 + timedelta(days=random_days)
        all_dates.append(random_date)
    
    # Período 3: 2021-2025
    start_p3 = datetime.strptime(config.PERIOD_3['start'], '%Y-%m-%d')
    end_p3 = datetime.strptime(config.PERIOD_3['end'], '%Y-%m-%d')
    delta_p3 = (end_p3 - start_p3).days
    
    for _ in range(config.PERIOD_3['samples']):
        random_days = random.randint(0, delta_p3)
        random_date = start_p3 + timedelta(days=random_days)
        all_dates.append(random_date)
    
    # Ordenar cronológicamente
    all_dates.sort()
    
    logger.info(f"Generated {len(all_dates)} sampling dates")
    logger.info(f"  - {config.PERIOD_1['name']}: {config.PERIOD_1['samples']}")
    logger.info(f"  - {config.PERIOD_2['name']}: {config.PERIOD_2['samples']}")
    logger.info(f"  - {config.PERIOD_3['name']}: {config.PERIOD_3['samples']}")
    
    return all_dates


# ============================================================================
# DESCARGA CON RETRY Y EXPONENTIAL BACKOFF
# ============================================================================

def download_with_retry(
    date: datetime,
    download_dir: Path,
    config: Config
) -> Optional[Path]:
    """
    Descarga un magnetograma con retry y exponential backoff.
    
    Parameters
    ----------
    date : datetime
        Fecha objetivo
    download_dir : Path
        Directorio de descarga
    config : Config
        Configuración
    
    Returns
    -------
    Path or None
        Ruta al archivo descargado, o None si falla
    """
    for attempt in range(config.MAX_RETRIES):
        try:
            # Query para la fecha específica
            time_range = a.Time(date, date + timedelta(hours=1))
            query = Fido.search(
                time_range,
                a.Instrument("HMI"),
                a.Physobs("LOS_magnetic_field")
            )
            
            if len(query) == 0:
                logger.warning(f"No hay datos para {date.strftime('%Y-%m-%d')}")
                return None
            
            # Tomar el primer resultado
            downloaded = Fido.fetch(
                query[0, 0],
                path=str(download_dir / "{file}"),
                progress=False
            )
            
            file_path = Path(list(downloaded)[0])
            
            # Pausa anti-baneo (1-3 segundos)
            sleep_time = random.uniform(config.SLEEP_MIN, config.SLEEP_MAX)
            time.sleep(sleep_time)
            
            return file_path
            
        except Exception as e:
            # Verificar si es error de rate limiting
            if '429' in str(e) or '503' in str(e):
                wait_time = (config.BACKOFF_BASE ** attempt) + random.uniform(0, 1)
                logger.warning(
                    f"Rate limit detectado (intento {attempt + 1}/{config.MAX_RETRIES}). "
                    f"Esperando {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"Error descargando {date}: {str(e)}")
                return None
    
    logger.error(f"Máximo de reintentos alcanzado para {date}")
    return None


# ============================================================================
# PROCESAMIENTO (REUTILIZADO DEL PIPELINE ORIGINAL)
# ============================================================================

def process_magnetogram(
    fits_path: Path,
    config: Config
) -> Tuple[Optional[np.ndarray], Optional[Dict]]:
    """
    Procesa un magnetograma individual.
    
    Returns
    -------
    Tuple[ndarray, Dict] or Tuple[None, None]
        Array procesado y metadata, o (None, None) si falla
    """
    try:
        # Cargar con SunPy
        solar_map = sunpy.map.Map(str(fits_path))
        data = solar_map.data
        
        # Reemplazar NaN
        data = np.nan_to_num(data, nan=0.0)
        
        # Calcular Sunspot Index ANTES de procesar
        strong_field = np.abs(data) > config.SUNSPOT_THRESHOLD
        sunspot_index = (np.sum(strong_field) / data.size) * 100
        
        # Resample
        data_resampled = resize(
            data,
            (config.TARGET_SIZE, config.TARGET_SIZE),
            mode='reflect',
            anti_aliasing=True,
            preserve_range=True
        )
        
        data_resampled = np.nan_to_num(data_resampled, nan=0.0)
        
        # Normalización
        data_clipped = np.clip(data_resampled, -config.CLIP_VALUE, config.CLIP_VALUE)
        data_normalized = data_clipped / config.CLIP_VALUE
        
        # Metadata
        metadata = {
            'filename': fits_path.stem,
            'date': solar_map.date.iso,
            'sunspot_index': sunspot_index,
            'original_shape': str(data.shape),
            'processed_shape': str(data_normalized.shape),
            'min_value': float(np.min(data_normalized)),
            'max_value': float(np.max(data_normalized)),
            'mean_value': float(np.mean(data_normalized))
        }
        
        return data_normalized.astype(np.float32), metadata
        
    except Exception as e:
        logger.error(f"Error procesando {fits_path.name}: {str(e)}")
        return None, None


# ============================================================================
# VALIDACIÓN DE INTEGRIDAD
# ============================================================================

def validate_npy_file(npy_path: Path) -> bool:
    """
    Valida que el archivo .npy esté bien formado y no esté vacío.
    
    Returns
    -------
    bool
        True si el archivo es válido
    """
    try:
        if not npy_path.exists():
            return False
        
        # Verificar tamaño mínimo (archivo no vacío)
        if npy_path.stat().st_size < 100:  # menos de 100 bytes = corrupto
            logger.error(f"Archivo vacío o corrupto: {npy_path.name}")
            return False
        
        # Intentar cargar
        data = np.load(str(npy_path))
        
        # Verificar dimensiones
        if data.shape != (512, 512):
            logger.error(f"Dimensiones incorrectas: {data.shape}")
            return False
        
        # Verificar rango de valores
        if np.min(data) < -1.1 or np.max(data) > 1.1:
            logger.error(f"Valores fuera de rango: [{np.min(data)}, {np.max(data)}]")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validando {npy_path.name}: {str(e)}")
        return False


# ============================================================================
# PERSISTENCIA CON CSV APPEND
# ============================================================================

def append_to_csv(metadata: Dict, csv_path: Path):
    """
    Agrega metadata al CSV en modo append usando pandas.
    Garantiza escritura inmediata con flush.
    Crea el archivo con headers si no existe.
    """
    # Convertir metadata a DataFrame de una fila
    df_new = pd.DataFrame([metadata])
    
    # Verificar si el archivo ya existe
    file_exists = csv_path.exists()
    
    # Escribir con pandas (automáticamente hace flush)
    df_new.to_csv(
        csv_path,
        mode='a',  # Append mode
        header=not file_exists,  # Header solo si es nuevo
        index=False
    )
    
    # Flush explícito para garantizar escritura inmediata
    # (to_csv ya hace flush, pero lo hacemos explícito por seguridad)


def get_processed_files(csv_path: Path) -> set:
    """
    Obtiene el set de archivos ya procesados desde el CSV.
    Permite reanudar desde donde quedó.
    """
    if not csv_path.exists():
        return set()
    
    try:
        df = pd.read_csv(csv_path)
        if 'filename' in df.columns:
            return set(df['filename'].values)
        else:
            logger.warning("CSV no tiene columna 'filename', retornando set vacío")
            return set()
    except Exception as e:
        logger.error(f"Error leyendo CSV: {e}")
        return set()


# ============================================================================
# PIPELINE ETL POR LOTES
# ============================================================================

def process_batch_etl(
    dates: List[datetime],
    config: Config,
    processed_files: set
) -> Dict[str, int]:
    """
    Ejecuta el pipeline ETL completo por lotes.
    
    Para cada lote de 50 imágenes:
    1. Descarga → 2. Transforma → 3. Valida → 4. Limpia
    
    Returns
    -------
    Dict[str, int]
        Estadísticas de ejecución
    """
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    stats = {
        'total': len(dates),
        'already_processed': 0,
        'downloaded': 0,
        'processed': 0,
        'failed_download': 0,
        'failed_processing': 0,
        'failed_validation': 0
    }
    
    total_batches = (len(dates) + config.BATCH_SIZE - 1) // config.BATCH_SIZE
    
    logger.info("="*70)
    logger.info(f"Starting massive ingestion: {len(dates)} images")
    logger.info(f"Batches: {total_batches} (size: {config.BATCH_SIZE})")
    logger.info("="*70)
    
    # Iterar por lotes
    for batch_idx in range(total_batches):
        batch_start = batch_idx * config.BATCH_SIZE
        batch_end = min(batch_start + config.BATCH_SIZE, len(dates))
        batch_dates = dates[batch_start:batch_end]
        
        logger.info(f"\n{'='*70}")
        logger.info(f"BATCH {batch_idx + 1}/{total_batches} ({len(batch_dates)} images)")
        logger.info(f"{'='*70}")
        
        batch_files = []
        
        # Phase 1: Download
        logger.info("Phase 1: Download...")
        for date in tqdm(batch_dates, desc=f"Batch {batch_idx + 1} - Download", leave=False):
            # VERIFICACIÓN DE DUPLICADOS PRE-DESCARGA
            # Generar posibles variantes del nombre de archivo para esta fecha
            date_str = date.strftime('%Y.%m.%d')
            
            # Verificar si ya existe en processed_files
            # La verificación ahora se hace ANTES de intentar descargar
            is_already_processed = False
            for pf in processed_files:
                if date_str in pf:
                    is_already_processed = True
                    stats['already_processed'] += 1
                    break
            
            if is_already_processed:
                # Skip this date without downloading
                continue
            
            # Only download if not in processed_files
            fits_path = download_with_retry(date, config.RAW_DIR, config)
            
            if fits_path:
                # Additional verification: check if filename already exists in CSV
                if fits_path.stem in processed_files:
                    logger.info(f"File {fits_path.name} already processed, removing download...")
                    fits_path.unlink(missing_ok=True)
                    stats['already_processed'] += 1
                    continue
                
                batch_files.append(fits_path)
                stats['downloaded'] += 1
            else:
                stats['failed_download'] += 1
        
        # Phase 2: Transform and validate
        logger.info(f"Phase 2: Processing {len(batch_files)} files...")
        
        for fits_path in tqdm(batch_files, desc=f"Batch {batch_idx + 1} - Processing", leave=False):
            # Process magnetogram
            processed_data, metadata = process_magnetogram(fits_path, config)
            
            if processed_data is None:
                stats['failed_processing'] += 1
                continue
            
            # Guardar .npy
            output_filename = f"{fits_path.stem}_processed.npy"
            npy_path = config.PROCESSED_DIR / output_filename
            np.save(str(npy_path), processed_data)
            
            # Validate integrity
            if not validate_npy_file(npy_path):
                stats['failed_validation'] += 1
                # Remove corrupted file
                npy_path.unlink(missing_ok=True)
                continue
            
            # Add filename to metadata
            metadata['processed_file'] = output_filename
            
            # Persist to CSV (append)
            append_to_csv(metadata, config.METADATA_CSV)
            processed_files.add(metadata['filename'])
            
            stats['processed'] += 1
        
        # Phase 3: Cleanup
        logger.info("Phase 3: Cleaning .fits files...")
        for fits_path in batch_files:
            try:
                fits_path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Could not delete {fits_path.name}: {e}")
        
        # Pause between batches (anti-ban)
        if batch_idx < total_batches - 1:
            sleep_time = random.uniform(config.BATCH_SLEEP_MIN, config.BATCH_SLEEP_MAX)
            logger.info(f"Batch pause: {sleep_time:.1f}s")
            time.sleep(sleep_time)
    
    return stats


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal del pipeline de ingestión masiva."""
    
    config = Config()
    
    logger.info("="*70)
    logger.info("HELIOS PIPELINE - MASSIVE INGEST")
    logger.info("="*70)
    
    # 1. Generar fechas de muestreo
    dates = generate_sampling_dates(config)
    
    # 2. Obtener archivos ya procesados (para reanudar)
    processed_files = get_processed_files(config.METADATA_CSV)
    logger.info(f"\nFiles already processed: {len(processed_files)}")
    logger.info(f"Files pending: {len(dates) - len(processed_files)}")
    
    # 3. Ejecutar pipeline ETL
    start_time = time.time()
    stats = process_batch_etl(dates, config, processed_files)
    elapsed_time = time.time() - start_time
    
    # Execution summary
    logger.info("\n" + "="*70)
    logger.info("EXECUTION SUMMARY")
    logger.info("="*70)
    logger.info(f"Total dates: {stats['total']}")
    logger.info(f"Already processed (skip): {stats['already_processed']}")
    logger.info(f"Downloaded successfully: {stats['downloaded']}")
    logger.info(f"Processed successfully: {stats['processed']}")
    logger.info(f"Download failures: {stats['failed_download']}")
    logger.info(f"Processing failures: {stats['failed_processing']}")
    logger.info(f"Validation failures: {stats['failed_validation']}")
    logger.info(f"Total time: {elapsed_time/60:.2f} minutes")
    logger.info("="*70)
    
    success_rate = (stats['processed'] / stats['total']) * 100 if stats['total'] > 0 else 0
    logger.info(f"\nSuccess rate: {success_rate:.2f}%")
    
    if stats['processed'] > 0:
        logger.info(f"Massive dataset created successfully")
        logger.info(f"   Location: {config.PROCESSED_DIR}")
        logger.info(f"   Metadata: {config.METADATA_CSV}")


if __name__ == "__main__":
    main()
