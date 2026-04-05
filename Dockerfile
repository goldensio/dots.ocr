# Use CUDA 13.0 + Ubuntu 22.04
FROM nvidia/cuda:13.0.1-devel-ubuntu22.04

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    python3.11-dev \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libcairo2 \
    wget \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Ensure python3 points to 3.11
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && python3 --version

# Upgrade pip, wheel, setuptools
RUN pip3 install --upgrade pip wheel setuptools

# Copy requirements and install
COPY requirements.txt ./
RUN pip3 install --timeout=600 -r requirements.txt

# Copy and install package
COPY setup.py ./
RUN pip3 install --no-deps -e .

# Copy app code
COPY dots_mocr/ ./dots_mocr/
COPY tools/ ./tools/
COPY api.py .
COPY launch_api.sh .
RUN chmod +x launch_api.sh

# Create output directory
RUN mkdir -p /app/output

EXPOSE 8080

ENV PYTHONUNBUFFERED=1
ENV API_PORT=8080
ENV VLLM_PROTOCOL=http
ENV VLLM_IP=host.docker.internal
ENV VLLM_PORT=8000
ENV MODEL_NAME=rednote-hilab/dots.mocr
ENV TEMPERATURE=0.1
ENV TOP_P=1.0
ENV MAX_COMPLETION_TOKENS=32768
ENV NUM_THREAD=16
ENV DPI=200
ENV OUTPUT_DIR=/app/output
ENV USE_HF=false

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

CMD ["python3", "api.py"]