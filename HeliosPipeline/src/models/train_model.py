import os
import logging
from pathlib import Path
from typing import Tuple, Dict, List
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
import torchvision.transforms as transforms
from tqdm import tqdm


# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


# ============================================================================
# DATA AUGMENTATION
# ============================================================================

class SolarAugmentation:
    """Data augmentation transforms for solar magnetograms."""
    
    def __init__(self):
        self.transforms = transforms.Compose([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.5),
            transforms.RandomRotation(degrees=10)
        ])
    
    def __call__(self, img: torch.Tensor) -> torch.Tensor:
        """Apply random transformations to tensor."""
        return self.transforms(img)


# ============================================================================
# DATASET PERSONALIZADO CON AUGMENTATION
# ============================================================================

class SolarDataset(Dataset):
    """
    Dataset personalizado para magnetogramas solares procesados.
    
    NUEVO: Soporta Data Augmentation opcional para entrenamiento.
    
    Parameters
    ----------
    data_dir : str
        Directorio con archivos .npy procesados
    metadata_csv : str
        Ruta al archivo CSV con metadatos
    transform : callable, optional
        Transformaciones de data augmentation (ej: SolarAugmentation())
    """
    
    def __init__(
        self,
        data_dir: str = "data/processed",
        metadata_csv: str = "data/processed/metadata_processed.csv",
        transform=None
    ):
        self.data_dir = Path(data_dir)
        self.transform = transform
        
        # Load metadata
        self.metadata = pd.read_csv(metadata_csv)
        logger.info(f"Dataset loaded: {len(self.metadata)} samples")
        logger.info(f"Sunspot Index range: [{self.metadata['sunspot_index'].min():.3f}, "
                   f"{self.metadata['sunspot_index'].max():.3f}]")
    
    def __len__(self) -> int:
        """Retorna el número total de muestras."""
        return len(self.metadata)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Carga una muestra individual con augmentation opcional.
        
        Returns
        -------
        Tuple[torch.Tensor, torch.Tensor]
            - Imagen: tensor de forma (1, 512, 512) - canal único (grayscale)
            - Target: tensor de forma (1,) - sunspot_index para regresión
        """
        # Cargar imagen .npy
        filename = self.metadata.iloc[idx]['processed_file']
        img_path = self.data_dir / filename
        image = np.load(str(img_path))
        
        # Cargar target (sunspot_index)
        target = self.metadata.iloc[idx]['sunspot_index']
        
        # Convertir a tensores de PyTorch
        # Agregar dimensión de canal: (512, 512) -> (1, 512, 512)
        image = torch.from_numpy(image).float().unsqueeze(0)
        target = torch.tensor([target], dtype=torch.float32)
        
        # Aplicar Data Augmentation si está especificado
        if self.transform:
            image = self.transform(image)
        
        return image, target


# ============================================================================
# ARQUITECTURA DEL MODELO: SolarNet
# ============================================================================

class SolarNet(nn.Module):
    """
    Red Neuronal Convolucional para predicción de actividad solar.
    
    Arquitectura:
    - 4 capas convolucionales con BatchNorm y Dropout
    - Global Average Pooling
    - Capa final de regresión (1 neurona)
    
    Input: (batch, 1, 512, 512) - magnetogramas normalizados
    Output: (batch, 1) - predicción del sunspot index
    """
    
    def __init__(self, dropout_rate: float = 0.3):
        super(SolarNet, self).__init__()
        
        # ====================================================================
        # BLOQUE CONVOLUCIONAL 1
        # Input: (batch, 1, 512, 512)
        # Output: (batch, 32, 256, 256)
        # ====================================================================
        self.conv1 = nn.Conv2d(
            in_channels=1,
            out_channels=32,
            kernel_size=3,
            stride=1,
            padding=1
        )
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)  # 512 -> 256
        self.dropout1 = nn.Dropout2d(p=dropout_rate)
        
        # ====================================================================
        # BLOQUE CONVOLUCIONAL 2
        # Input: (batch, 32, 256, 256)
        # Output: (batch, 64, 128, 128)
        # ====================================================================
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)  # 256 -> 128
        self.dropout2 = nn.Dropout2d(p=dropout_rate)
        
        # ====================================================================
        # BLOQUE CONVOLUCIONAL 3
        # Input: (batch, 64, 128, 128)
        # Output: (batch, 128, 64, 64)
        # ====================================================================
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(kernel_size=2, stride=2)  # 128 -> 64
        self.dropout3 = nn.Dropout2d(p=dropout_rate)
        
        # ====================================================================
        # BLOQUE CONVOLUCIONAL 4
        # Input: (batch, 128, 64, 64)
        # Output: (batch, 256, 32, 32)
        # ====================================================================
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.pool4 = nn.MaxPool2d(kernel_size=2, stride=2)  # 64 -> 32
        self.dropout4 = nn.Dropout2d(p=dropout_rate)
        
        # ====================================================================
        # GLOBAL AVERAGE POOLING
        # Input: (batch, 256, 32, 32)
        # Output: (batch, 256)
        # ====================================================================
        self.global_avg_pool = nn.AdaptiveAvgPool2d((1, 1))
        
        # ====================================================================
        # CAPA FINAL DE REGRESIÓN
        # Input: (batch, 256)
        # Output: (batch, 1)
        # ====================================================================
        self.fc = nn.Linear(256, 1)
        
        # Función de activación
        self.relu = nn.ReLU()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass del modelo.
        
        Parameters
        ----------
        x : torch.Tensor
            Input de forma (batch, 1, 512, 512)
        
        Returns
        -------
        torch.Tensor
            Output de forma (batch, 1) - predicción del sunspot index
        """
        # Bloque 1: (batch, 1, 512, 512) -> (batch, 32, 256, 256)
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.pool1(x)
        x = self.dropout1(x)
        
        # Bloque 2: (batch, 32, 256, 256) -> (batch, 64, 128, 128)
        x = self.conv2(x)
        x = self.bn2(x)
        x = self.relu(x)
        x = self.pool2(x)
        x = self.dropout2(x)
        
        # Bloque 3: (batch, 64, 128, 128) -> (batch, 128, 64, 64)
        x = self.conv3(x)
        x = self.bn3(x)
        x = self.relu(x)
        x = self.pool3(x)
        x = self.dropout3(x)
        
        # Bloque 4: (batch, 128, 64, 64) -> (batch, 256, 32, 32)
        x = self.conv4(x)
        x = self.bn4(x)
        x = self.relu(x)
        x = self.pool4(x)
        x = self.dropout4(x)
        
        # Global Average Pooling: (batch, 256, 32, 32) -> (batch, 256, 1, 1)
        x = self.global_avg_pool(x)
        
        # Flatten: (batch, 256, 1, 1) -> (batch, 256)
        x = x.view(x.size(0), -1)
        
        # Regresión: (batch, 256) -> (batch, 1)
        x = self.fc(x)
        
        return x


# ============================================================================
# DETECCIÓN DE HARDWARE
# ============================================================================

def get_device() -> torch.device:
    """
    Detecta automáticamente el mejor dispositivo disponible.
    
    Prioridad:
    1. MPS (Apple Silicon - M1/M2/M3)
    2. CUDA (Nvidia GPU)
    3. CPU (fallback)
    
    Returns
    -------
    torch.device
        Dispositivo para entrenamiento
    """
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info(f"Using CUDA: {torch.cuda.get_device_name(0)}")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        logger.info("Using MPS (Apple Silicon)")
    else:
        device = torch.device("cpu")
        logger.info("Using CPU")
    
    return device


# ============================================================================
# EARLY STOPPING
# ============================================================================

class EarlyStopping:
    """
    Early Stopping para detener entrenamiento si no hay mejora.
    
    Parameters
    ----------
    patience : int
        Número de épocas sin mejora antes de detener
    min_delta : float
        Cambio mínimo para considerar como mejora
    """
    
    def __init__(self, patience: int = 10, min_delta: float = 0.0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False
    
    def __call__(self, val_loss: float) -> bool:
        """
        Verifica si debe detenerse el entrenamiento.
        
        Returns
        -------
        bool
            True si debe detenerse, False si continúa
        """
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0
        
        return self.early_stop


# ============================================================================
# LOOP DE ENTRENAMIENTO CON MÉTRICAS MEJORADAS
# ============================================================================

def train_epoch(
    model: nn.Module,
    train_loader: DataLoader,
    criterion_mse: nn.Module,
    criterion_mae: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device
) -> Tuple[float, float]:
    """
    Ejecuta una época de entrenamiento.
    
    Returns
    -------
    Tuple[float, float]
        (MSE promedio, MAE promedio) de la época
    """
    model.train()
    running_mse = 0.0
    running_mae = 0.0
    
    for images, targets in tqdm(train_loader, desc="Training", leave=False):
        # Mover datos al dispositivo
        images = images.to(device)
        targets = targets.to(device)
        
        # Forward pass
        outputs = model(images)
        loss_mse = criterion_mse(outputs, targets)
        loss_mae = criterion_mae(outputs, targets)
        
        # Backward pass y optimización (usamos MSE para backprop)
        optimizer.zero_grad()
        loss_mse.backward()
        optimizer.step()
        
        running_mse += loss_mse.item()
        running_mae += loss_mae.item()
    
    return running_mse / len(train_loader), running_mae / len(train_loader)


def validate_epoch(
    model: nn.Module,
    val_loader: DataLoader,
    criterion_mse: nn.Module,
    criterion_mae: nn.Module,
    device: torch.device
) -> Tuple[float, float]:
    """
    Ejecuta una época de validación.
    
    Returns
    -------
    Tuple[float, float]
        (MSE promedio, MAE promedio) de validación
    """
    model.eval()
    running_mse = 0.0
    running_mae = 0.0
    
    with torch.no_grad():
        for images, targets in tqdm(val_loader, desc="Validation", leave=False):
            images = images.to(device)
            targets = targets.to(device)
            
            outputs = model(images)
            loss_mse = criterion_mse(outputs, targets)
            loss_mae = criterion_mae(outputs, targets)
            
            running_mse += loss_mse.item()
            running_mae += loss_mae.item()
    
    return running_mse / len(val_loader), running_mae / len(val_loader)


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    num_epochs: int = 100,
    learning_rate: float = 0.001,
    patience: int = 10,
    device: torch.device = None
) -> Dict[str, List[float]]:
    """
    Entrena el modelo completo con Early Stopping y LR Scheduler.
    
    NUEVO:
    - Early Stopping (patience=10)
    - ReduceLROnPlateau (reduce LR si val_loss se estanca)
    - Métricas MAE + MSE
    
    Returns
    -------
    Dict[str, List[float]]
        Historial de pérdidas y métricas
    """
    if device is None:
        device = get_device()
    
    model = model.to(device)
    
    # Funciones de pérdida
    criterion_mse = nn.MSELoss()  # Para backprop
    criterion_mae = nn.L1Loss()   # Para métricas humanas
    
    # Optimizador Adam
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # LR Scheduler: Reduce LR si val_loss no mejora
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=0.5,  # Reducir LR a la mitad
        patience=5   # Esperar 5 épocas sin mejora
    )
    
    # Early Stopping
    early_stopping = EarlyStopping(patience=patience)
    
    # Historial para visualización
    history = {
        'train_mse': [],
        'val_mse': [],
        'train_mae': [],
        'val_mae': [],
        'learning_rate': []
    }
    
    logger.info("="*70)
    logger.info("Starting training - SolarNet V2 PRO")
    logger.info(f"Max epochs: {num_epochs}, Initial LR: {learning_rate}")
    logger.info(f"Early stopping patience: {patience} epochs")
    logger.info(f"Device: {device}")
    logger.info("="*70)
    
    best_val_mse = float('inf')
    
    for epoch in range(1, num_epochs + 1):
        # Entrenamiento
        train_mse, train_mae = train_epoch(
            model, train_loader, criterion_mse, criterion_mae, optimizer, device
        )
        
        # Validación
        val_mse, val_mae = validate_epoch(
            model, val_loader, criterion_mse, criterion_mae, device
        )
        
        # Obtener learning rate actual
        current_lr = optimizer.param_groups[0]['lr']
        
        # Guardar historial
        history['train_mse'].append(train_mse)
        history['val_mse'].append(val_mse)
        history['train_mae'].append(train_mae)
        history['val_mae'].append(val_mae)
        history['learning_rate'].append(current_lr)
        
        # Logging con MAE (más interpretable para humanos)
        logger.info(
            f"Época {epoch}/{num_epochs} - "
            f"Train MSE: {train_mse:.6f}, Val MSE: {val_mse:.6f} | "
            f"Train MAE: {train_mae:.4f}%, Val MAE: {val_mae:.4f}% | "
            f"LR: {current_lr:.6f}"
        )
        
        # Guardar mejor modelo
        if val_mse < best_val_mse:
            best_val_mse = val_mse
            # Asegurar que existe el directorio
            Path("models").mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), "models/helios_v2_pro.pth")
            logger.info(f"Best model saved (val_mse: {val_mse:.6f}, val_mae: {val_mae:.4f}%)")
        
        # LR Scheduler step
        scheduler.step(val_mse)
        
        # Early stopping check
        if early_stopping(val_mse):
            logger.info(f"\nEarly stopping triggered at epoch {epoch}")
            logger.info(f"No improvement for {patience} consecutive epochs")
            break
    
    logger.info("="*70)
    logger.info(f"Training completed")
    logger.info(f"Best val_mse: {best_val_mse:.6f}")
    logger.info(f"Epochs executed: {len(history['train_mse'])}/{num_epochs}")
    logger.info("="*70)
    
    return history


# ============================================================================
# VISUALIZACIÓN MEJORADA
# ============================================================================

def plot_learning_curve(
    history: Dict[str, List[float]],
    output_path: str = "reports/figures/learning_curve_v2_pro.png"
):
    """
    Genera y guarda la curva de aprendizaje con métricas mejoradas.
    
    NUEVO: Muestra MSE y MAE en subplots separados
    
    Parameters
    ----------
    history : Dict[str, List[float]]
        Historial de pérdidas y métricas
    output_path : str
        Ruta donde guardar la figura
    """
    # Crear directorio si no existe
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    epochs = range(1, len(history['train_mse']) + 1)
    
    # Subplot 1: MSE Loss
    ax1.plot(epochs, history['train_mse'], 'b-', label='Train MSE', linewidth=2)
    ax1.plot(epochs, history['val_mse'], 'r-', label='Validation MSE', linewidth=2)
    ax1.set_title('MSE Loss - SolarNet V2 PRO', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Época', fontsize=12)
    ax1.set_ylabel('MSE', fontsize=12)
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    # Subplot 2: MAE (más interpretable)
    ax2.plot(epochs, history['train_mae'], 'g-', label='Train MAE', linewidth=2)
    ax2.plot(epochs, history['val_mae'], 'orange', label='Validation MAE', linewidth=2)
    ax2.set_title('MAE (Mean Absolute Error) - Error en Términos Humanos', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Época', fontsize=12)
    ax2.set_ylabel('MAE (%)', fontsize=12)
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    # Subplot 3: Learning Rate
    ax3.plot(epochs, history['learning_rate'], 'm-', linewidth=2)
    ax3.set_title('Learning Rate Schedule', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Época', fontsize=12)
    ax3.set_ylabel('Learning Rate', fontsize=12)
    ax3.set_yscale('log')  # Escala logarítmica para LR
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"Learning curve saved: {output_path}")
    plt.close()


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal de entrenamiento V2 PRO."""
    
    # ========================================================================
    # CONFIGURACIÓN PROFESIONAL PARA DATASET MASIVO
    # ========================================================================
    BATCH_SIZE = 32          # ↑ Aumentado de 4 a 32 para dataset grande
    NUM_EPOCHS = 100         # ↑ Aumentado de 50 a 100 (con early stopping)
    LEARNING_RATE = 0.001
    EARLY_STOPPING_PATIENCE = 10  # Detener si no mejora en 10 épocas
    VAL_SPLIT = 0.2
    
    # Load dataset with data augmentation
    logger.info("Loading dataset...")
    
    # Training dataset with augmentation
    train_dataset_full = SolarDataset(
        data_dir="data/processed",
        metadata_csv="data/processed/metadata_processed.csv",
        transform=SolarAugmentation()
    )
    
    # Validation dataset without augmentation
    val_dataset_full = SolarDataset(
        data_dir="data/processed",
        metadata_csv="data/processed/metadata_processed.csv",
        transform=None
    )
    
    # 2. Split train/validation
    total_size = len(train_dataset_full)
    val_size = int(total_size * VAL_SPLIT)
    train_size = total_size - val_size
    
    # Split usando los mismos índices para train y val
    indices = list(range(total_size))
    train_indices = indices[:train_size]
    val_indices = indices[train_size:]
    
    # Create train/val subsets
    from torch.utils.data import Subset
    train_dataset = Subset(train_dataset_full, train_indices)
    val_dataset = Subset(val_dataset_full, val_indices)
    
    logger.info(f"Train: {len(train_dataset)} samples (with augmentation)")
    logger.info(f"Val: {len(val_dataset)} samples (without augmentation)")
    
    # 3. DataLoaders con batch_size aumentado
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0  # Ajustar según tu sistema
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )
    
    # Initialize model
    logger.info("Initializing SolarNet V2 PRO...")
    model = SolarNet(dropout_rate=0.3)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Total parameters: {total_params:,}")
    logger.info(f"Trainable parameters: {trainable_params:,}")
    
    # 5. Detectar hardware
    device = get_device()
    
    # 6. Entrenar con todas las mejoras
    history = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE,
        patience=EARLY_STOPPING_PATIENCE,
        device=device
    )
    
    # Save final model
    Path("models").mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), "models/helios_v2_final.pth")
    logger.info("Final model saved: models/helios_v2_final.pth")
    logger.info("Best model saved: models/helios_v2_pro.pth")
    
    # Generate learning curve
    plot_learning_curve(history)
    
    logger.info("\nTraining pipeline completed successfully")


if __name__ == "__main__":
    main()
