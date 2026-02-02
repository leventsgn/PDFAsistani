import fitz  # PyMuPDF
from typing import List, Tuple

def extract_pages_text(pdf_path: str) -> Tuple[bool, List[Tuple[int, str]]]:
    """Returns: (has_text_layer, [(page_no, text), ...])"""
    doc = fitz.open(pdf_path)
    pages = []
    any_text = False
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text") or ""
        text = text.strip()
        if text:
            any_text = True
        pages.append((i + 1, text))
    doc.close()
    return any_text, pages
