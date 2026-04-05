# dots.mocr Fast API

A fast REST API for the dots.mocr OCR service that receives documents and returns the extracted text as markdown.

## Features

- Upload PDF or image files for OCR processing
- Get results as JSON or download as .md file
- Support for multiple prompt modes (OCR, layout detection, scene spotting, etc.)
- Fast processing with vLLM backend
- Easy deployment with Docker or directly via Python

## Installation

1. Install dependencies:
```bash
pip install -e .
```

2. Make sure you have a vLLM server running with dots.mocr model:
```bash
# Launch vLLM model server (in another terminal)
CUDA_VISIBLE_DEVICES=0 vllm serve rednote-hilab/dots.mocr \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.9 \
  --chat-template-content-format string \
  --trust-remote-code
```

## Running the API

### Quick Start (Default Settings)
```bash
bash launch_api.sh
```

### Custom Configuration
```bash
# Set environment variables
export VLLM_IP=localhost
export VLLM_PORT=8000
export API_PORT=8080
export MODEL_NAME=rednote-hilab/dots.mocr

# Run the API
python api.py
```

### With uvicorn directly
```bash
uvicorn api:app --host 0.0.0.0 --port 8080 --workers 1
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8080/health
```

### OCR Document (Returns JSON)
```bash
# Upload image
curl -X POST "http://localhost:8080/ocr" \
  -F "file=@document.jpg" \
  -F "prompt_mode=prompt_ocr"

# Upload PDF
curl -X POST "http://localhost:8080/ocr" \
  -F "file=@document.pdf" \
  -F "prompt_mode=prompt_layout_all_en"
```

### OCR Document (Returns .md File Download)
```bash
curl -X POST "http://localhost:8080/ocr/file" \
  -F "file=@document.jpg" \
  -F "prompt_mode=prompt_ocr" \
  -o output.md
```

## Prompt Modes

Available prompt modes for different tasks:

- `prompt_ocr` - Extract text only (excluding headers/footers)
- `prompt_layout_all_en` - Parse all layout info with detection and recognition
- `prompt_layout_only_en` - Layout detection only
- `prompt_web_parsing` - Parse web pages
- `prompt_scene_spotting` - Scene text spotting
- `prompt_general` - General purpose (use custom_prompt)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VLLM_PROTOCOL` | `http` | Protocol for vLLM server |
| `VLLM_IP` | `localhost` | IP address of vLLM server |
| `VLLM_PORT` | `8000` | Port of vLLM server |
| `MODEL_NAME` | `rednote-hilab/dots.mocr` | Model name |
| `API_PORT` | `8080` | Port for the API server |
| `TEMPERATURE` | `0.1` | Generation temperature |
| `TOP_P` | `1.0` | Top-p sampling parameter |
| `MAX_COMPLETION_TOKENS` | `32768` | Maximum tokens to generate |
| `NUM_THREAD` | `16` | Number of threads for PDF processing |
| `DPI` | `200` | DPI for PDF rendering |
| `OUTPUT_DIR` | `./output` | Output directory |
| `USE_HF` | `false` | Use HuggingFace instead of vLLM |

## Example Usage with Python

```python
import requests

# Upload document
url = "http://localhost:8080/ocr"
files = {"file": open("document.jpg", "rb")}
data = {"prompt_mode": "prompt_ocr"}

response = requests.post(url, files=files, data=data)
result = response.json()

print(result["markdown"])
```

## Supported File Formats

- **Images**: PNG, JPEG, JPG, BMP, TIFF, WEBP
- **Documents**: PDF

## Docker Deployment

### Quick Start with Scripts

#### Build and Run (All-in-One)
```bash
./build_and_run.sh
```

#### Separate Build and Run
```bash
# Build the image
./build.sh

# Run the container
docker run -d \
  --name dots-mocr-api \
  -p 8080:8080 \
  -e VLLM_IP=host.docker.internal \
  -e VLLM_PORT=8000 \
  -v $(pwd)/output:/app/output \
  dots-mocr-api:latest
```

### Using Docker Compose (Recommended)

Docker Compose sets up both the API and vLLM server:

```bash
# Start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Docker Commands

#### Build the Image
```bash
docker build -t dots-mocr-api .
```

#### Run the Container

**On macOS/Windows (Docker Desktop):**
```bash
docker run -d \
  --name dots-mocr-api \
  -p 8080:8080 \
  -e VLLM_IP=host.docker.internal \
  -e VLLM_PORT=8000 \
  -v $(pwd)/output:/app/output \
  dots-mocr-api
```

**On Linux:**
```bash
# Get host IP
HOST_IP=$(hostname -I | awk '{print $1}')

docker run -d \
  --name dots-mocr-api \
  -p 8080:8080 \
  -e VLLM_IP=$HOST_IP \
  -e VLLM_PORT=8000 \
  -v $(pwd)/output:/app/output \
  --network host \
  dots-mocr-api
```

#### Container Management
```bash
# View logs
docker logs -f dots-mocr-api

# Stop container
docker stop dots-mocr-api

# Start container
docker start dots-mocr-api

# Remove container
docker rm -f dots-mocr-api

# Shell into container
docker exec -it dots-mocr-api bash
```

### Docker Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | `8080` | API server port inside container |
| `VLLM_IP` | `host.docker.internal` | vLLM server IP |
| `VLLM_PORT` | `8000` | vLLM server port |
| `MODEL_NAME` | `rednote-hilab/dots.mocr` | Model name |
| `TEMPERATURE` | `0.1` | Generation temperature |
| `TOP_P` | `1.0` | Top-p sampling |
| `MAX_COMPLETION_TOKENS` | `32768` | Max tokens |
| `NUM_THREAD` | `16` | Thread count for PDFs |
| `DPI` | `200` | PDF rendering DPI |
| `OUTPUT_DIR` | `/app/output` | Output directory |

### Docker with External vLLM Server

If you have a vLLM server running separately:

```bash
# With Docker host network (Linux)
docker run -d \
  --name dots-mocr-api \
  --network host \
  -e VLLM_IP=localhost \
  -e VLLM_PORT=8000 \
  -v $(pwd)/output:/app/output \
  dots-mocr-api

# With custom network
docker network create dots-mocr-net
docker run -d \
  --name dots-mocr-api \
  --network dots-mocr-net \
  -p 8080:8080 \
  -e VLLM_IP=vllm-server \
  -e VLLM_PORT=8000 \
  dots-mocr-api
```

## API Response Format

### JSON Response (GET /ocr)
```json
{
  "filename": "document.jpg",
  "status": "success",
  "total_pages": 1,
  "markdown": "# Extracted text content..."
}
```

### File Download (POST /ocr/file)
Returns a `.md` file with the extracted content.
