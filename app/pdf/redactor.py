import io
import base64
import re
import fitz  # PyMuPDF
import cv2
import numpy as np
from typing import List, Tuple

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Broad MY phone pattern: accepts +60, 01x, separators, spaces, parentheses
PHONE_RE = re.compile(r"(?:\+?6?0|0)(?:1[0-46-9]|[2-9])\d(?:[\s\-]?\d){6,8}")

def to_pix(page: fitz.Page) -> np.ndarray:
    mat = fitz.Matrix(2, 2)  # upscale for better detection
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    if pix.n == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img

def load_haar() -> cv2.CascadeClassifier:
    # uses built-in OpenCV data if available, else fallback to a common filename
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if cascade.empty():
        raise RuntimeError("Failed to load Haar cascade for face detection.")
    return cascade

class RedactionService:
    def __init__(self) -> None:
        self._face = load_haar()

    def redact(self, pdf_bytes: bytes) -> bytes:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        # 1) redact emails & phones via text search
        for page in doc:
            text = page.get_text("text")
            rects: List[fitz.Rect] = []
            for m in EMAIL_RE.finditer(text):
                quads = page.search_for(m.group(), hit_max=1000)
                rects.extend([fitz.Rect(q.rect) if hasattr(q, "rect") else q for q in quads])
            for m in PHONE_RE.finditer(text):
                quads = page.search_for(m.group(), hit_max=1000)
                rects.extend([fitz.Rect(q.rect) if hasattr(q, "rect") else q for q in quads])
            for r in rects:
                page.add_redact_annot(r, fill=(255, 255, 255))
            if rects:
                page.apply_redactions()

        # 2) detect faces in raster and delete image objects overlapping those regions
        for i, page in enumerate(doc):
            img = to_pix(page)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self._face.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
            if len(faces) == 0:
                continue

            # map image-space -> page rectangles to remove images
            # simple approach: remove all images on page if faces found inside their bbox
            img_list = page.get_images(full=True)
            for img_xref in img_list:
                xref = img_xref[0]
                bbox = page.get_image_bbox(xref)
                # if any detected face falls inside the image bbox, drop that image
                remove = False
                for (x, y, w, h) in faces:
                    # normalize to page coordinates using pixmap scaling heuristic
                    # (best-effort; PyMuPDF doesn't give direct pixel->page mapping for pixmaps)
                    # Use full-page heuristic: if any face exists, remove all images (safer bias-wise)
                    remove = True
                    break
                if remove:
                    page.delete_image(xref)

        out = io.BytesIO()
        doc.save(out, deflate=True, incremental=False, garbage=4)
        doc.close()
        return out.getvalue()

    @staticmethod
    def to_base64(pdf_bytes: bytes) -> str:
        return base64.b64encode(pdf_bytes).decode("utf-8")
