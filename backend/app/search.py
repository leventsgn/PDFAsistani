from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any

def fts_search(db: Session, question: str, source_ids: Optional[List[int]] = None, limit: int = 10) -> List[Dict[str, Any]]:
    # plainto_tsquery('turkish', :q)
    tokens = [t for t in (question or "").split() if len(t) >= 3]
    patterns = [f"%{t}%" for t in tokens[:8]]
    rows = []
    try:
        if source_ids:
            sql = text("""
                SELECT c.id, c.document_id, c.section_path, c.page_start, c.page_end, c.chunk_text,
                       d.title as document_title
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.document_id = ANY(:source_ids)
                  AND c.fts @@ plainto_tsquery('turkish', :q)
                ORDER BY ts_rank(c.fts, plainto_tsquery('turkish', :q)) DESC
                LIMIT :lim
            """)
            rows = db.execute(sql, {"q": question, "lim": limit, "source_ids": source_ids}).mappings().all()
        else:
            sql = text("""
                SELECT c.id, c.document_id, c.section_path, c.page_start, c.page_end, c.chunk_text,
                       d.title as document_title
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.fts @@ plainto_tsquery('turkish', :q)
                ORDER BY ts_rank(c.fts, plainto_tsquery('turkish', :q)) DESC
                LIMIT :lim
            """)
            rows = db.execute(sql, {"q": question, "lim": limit}).mappings().all()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass

    # Fallback: simple ILIKE search if FTS is unavailable or returns no rows
    if not rows:
        if not patterns:
            patterns = [f"%{question}%"] if question else []
        if source_ids:
            sql = text("""
                SELECT c.id, c.document_id, c.section_path, c.page_start, c.page_end, c.chunk_text,
                       d.title as document_title
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.document_id = ANY(:source_ids)
                  AND c.chunk_text ILIKE ANY(:patterns)
                ORDER BY c.id DESC
                LIMIT :lim
            """)
            rows = db.execute(sql, {"patterns": patterns, "lim": limit, "source_ids": source_ids}).mappings().all()
        else:
            sql = text("""
                SELECT c.id, c.document_id, c.section_path, c.page_start, c.page_end, c.chunk_text,
                       d.title as document_title
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.chunk_text ILIKE ANY(:patterns)
                ORDER BY c.id DESC
                LIMIT :lim
            """)
            rows = db.execute(sql, {"patterns": patterns, "lim": limit}).mappings().all()

    out = []
    for r in rows:
        excerpt = (r["chunk_text"][:1200]).strip()
        out.append({
            "chunk_id": r["id"],
            "document_id": r["document_id"],
            "document_title": r["document_title"],
            "section_path": r["section_path"],
            "page_start": r["page_start"],
            "page_end": r["page_end"],
            "excerpt": excerpt
        })
    return out

def vector_search(
    db: Session,
    query_embedding: Optional[List[float]],
    source_ids: Optional[List[int]] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    if not query_embedding:
        return []

    if source_ids:
        sql = text("""
            SELECT c.id, c.document_id, c.section_path, c.page_start, c.page_end, c.chunk_text,
                   d.title as document_title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.document_id = ANY(:source_ids)
              AND c.embedding IS NOT NULL
            ORDER BY c.embedding <-> :qvec
            LIMIT :lim
        """)
        rows = db.execute(sql, {"qvec": query_embedding, "lim": limit, "source_ids": source_ids}).mappings().all()
    else:
        sql = text("""
            SELECT c.id, c.document_id, c.section_path, c.page_start, c.page_end, c.chunk_text,
                   d.title as document_title
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL
            ORDER BY c.embedding <-> :qvec
            LIMIT :lim
        """)
        rows = db.execute(sql, {"qvec": query_embedding, "lim": limit}).mappings().all()

    out = []
    for r in rows:
        excerpt = (r["chunk_text"][:1200]).strip()
        out.append({
            "chunk_id": r["id"],
            "document_id": r["document_id"],
            "document_title": r["document_title"],
            "section_path": r["section_path"],
            "page_start": r["page_start"],
            "page_end": r["page_end"],
            "excerpt": excerpt
        })
    return out

def hybrid_search(
    db: Session,
    question: str,
    query_embedding: Optional[List[float]] = None,
    source_ids: Optional[List[int]] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    fts = fts_search(db, question, source_ids=source_ids, limit=limit)
    vec = vector_search(db, query_embedding, source_ids=source_ids, limit=limit)

    combined = []
    seen = set()
    for r in fts + vec:
        if r["chunk_id"] in seen:
            continue
        seen.add(r["chunk_id"])
        combined.append(r)
        if len(combined) >= limit:
            break
    return combined
