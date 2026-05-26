"""Render a quick FITS magnetogram preview for notebook verification.

This helper is intentionally lightweight: it loads the first raw FITS file,
applies the same visualization range used in the exploratory notebook, and
writes a PNG artifact without requiring the full notebook to be executed.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sunpy.map
import warnings

warnings.filterwarnings('ignore')

data_dir = Path('data/raw')
fits_files = sorted(list(data_dir.glob('*.fits')))

if fits_files:
    print(f"Loading {fits_files[0].name}...")
    solar_map = sunpy.map.Map(str(fits_files[0]))

    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection=solar_map)

    # SunPy may already carry a norm in plot_settings; passing an explicit
    # Normalize object avoids conflicting vmin/vmax arguments.
    from matplotlib.colors import Normalize
    norm = Normalize(vmin=-200, vmax=200)

    solar_map.plot(
        axes=ax,
        cmap='hmimag',
        norm=norm,
        title=f'SDO/HMI Magnetogram - {solar_map.date.strftime("%Y-%m-%d %H:%M:%S")} UTC'
    )

    solar_map.draw_grid(axes=ax, color='white', alpha=0.4, linewidth=0.5)

    cbar = plt.colorbar(ax.images[0], ax=ax, fraction=0.046, pad=0.08)
    cbar.set_label('Magnetic Field (Gauss)', rotation=270, labelpad=25)

    info_text = f"Resolution: {solar_map.dimensions[0].value}x{solar_map.dimensions[1].value} px\n"
    info_text += "Display range: +/-200 G"

    ax.text(
        0.02, 0.98, info_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
    )

    output_path = 'notebooks/magnetogram_sample.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Preview saved to: {output_path}")
    plt.close()

else:
    print("No .fits files found in data/raw/")
