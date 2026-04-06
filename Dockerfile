# Dockerfile for RunPod Serverless - dots.mocr OCR
# Use CUDA 12.8 for latest GPU support
FROM nvidia/cuda:12.8.0-devel-ubuntu22.04

# Install Python and system dependencies
# Ubuntu 22.04 has Python 3.10
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

# Install PyTorch with CUDA 12.8
RUN pip3 install --timeout=600 --extra-index-url https://download.pytorch.org/whl/cu128 -r requirements.txt

# Copy setup.py and install package
COPY setup.py ./
RUN pip3 install --no-deps -e .

# Copy tools for model download and model code
COPY tools/ ./tools/
COPY dots_ocr/ ./dots_ocr/

# Download model weights
RUN python3 tools/download_model.py && \
    mv weights/DotsMOCR /model && \
    rm -rf weights

# Copy handler
COPY handler.py .

# Create output directory
RUN mkdir -p /app/output

# Set environment variables for HuggingFace mode and CUDA debugging
ENV PYTHONUNBUFFERED=1
ENV CUDA_LAUNCH_BLOCKING=0
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
