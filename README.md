# Helios Pipeline: Solar Activity Prediction System

An enterprise-grade deep learning pipeline for real-time solar activity monitoring and forecasting using SDO/HMI magnetograms.

## Abstract / Executive Summary

Space weather events, driven by solar activity, pose significant risks to satellite infrastructure, power grids, and radio communications. Use of traditional forecasting methods often lacks the temporal resolution required for immediate mitigation. This project implements **SolarNet CNN**, a deep learning model served via **FastAPI**, to analyze solar magnetograms in near real-time. By providing accurate sunspot index predictions and risk assessments, Helios Pipeline enables proactive protection of critical technological infrastructure.
<img width="1773" height="1487" alt="image" src="https://github.com/user-attachments/assets/3eac8a15-69de-4eab-9495-3cdbae70da39" />

## Architecture

This system utilizes a decoupled microservices-inspired architecture:

-   **Backend**: Python 3.10+ / FastAPI. Handles data ingestion, image processing, and model inference.
-   **Machine Learning**: PyTorch / SolarNet CCN. Custom convolutional neural network optimized for specific features in solar magnetograms.
-   **Frontend**: React 18 / TypeScript / Vite. Interactive dashboard for real-time monitoring and historical analysis.
-   **Data Flow**: 
    1.  Ingestion service fetches raw `.fits` data from NASA JSOC.
    2.  Processing pipeline normalizes and converts data to optimized `.npy` tensors.
    3.  Inference engine (SolarNet) assesses activity and risk levels.
    4.  API serves results and visual explanations (Grad-CAM) to the client.

## Project Structure

```bash
Helios-Pipeline/
├── HeliosPipeline/           # Backend Application from Python
│   ├── src/
│   │   ├── api/              # REST API endpoints (FastAPI)
│   │   ├── ingestion/        # Solar data acquisition scripts
│   │   ├── models/           # SolarNet architecture and training
│   │   ├── processing/       # Data cleaning and transformation
│   │   └── visualization/    # Grad-CAM and plotting utilities
│   └── data/                 # Local data storage (raw/processed)
├── Helios-front/             # Frontend Application (React)
│   ├── src/
│   │   ├── assets/           # Static resources
│   │   ├── features/         # Functional modules (Dashboard, etc)
│   │   └── lib/              # Shared utilities
│   └── package.json
└── requirements.txt          # Python dependencies
```

## Prerequisites

-   **Python**: 3.9+
-   **Node.js**: 18+ (LTS recommended)
-   **npm** or **yarn**
-   **Docker** (Optional, for containerized deployment)

## Installation & Setup

### Backend (Python)

1.  Navigate to the project root:
    ```bash
    cd HeliosPipeline
    ```

2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r ../requirements.txt
    ```

### Frontend (React)

1.  Navigate to the frontend directory:
    ```bash
    cd Helios-front
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

## Usage / Execution

### 1. Start the API Server

From the `HeliosPipeline` directory (with venv activated):

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
*The API will be available at http://localhost:8000*

### 2. Start the Web Client

From the `Helios-front` directory:

```bash
npm run dev
```
*The dashboard will be available at http://localhost:5173*

## Model Metrics

The SolarNet V2 Pro model has been trained and validated with the following performance metrics:

| Metric | Value | Description |
| :--- | :--- | :--- |
| **Validation MAE** | **0.1416** | Mean Absolute Error on validation set |
| **Loss Function** | **MSE** | Optimized using Mean Squared Error |
| **Input Resolution** | **512x512** | High-fidelity magnetogram processing |

## License

**Proprietary Software**
All rights reserved. Unauthorized copying of this file, via any medium, is strictly prohibited.

## Authors / Contact

**Alejandro C.**
Software Engineer
