import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def validate_processed_dataset():
    # 1. Cargar metadata
    metadata_path = Path("data/processed/metadata_processed.csv")
    if not metadata_path.exists():
        print("ERROR: metadata_processed.csv no encontrado")
        return
    
    metadata = pd.read_csv(metadata_path)
    print("="*70)
    print("VALIDACIÓN DEL DATASET PROCESADO")
    print("="*70)
    print(f"\n Total de archivos: {len(metadata)}")
    print(f"\n Rango de fechas:")
    print(f"  Inicio: {metadata['date'].iloc[0]}")
    print(f"  Fin: {metadata['date'].iloc[-1]}")
    
    # 2. Validar un archivo de muestra
    sample_file = Path(f"data/processed/{metadata['processed_file'].iloc[0]}")
    if not sample_file.exists():
        print(f"ERROR: {sample_file} no encontrado")
        return
    
    data = np.load(str(sample_file))
    
    print(f"\n Validación de muestra: {sample_file.name}")
    print(f"  Shape: {data.shape}")
    print(f"  Dtype: {data.dtype}")
    print(f"  Min value: {np.min(data):.4f}")
    print(f"  Max value: {np.max(data):.4f}")
    print(f"  Mean: {np.mean(data):.4f}")
    print(f"  Std: {np.std(data):.4f}")
    
    # Verificar que los valores estén en [-1, 1]
    if np.min(data) >= -1.0 and np.max(data) <= 1.0:
        print(" Rango de normalización correcto: [-1, 1]")
    else:
        print(" ERROR: Valores fuera del rango esperado")
    
    # 3. Estadísticas del Sunspot Index
    print(f"\n Sunspot Index:")
    print(f"  Promedio: {metadata['sunspot_index'].mean():.3f}%")
    print(f"  Min: {metadata['sunspot_index'].min():.3f}%")
    print(f"  Max: {metadata['sunspot_index'].max():.3f}%")
    print(f"  Std: {metadata['sunspot_index'].std():.3f}%")
    
    # 4. Visualizar una imagen de muestra
    print(f"\n Generando visualización de muestra...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Imagen procesada
    im1 = ax1.imshow(data, cmap='gray', vmin=-1, vmax=1)
    ax1.set_title(f'Magnetograma Procesado\n{sample_file.stem[:30]}...', fontsize=10)
    ax1.axis('off')
    plt.colorbar(im1, ax=ax1, fraction=0.046, label='Normalizado [-1, 1]')
    
    # Histograma de valores
    ax2.hist(data.flatten(), bins=100, color='steelblue', alpha=0.7, edgecolor='black')
    ax2.axvline(0, color='red', linestyle='--', linewidth=2, label='Cero')
    ax2.set_xlabel('Valor Normalizado')
    ax2.set_ylabel('Frecuencia (píxeles)')
    ax2.set_title('Distribución de Valores Procesados')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = "data/processed/validation_sample.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Imagen guardada en: {output_path}")
    
    print(f"\n{'='*70}")
    print(" VALIDACIÓN COMPLETADA - Dataset listo para entrenam iento")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    validate_processed_dataset()
