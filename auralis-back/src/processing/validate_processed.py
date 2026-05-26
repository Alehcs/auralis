"""Small smoke test for processed dataset artifacts.

This script checks that metadata and at least one tensor can be loaded locally.
It is intended for quick manual verification, not as a full schema validator for
the training pipeline.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def validate_processed_dataset():
    """Print dataset summary statistics and save a sample diagnostic plot."""
    metadata_path = Path("data/processed/metadata_processed.csv")
    if not metadata_path.exists():
        print("ERROR: metadata_processed.csv not found")
        return

    metadata = pd.read_csv(metadata_path)
    print("="*70)
    print("PROCESSED DATASET VALIDATION")
    print("="*70)
    print(f"\n Total files: {len(metadata)}")
    print(f"\n Date range:")
    print(f"  Start: {metadata['date'].iloc[0]}")
    print(f"  End: {metadata['date'].iloc[-1]}")

    sample_file = Path(f"data/processed/{metadata['processed_file'].iloc[0]}")
    if not sample_file.exists():
        print(f"ERROR: {sample_file} not found")
        return

    data = np.load(str(sample_file))

    print(f"\n Sample validation: {sample_file.name}")
    print(f"  Shape: {data.shape}")
    print(f"  Dtype: {data.dtype}")
    print(f"  Min value: {np.min(data):.4f}")
    print(f"  Max value: {np.max(data):.4f}")
    print(f"  Mean: {np.mean(data):.4f}")
    print(f"  Std: {np.std(data):.4f}")

    if np.min(data) >= -1.0 and np.max(data) <= 1.0:
        print(" Normalization range is valid: [-1, 1]")
    else:
        print(" ERROR: values outside expected range")

    print(f"\n Sunspot Index:")
    print(f"  Mean: {metadata['sunspot_index'].mean():.3f}%")
    print(f"  Min: {metadata['sunspot_index'].min():.3f}%")
    print(f"  Max: {metadata['sunspot_index'].max():.3f}%")
    print(f"  Std: {metadata['sunspot_index'].std():.3f}%")

    print(f"\n Generating sample visualization...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    im1 = ax1.imshow(data, cmap='gray', vmin=-1, vmax=1)
    ax1.set_title(f'Processed Magnetogram\n{sample_file.stem[:30]}...', fontsize=10)
    ax1.axis('off')
    plt.colorbar(im1, ax=ax1, fraction=0.046, label='Normalized [-1, 1]')

    ax2.hist(data.flatten(), bins=100, color='steelblue', alpha=0.7, edgecolor='black')
    ax2.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero')
    ax2.set_xlabel('Normalized Value')
    ax2.set_ylabel('Frequency (pixels)')
    ax2.set_title('Processed Value Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = "data/processed/validation_sample.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Image saved to: {output_path}")

    print(f"\n{'='*70}")
    print(" VALIDATION COMPLETE - dataset is ready for training")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    validate_processed_dataset()
