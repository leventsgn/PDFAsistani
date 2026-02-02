from typing import List, Dict

def chunk_pages(pages: List[Dict], max_chars: int = 1800) -> List[Dict]:
    """Very simple paragraph chunker.
    pages: [{page_no:int, text:str}, ...]
    Returns chunks with page_start/page_end and chunk_text.
    """
    chunks = []
    buf = []
    buf_len = 0
    page_start = None
    last_page = None

    def flush():
        nonlocal buf, buf_len, page_start, last_page
        if not buf:
            return
        chunk_text = "\n\n".join(buf).strip()
        if chunk_text:
            chunks.append({
                "page_start": page_start,
                "page_end": last_page,
                "section_path": None,
                "chunk_text": chunk_text
            })
        buf = []
        buf_len = 0
        page_start = None
        last_page = None

    for p in pages:
        page_no = p["page_no"]
        text = (p.get("text") or "").strip()
        if not text:
            continue
        paras = [x.strip() for x in text.split("\n\n") if x.strip()]
        for para in paras:
            if page_start is None:
                page_start = page_no
            last_page = page_no
            if buf_len + len(para) > max_chars:
                flush()
                page_start = page_no
                last_page = page_no
            buf.append(para)
            buf_len += len(para)

    flush()
    return chunks
