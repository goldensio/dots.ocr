# Dockerfile for RunPod Serverless - dots.mocr OCR
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Install Python and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3-pip \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libcairo2 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip3 install --upgrade pip wheel setuptools

# Copy requirements
COPY requirements.txt ./

# Install dependencies
RUN pip3 install --timeout=600 -r requirements.txt

# Copy setup.py and install package
COPY setup.py ./
RUN pip3 install --no-deps -e .

# Copy application code
COPY dots_mocr/ ./dots_mocr/
COPY tools/ ./tools/
COPY handler.py .

# Create output directory
RUN mkdir -p /app/output

# Set environment variables for HuggingFace mode
ENV PYTHONUNBUFFERED=1
ENV USE_HF=true
ENV MODEL_NAME=rednote-hilab/dots.mocr
ENV TEMPERATURE=0.1
ENV TOP_P=1.0
ENV MAX_COMPLETION_TOKENS=32768
ENV DPI=200
ENV OUTPUT_DIR=/app/output

# Set the handler for RunPod
ENV HANDLER=handler

# Default command (RunPod will override this)
CMD ["python3", "-u", "handler.py"]
