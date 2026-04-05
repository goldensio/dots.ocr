"""
Fast API for dots.mocr OCR service
Receives a document and performs OCR, returning the text as markdown
"""
import os
import io
import tempfile
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import uvicorn

from dots_mocr.parser import DotsMOCRParser
from dots_mocr.utils.consts import image_extensions

# Initialize FastAPI app
app = FastAPI(
    title="dots.mocr OCR API",
    description="Fast OCR API that receives documents and returns markdown text",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global parser instance (will be initialized on startup)
parser: Optional[DotsMOCRParser] = None


def get_parser() -> DotsMOCRParser:
    """Get or initialize the parser instance"""
    global parser
    if parser is None:
        protocol = os.environ.get("VLLM_PROTOCOL", "http")
        ip = os.environ.get("VLLM_IP", "localhost")
        port = int(os.environ.get("VLLM_PORT", "8000"))
        model_name = os.environ.get("MODEL_NAME", "rednote-hilab/dots.mocr")
        temperature = float(os.environ.get("TEMPERATURE", "0.1"))
        top_p = float(os.environ.get("TOP_P", "1.0"))
        max_completion_tokens = int(os.environ.get("MAX_COMPLETION_TOKENS", "32768"))
        num_thread = int(os.environ.get("NUM_THREAD", "16"))
        dpi = int(os.environ.get("DPI", "200"))
        output_dir = os.environ.get("OUTPUT_DIR", "./output")
        use_hf = os.environ.get("USE_HF", "false").lower() == "true"

        parser = DotsMOCRParser(
            protocol=protocol,
            ip=ip,
            port=port,
            model_name=model_name,
            temperature=temperature,
            top_p=top_p,
            max_completion_tokens=max_completion_tokens,
            num_thread=num_thread,
            dpi=dpi,
            output_dir=output_dir,
            use_hf=use_hf,
        )
    return parser


@app.on_event("startup")
async def startup_event():
    """Initialize parser on startup"""
    get_parser()
    print("OCR Parser initialized successfully!")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "dots.mocr OCR API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/ocr": "Upload document for OCR (returns JSON with markdown)",
            "/ocr/file": "Upload document for OCR (returns .md file download)",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        _ = get_parser()
        return {"status": "healthy", "parser": "initialized"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/ocr")
async def ocr_document(
    file: UploadFile = File(..., description="Document file (PDF or image)"),
    prompt_mode: str = Form("prompt_ocr", description="Prompt mode for OCR processing"),
):
    """
    Upload a document and perform OCR, returning the markdown text as JSON

    Supported formats: PDF, PNG, JPEG, JPG, BMP, TIFF, WEBP
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Get file extension
    _, file_ext = os.path.splitext(file.filename)
    file_ext = file_ext.lower()

    if file_ext == '.pdf':
        # Handle PDF
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            dots_parser = get_parser()
            results = dots_parser.parse_pdf(
                tmp_file_path,
                os.path.splitext(file.filename)[0],
                prompt_mode,
                tempfile.gettempdir()
            )

            # Combine all markdown pages
            combined_md = ""
            for result in sorted(results, key=lambda x: x.get("page_no", 0)):
                md_path = result.get("md_content_path")
                if md_path and os.path.exists(md_path):
                    with open(md_path, "r", encoding="utf-8") as f:
                        combined_md += f.read() + "\n\n"

            os.unlink(tmp_file_path)

            return {
                "filename": file.filename,
                "status": "success",
                "total_pages": len(results),
                "markdown": combined_md.strip()
            }

        except Exception as e:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    elif file_ext in image_extensions:
        # Handle image
        content = await file.read()
        image_stream = io.BytesIO(content)

        try:
            image = Image.open(image_stream)
            image = image.convert("RGB")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                tmp_file_path = tmp_file.name
                image.save(tmp_file_path, format="PNG")

            dots_parser = get_parser()
            results = dots_parser.parse_image(
                tmp_file_path,
                os.path.splitext(file.filename)[0],
                prompt_mode,
                tempfile.gettempdir()
            )

            if results and len(results) > 0:
                md_path = results[0].get("md_content_path")
                if md_path and os.path.exists(md_path):
                    with open(md_path, "r", encoding="utf-8") as f:
                        markdown_content = f.read()

                    os.unlink(tmp_file_path)

                    return {
                        "filename": file.filename,
                        "status": "success",
                        "markdown": markdown_content
                    }

            os.unlink(tmp_file_path)
            raise HTTPException(status_code=500, detail="OCR processing produced no results")

        except Exception as e:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_ext}. Supported formats: PDF, {', '.join(image_extensions)}"
        )


@app.post("/ocr/file")
async def ocr_document_return_file(
    file: UploadFile = File(..., description="Document file (PDF or image)"),
    prompt_mode: str = Form("prompt_ocr", description="Prompt mode for OCR processing"),
):
    """
    Upload a document and perform OCR, returning the markdown as a downloadable .md file
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Get file extension
    _, file_ext = os.path.splitext(file.filename)
    file_ext = file_ext.lower()

    output_filename = os.path.splitext(file.filename)[0] + ".md"

    if file_ext == '.pdf':
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        try:
            dots_parser = get_parser()
            results = dots_parser.parse_pdf(
                tmp_file_path,
                os.path.splitext(file.filename)[0],
                prompt_mode,
                tempfile.gettempdir()
            )

            # Combine all markdown pages
            combined_md = ""
            for result in sorted(results, key=lambda x: x.get("page_no", 0)):
                md_path = result.get("md_content_path")
                if md_path and os.path.exists(md_path):
                    with open(md_path, "r", encoding="utf-8") as f:
                        combined_md += f.read() + "\n\n"

            os.unlink(tmp_file_path)

            # Create temp file for response
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".md") as md_file:
                md_file.write(combined_md.strip())
                md_file_path = md_file.name

            return FileResponse(
                md_file_path,
                media_type="text/markdown",
                filename=output_filename,
                background=lambda: os.unlink(md_file_path)
            )

        except Exception as e:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    elif file_ext in image_extensions:
        content = await file.read()
        image_stream = io.BytesIO(content)

        try:
            image = Image.open(image_stream)
            image = image.convert("RGB")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                image.save(tmp_file.name, format="PNG")
                tmp_file_path = tmp_file.name

            dots_parser = get_parser()
            results = dots_parser.parse_image(
                tmp_file_path,
                os.path.splitext(file.filename)[0],
                prompt_mode,
                tempfile.gettempdir()
            )

            if results and len(results) > 0:
                md_path = results[0].get("md_content_path")
                if md_path and os.path.exists(md_path):
                    with open(md_path, "r", encoding="utf-8") as f:
                        markdown_content = f.read()

                    os.unlink(tmp_file_path)

                    # Create temp file for response
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".md") as md_file:
                        md_file.write(markdown_content)
                        md_file_path = md_file.name

                    return FileResponse(
                        md_file_path,
                        media_type="text/markdown",
                        filename=output_filename,
                        background=lambda: os.unlink(md_file_path)
                    )

            os.unlink(tmp_file_path)
            raise HTTPException(status_code=500, detail="OCR processing produced no results")

        except Exception as e:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_ext}. Supported formats: PDF, {', '.join(image_extensions)}"
        )


if __name__ == "__main__":
    # Run the API server
    port = int(os.environ.get("API_PORT", "8080"))
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=1
    )
