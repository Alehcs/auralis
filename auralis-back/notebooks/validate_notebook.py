"""Validate that the exploratory SunPy notebook can run against local FITS data.

The notebook is useful for inspecting raw HMI files before they enter the ML
pipeline. This script keeps the verification path small enough to run from the
terminal when Jupyter is not available.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sunpy.map
import warnings

warnings.filterwarnings('ignore')

print("=" * 70)
print("EXPLORATORY NOTEBOOK VALIDATION")
print("=" * 70)

data_dir = Path('data/raw')
fits_files = sorted(list(data_dir.glob('*.fits')))

print(f"\nFiles found: {len(fits_files)}")

if fits_files:
    magnetogram_path = fits_files[0]
    print(f"Loading: {magnetogram_path.name}")

    solar_map = sunpy.map.Map(str(magnetogram_path))
    print(f"Dimensions: {solar_map.data.shape}")

    print(f"\nMETADATA:")
    print(f"  Instrument: {solar_map.meta.get('INSTRUME', 'N/A')}")
    print(f"  Observation date: {solar_map.date}")
    print(f"  Spatial scale: {solar_map.meta.get('CDELT1', 'N/A')} arcsec/px")

    data = solar_map.data
    print(f"\nFIELD STATISTICS:")
    print(f"  Min: {np.nanmin(data):.2f} G")
    print(f"  Max: {np.nanmax(data):.2f} G")
    print(f"  Mean: {np.nanmean(data):.2f} G")
    print(f"  Std: {np.nanstd(data):.2f} G")

    threshold = 200
    strong_positive = np.sum(data > threshold)
    strong_negative = np.sum(data < -threshold)
    total_active = strong_positive + strong_negative

    print(f"\nACTIVE-REGION PROXY (|B| > {threshold} G):")
    print(f"  Active pixels: {total_active:,}")
    print(f"  Percentage: {100*total_active/data.size:.3f}%")

    print("\nVALIDATION PASSED - the notebook has the required local inputs")
    print("=" * 70)

else:
    print("No .fits files found in data/raw/")
