# Exploratory Magnetogram Notebook

## File: `01_exploracion_y_visualizacion.ipynb`

This notebook is a manual inspection tool for raw HMI FITS magnetograms. It is not part of the training or API runtime path, but it is useful when validating newly downloaded data before preprocessing.

## Notebook Scope

### 1. Data Loading
- Uses `sunpy.map.Map` to load FITS files with WCS metadata.
- Detects available files under `data/raw/`.

### 2. Metadata Inspection
Captures instrument, observation timestamp, Sun-center coordinates, and spatial scale. These fields are useful for spotting corrupted or unexpected FITS records before they enter the dataset.

### 3. Field Statistics
- Min, max, mean, and standard deviation of the magnetic field.
- Percentile distribution for display-range selection.
- Active-region proxy count using `|B| > 200 G`.

### 4. Visualization
- Magnetogram rendered with the HMI-specific `hmimag` colormap.
- Heliographic grid overlay for orientation.
- Display normalization around `+/-200 G`, which highlights active regions without letting extreme pixels dominate the image.

### 5. Histograms
- Full magnetic-field distribution.
- Zoomed distribution around `+/-500 G`.

## SunPy Normalization Note

If SunPy raises `Cannot manually specify vmax`, use an explicit `Normalize` object instead of passing `vmin` and `vmax` directly:

```python
from matplotlib.colors import Normalize

norm = Normalize(vmin=-200, vmax=200)

solar_map.plot(
    axes=ax,
    cmap='hmimag',
    norm=norm,
    title=f'SDO/HMI Magnetogram - {solar_map.date.strftime("%Y-%m-%d %H:%M:%S")} UTC'
)
```

## Running the Notebook

### Requirements
```bash
source venv/bin/activate
pip install jupyter ipykernel

pip install ipywidgets
```

### Jupyter
```bash
jupyter lab

jupyter notebook
```

Open `notebooks/01_exploracion_y_visualizacion.ipynb` and select the backend virtual environment as the kernel.

## Expected Local Inputs

- FITS files under `data/raw/`.
- Typical HMI dimensions: `4096 x 4096` pixels.
- Magnetic field values in Gauss, often with long tails around active regions.

## Validation

Use the terminal validator when you only need to confirm that SunPy can load the local FITS files:

```bash
python notebooks/validate_notebook.py
```

## Sample Preview

Generate a PNG preview without running the notebook:

```bash
python notebooks/generate_sample_viz.py
```

The output is written to `notebooks/magnetogram_sample.png`.
