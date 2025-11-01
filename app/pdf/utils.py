import io
from typing import Tuple
from fastapi import UploadFile, HTTPException
from PIL import Image
import fitz  # PyMuPDF

MAX_BYTES = 20 * 1024 * 1024  # 20MB

async def file_to_bytesio(file: UploadFile) -> bytes:
    b = await file.read()
    if len(b) > MAX_BYTES:
        raise HTTPException(413, "File too large (max 20MB).")
    return b

async def ensure_pdf_like(file: UploadFile) -> bytes:
    data = await file_to_bytesio(file)
    if file.content_type == "application/pdf":
        return data
    # Convert single image to 1-page PDF
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(400, "Invalid image format.")
    out = io.BytesIO()
    img.save(out, format="PDF")
    return out.getvalue()
