from typing import List, Dict, Any, Tuple
import io
import spacy
from spacy_layout import spaCyLayout

# Basic heading normalization borrowed from your notebook idea
MAJOR_HEADINGS = {
    "skills": ["skill", "skills", "technical skills", "tech stack", "competencies"],
    "education": ["education", "academic", "qualification", "qualifications", "academics"],
    "experience": ["experience", "work experience", "employment", "career history", "professional experience"],
}

def normalize_heading(h: str | Any) -> str:
    # Handle spaCy Span objects or other types by converting to string
    if hasattr(h, 'text'):
        h = str(h.text)
    elif not isinstance(h, str):
        h = str(h) if h is not None else ""
    
    h = (h or "").strip().lower()
    for canon, alts in MAJOR_HEADINGS.items():
        if h == canon or any(h == a for a in alts) or any(h.startswith(a) for a in alts):
            return canon.title()
    return (h or "other").title()

class LayoutService:
    def __init__(self) -> None:
        self._nlp = spacy.blank("en")
        self._layout = spaCyLayout(self._nlp)

    def extract_groups(self, pdf_bytes: bytes) -> Tuple[Any, List[Dict[str, Any]]]:
        doc = self._layout(pdf_bytes)  # spaCy Doc with layout spans & headings
        groups: List[Dict[str, Any]] = []

        # Group text by inferred headings (spaCy-Layout exposes spans["layout"])
        # Each span has .label_ like "heading" / "text" and bbox via span._.bbox
        blocks = []
        for span in doc.spans.get("layout", []):
            blocks.append({
                "label": span.label_,
                "text": str(span.text),
                "bbox": getattr(span._, "bbox", None),
                "page": getattr(span._, "page_num", None),
                "heading": getattr(span._, "heading", None),
            })

        # Consolidate text under nearest heading
        grouped: Dict[str, List[str]] = {}
        for b in blocks:
            if b["label"].lower() == "heading":
                current = normalize_heading(b["text"])
                grouped.setdefault(current, [])
            else:
                current = normalize_heading(b.get("heading") or "Other")
                grouped.setdefault(current, []).append((b.get("text") or "").strip())

        for key, parts in grouped.items():
            groups.append({"section": key, "text": "\n".join([p for p in parts if p])})

        return doc, groups
