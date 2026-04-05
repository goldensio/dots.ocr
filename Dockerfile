# Dockerfile for RunPod Serverless - dots.mocr OCR
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Install Python and system dependencies
# Ubuntu 22.04 has Python 3.10, not 3.12
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libcairo2 \
    wget \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip3 install --upgrade pip wheel setuptools

# Copy requirements first (for better caching)
COPY requirements.txt ./

# Install dependencies
RUN pip3 install --timeout=600 -r requirements.txt

# Copy setup.py and install package
COPY setup.py ./
RUN pip3 install --no-deps -e .

# Copy tools for model download
COPY tools/ ./tools/
COPY dots_mocr/ ./dots_mocr/

# Download model weights (this will cache in the layer)
RUN python3 tools/download_model.py && \
    mv weights/DotsMOCR /model && \
    rm -rf weights

# Copy handler and application code
COPY handler.py .

# Create output directory
RUN mkdir -p /app/output

# Set environment variables for HuggingFace mode with local model
ENV PYTHONUNBUFFERED=1
ENV USE_HF=true
ENV MODEL_NAME=/model
ENV TEMPERATURE=0.1
ENV TOP_P=1.0
ENV MAX_COMPLETION_TOKENS=32768
ENV DPI=200
ENV OUTPUT_DIR=/app/output

# Set the handler for RunPod Serverless
ENV HANDLER=handler

# Start the RunPod serverless worker
CMD ["python3", "-u", "handler.py"]
