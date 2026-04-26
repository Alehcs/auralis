# Notebook de Exploración y Visualización

## 📓 Archivo: `01_exploracion_y_visualizacion.ipynb`

Este notebook proporciona exploración y visualización profesional de los magnetogramas solares descargados para el proyecto Auralis.

## ✅ Contenido del Notebook

### 1. Carga de Datos
- Utiliza `sunpy.map.Map` para cargar archivos FITS
- Detecta automáticamente todos los archivos en `data/raw/`

### 2. Inspección de Metadatos
Extrae información clave como:
- Instrumento (HMI_FRONT2)
- Fecha de observación
- Coordenadas del centro del Sol
- Resolución espacial (0.5 arcsec/pixel)

### 3. Análisis Estadístico
- Valores min/max/media/std del campo magnético
- Distribución de percentiles
- Detección de regiones activas (|B| > 200 G)

### 4. Visualización Científica
- Magnetograma con grid heliográfico
- Colormap `hmimag` especializado
- Normalización ±200 G para resaltar manchas solares

### 5. Histogramas
- Distribución completa del campo magnético
- Zoom en rango ±500 G

## ⚠️ Nota Importante sobre Normalización

**Si encuentras un error** `Cannot manually specify vmax`, actualiza la celda de visualización (Sección 4) para usar `Normalize`:

```python
from matplotlib.colors import Normalize

# En lugar de vmin=-200, vmax=200
norm = Normalize(vmin=-200, vmax=200)

solar_map.plot(
    axes=ax,
    cmap='hmimag',
    norm=norm,  # Usar norm en lugar de vmin/vmax
    title=f'Magnetograma SDO/HMI - {solar_map.date.strftime("%Y-%m-%d %H:%M:%S")} UTC'
)
```

## 🚀 Cómo Ejecutarlo

### Requisitos
```bash
# Asegúrate de que jupyter esté instalado
source venv/bin/activate
pip install jupyter ipykernel

# Opcionalmente, añadir widgets para mejor interactividad
pip install ipywidgets
```

### Ejecutar el Notebook
```bash
# Opción 1: JupyterLab (recomendado)
jupyter lab

# Opción 2: Jupyter Notebook clásico
jupyter notebook

# Navega a notebooks/01_exploracion_y_visualizacion.ipynb
```

### Ejecutar en VS Code
1. Abre el archivo `.ipynb` en VS Code
2. Selecciona el kernel de Python del venv
3. Ejecuta las celdas secuencialmente

## 📊 Resultados Esperados

✓ **17 archivos FITS** detectados (desde 2026-01-28 hasta 2026-02-09)  
✓ **Dimensiones**: 4096×4096 píxeles por imagen  
✓ **Rango de campo magnético**: ±4808 G (valores extremos)  
✓ **Regiones activas**: ~1.78% de píxeles con |B| > 200 G  

## 🔬 Validación

El script `validate_notebook.py` verifica que el código funciona correctamente:

```bash
python notebooks/validate_notebook.py
```

Resultado esperado:
```
✓ Archivos encontrados: 17
✓ Dimensiones: (4096, 4096)
📡 Instrumento: HMI_FRONT2
📊 Min: -4808.40 G, Max: 4808.40 G
✅ VALIDACIÓN EXITOSA
```

## 📸 Visualización de Muestra

Puedes generar una imagen PNG de muestra sin ejecutar el notebook completo:

```bash
python notebooks/generate_sample_viz.py
```

Esto creará `notebooks/magnetogram_sample.png` con la visualización del primer magnetograma.

---

**Proyecto**: Auralis - Detección de Manchas Solares  
**Fecha**: 2026-02-13
