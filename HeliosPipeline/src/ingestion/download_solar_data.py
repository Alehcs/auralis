import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Union

import astropy.units as u
from sunpy.net import Fido, attrs as a


#Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_solar_data(
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    sample_rate: int = 24,
    download_dir: str = "data/raw",
    instrument: str = "hmi",
    physobs: str = "los_magnetic_field"
) -> list:

    #Convertir strings a datetime si es necesario
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    logger.info(f"Iniciando descarga de datos solares desde {start_date} hasta {end_date}")
    logger.info(f"Intervalo de muestreo: {sample_rate} horas")
    
    #Asegurar que el directorio de descarga existe
    download_path = Path(download_dir)
    download_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directorio de descarga: {download_path.absolute()}")
    
    downloaded_files = []
    
    #Generar lista de timestamps para descargar según el sample_rate
    current_time = start_date
    sample_times = []
    
    while current_time <= end_date:
        sample_times.append(current_time)
        current_time += timedelta(hours=sample_rate)
    
    logger.info(f"Se descargarán {len(sample_times)} imágenes")
    
    #Descargar cada timestamp
    for idx, sample_time in enumerate(sample_times, 1):
        try:
            #Definir ventana de tiempo pequeña alrededor del timestamp objetivo
            # (±5 minutos para asegurar que capturamos una imagen cercana)
            time_start = sample_time - timedelta(minutes=5)
            time_end = sample_time + timedelta(minutes=5)
            
            logger.info(f"[{idx}/{len(sample_times)}] Buscando datos para {sample_time}")
            
            #Construir la consulta usando attrs de SunPy
            query = Fido.search(
                a.Time(time_start, time_end),
                a.Instrument(instrument),
                a.Physobs(physobs),
                a.Sample(24 * u.hour)  #esto ayuda a filtrar duplicados
            )
            
            #Verificar si se encontraron resultados
            if len(query) == 0:
                logger.warning(f"No se encontraron datos para {sample_time}")
                continue
            
            logger.info(f"Encontrados {len(query[0])} archivo(s). Descargando...")
            
            #Descargar archivos (toma el primero si hay múltiples)
            downloaded = Fido.fetch(
                query[0, 0],  #Tomar solo el primer resultado
                path=str(download_path / "{file}"),  #Mantener nombre original
                progress=True
            )
            
            #Convertir parfive.Results a lista de strings (rutas)
            downloaded_paths = list(downloaded)
            
            #Agregar a la lista de archivos descargados
            downloaded_files.extend(downloaded_paths)
            
            if downloaded_paths:
                logger.info(f"✓ Descargado: {Path(downloaded_paths[0]).name}")
            
        except Exception as e:
            logger.error(f"Error descargando datos para {sample_time}: {str(e)}")
            continue
    
    logger.info(f"Descarga completada. Total de archivos: {len(downloaded_files)}")
    return downloaded_files


def main():
    #Descargar magnetogramas desde hace 2 semanas hasta hace 2 días (evitar delay de procesamiento NASA)
    end_date = datetime.now() - timedelta(days=2)
    start_date = end_date - timedelta(days=14)
    
    logger.info("=== HeliosPipeline: Solar Data Ingestion ===")
    
    files = fetch_solar_data(
        start_date=start_date,
        end_date=end_date,
        sample_rate=24, 
        download_dir="data/raw"
    )
    
    if files:
        logger.info(f"\n{'='*60}")
        logger.info("Archivos descargados exitosamente:")
        for f in files:
            logger.info(f"  - {Path(f).name}")
        logger.info(f"{'='*60}")
    else:
        logger.warning("No se descargaron archivos.")


if __name__ == "__main__":
    main()
