"""
RunPod Serverless Handler for dots.mocr OCR
"""
import os
import io
import tempfile
import base64
from typing import Optional
from PIL import Image
import runpod  # Required

from dots_mocr.parser import DotsMOCRParser
from dots_mocr.utils.consts import image_extensions

# Global parser instance
parser: Optional[DotsMOCRParser] = None


def get_parser():
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


def handler(event):
    """
    RunPod Serverless handler

    Expected event format:
    {
        "input": {
            "file_base64": "base64_encoded_file",
            "filename": "document.pdf",
            "prompt_mode": "prompt_ocr"
        }
    }
    """
    # Extract input data from the request
    input_data = event.get("input", {})
    file_base64 = input_data.get("file_base64")
    filename = input_data.get("filename", "document.pdf")
    prompt_mode = input_data.get("prompt_mode", "prompt_ocr")

    if not file_base64:
        return {
            "error": "No file provided. Please include 'file_base64' in input."
        }

    try:
        # Initialize parser
        dots_parser = get_parser()

        # Decode base64 file
        if "," in file_base64:
            file_base64 = file_base64.split(",")[1]

        file_data = base64.b64decode(file_base64)

        # Get file extension
        _, file_ext = os.path.splitext(filename)
        file_ext = file_ext.lower()

        # Process file
        if file_ext == '.pdf':
            # Handle PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_data)
                tmp_file_path = tmp_file.name

            try:
                results = dots_parser.parse_pdf(
                    tmp_file_path,
                    os.path.splitext(filename)[0],
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

                # Return the result
                return {
                    "status": "success",
                    "filename": filename,
                    "total_pages": len(results),
                    "markdown": combined_md.strip()
                }

            except Exception as e:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                raise e

        elif file_ext in image_extensions:
            # Handle image
            image_stream = io.BytesIO(file_data)
            image = Image.open(image_stream)
            image = image.convert("RGB")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                image.save(tmp_file, format="PNG")
                tmp_file_path = tmp_file.name

            try:
                results = dots_parser.parse_image(
                    tmp_file_path,
                    os.path.splitext(filename)[0],
                    prompt_mode,
                    tempfile.gettempdir()
                )

                if results and len(results) > 0:
                    md_path = results[0].get("md_content_path")
                    if md_path and os.path.exists(md_path):
                        with open(md_path, "r", encoding="utf-8") as f:
                            markdown_content = f.read()

                        os.unlink(tmp_file_path)

                        # Return the result
                        return {
                            "status": "success",
                            "filename": filename,
                            "markdown": markdown_content
                        }

                os.unlink(tmp_file_path)
                return {
                    "error": "OCR processing produced no results"
                }

            except Exception as e:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                raise e

        else:
            return {
                "error": f"Unsupported file format: {file_ext}"
            }

    except Exception as e:
        return {
            "error": f"OCR processing failed: {str(e)}"
        }


# Required - Start the RunPod serverless worker
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
