FROM python:3.11-slim

WORKDIR /app

# System deps for matplotlib / scipy
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cache)
COPY requirements.api.txt .
RUN pip install --no-cache-dir -r requirements.api.txt

# Copy source code and assets
COPY src/         ./src/
COPY models/      ./models/
COPY experiments/ ./experiments/
COPY reports/     ./reports/

# Sample dataset (16 representative magnetograms for demo)
COPY data/sample/ ./data/processed/

# Expose port (Render uses $PORT, default 8000)
ENV PORT=8000
EXPOSE $PORT

CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"]
