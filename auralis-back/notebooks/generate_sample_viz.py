"""
Generador de visualización de muestra del magnetograma
Crea una imagen PNG para verificar que la visualización funciona
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sunpy.map
import warnings

warnings.filterwarnings('ignore')

# Cargar datos
data_dir = Path('data/raw')
fits_files = sorted(list(data_dir.glob('*.fits')))

if fits_files:
    print(f"Cargando {fits_files[0].name}...")
    solar_map = sunpy.map.Map(str(fits_files[0]))
    
    # Crear visualización
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection=solar_map)
    
    # Configurar normalización
    from matplotlib.colors import Normalize
    norm = Normalize(vmin=-200, vmax=200)
    
    # Plotear con normalización ±200 G
    solar_map.plot(
        axes=ax,
        cmap='hmimag',
        norm=norm,
        title=f'Magnetograma SDO/HMI - {solar_map.date.strftime("%Y-%m-%d %H:%M:%S")} UTC'
    )
    
    # Grid heliográfico
    solar_map.draw_grid(axes=ax, color='white', alpha=0.4, linewidth=0.5)
    
    # Barra de color
    cbar = plt.colorbar(ax.images[0], ax=ax, fraction=0.046, pad=0.08)
    cbar.set_label('Campo Magnético (Gauss)', rotation=270, labelpad=25)
    
    # Información
    info_text = f"Resolución: {solar_map.dimensions[0].value}×{solar_map.dimensions[1].value} px\n"
    info_text += f"Rango: ±200 G"
    
    ax.text(
        0.02, 0.98, info_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
    )
    
    # Guardar
    output_path = 'notebooks/magnetogram_sample.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Visualización guardada en: {output_path}")
    plt.close()
    
else:
    print("⚠️ No se encontraron archivos")
