"""
Script de validación del notebook de exploración
Prueba que el código del notebook funciona correctamente
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sunpy.map
import warnings

warnings.filterwarnings('ignore')

print("=" * 70)
print("VALIDACIÓN DEL NOTEBOOK DE EXPLORACIÓN")
print("=" * 70)

# 1. Buscar archivos
data_dir = Path('data/raw')
fits_files = sorted(list(data_dir.glob('*.fits')))

print(f"\n✓ Archivos encontrados: {len(fits_files)}")

if fits_files:
    # 2. Cargar primer magnetograma
    magnetogram_path = fits_files[0]
    print(f"✓ Cargando: {magnetogram_path.name}")
    
    solar_map = sunpy.map.Map(str(magnetogram_path))
    print(f"✓ Dimensiones: {solar_map.data.shape}")
    
    # 3. Metadatos clave
    print(f"\n📡 METADATOS:")
    print(f"  Instrumento: {solar_map.meta.get('INSTRUME', 'N/A')}")
    print(f"  Fecha: {solar_map.date}")
    print(f"  Resolución: {solar_map.meta.get('CDELT1', 'N/A')} arcsec/px")
    
    # 4. Estadísticas
    data = solar_map.data
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"  Min: {np.nanmin(data):.2f} G")
    print(f"  Max: {np.nanmax(data):.2f} G")
    print(f"  Media: {np.nanmean(data):.2f} G")
    print(f"  Std: {np.nanstd(data):.2f} G")
    
    # 5. Detección de regiones activas
    threshold = 200
    strong_positive = np.sum(data > threshold)
    strong_negative = np.sum(data < -threshold)
    total_active = strong_positive + strong_negative
    
    print(f"\n🔍 REGIONES ACTIVAS (|B| > {threshold} G):")
    print(f"  Píxeles activos: {total_active:,}")
    print(f"  Porcentaje: {100*total_active/data.size:.3f}%")
    
    print(f"\n✅ VALIDACIÓN EXITOSA - El notebook debería funcionar correctamente")
    print("=" * 70)
    
else:
    print("⚠️  No se encontraron archivos .fits")
