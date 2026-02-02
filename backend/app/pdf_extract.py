import fitz  # PyMuPDF
from typing import List, Tuple, Union
import io

def extract_pages_text(pdf_source: Union[str, io.BytesIO]) -> Tuple[bool, List[Tuple[int, str]]]:
    """
    Extract text from PDF pages.
    pdf_source can be a file path (str) or BytesIO object.
    Returns: (has_text_layer, [(page_no, text), ...])
    """
    if isinstance(pdf_source, io.BytesIO):
        doc = fitz.open(stream=pdf_source.read(), filetype="pdf")
    else:
        doc = fitz.open(pdf_source)
    
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
