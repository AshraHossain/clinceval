FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (chromadb needs build tools for SQLite)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# HuggingFace model cache directory (mount as volume)
ENV HF_HOME=/app/.cache/huggingface
RUN mkdir -p $HF_HOME

# Expose FastAPI port
EXPOSE 8000

# Warm up the embedding model and retriever on startup
RUN python -c "from app.retriever import get_retriever; get_retriever()" || true

# Run FastAPI
CMD ["python", "-m", "uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
