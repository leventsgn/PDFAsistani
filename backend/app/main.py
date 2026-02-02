import os
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .models import Document, Page, Chunk
from .settings import settings, get_chat_settings, update_chat_settings
from .schemas import UploadResponse, DocumentOut, AskRequest, AskResponse, LLMSettingsOut, LLMSettingsUpdate
from .pdf_extract import extract_pages_text
from .chunking import chunk_pages
from .search import fts_search, hybrid_search
from .embeddings import embed_texts
from .llm import answer_with_citations

app = FastAPI(title="TEXT-ONLY RAG Backend", version="0.1.0")

# CORS - Allow frontend origins
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
# Add Render frontend URL if set
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)
# Allow all origins in production (Render)
if os.getenv("RENDER"):
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    os.makedirs(settings.files_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/settings", response_model=LLMSettingsOut)
def get_settings():
    chat = get_chat_settings()
    return LLMSettingsOut(chat_base_url=chat["chat_base_url"], chat_model=chat["chat_model"])

@app.post("/settings", response_model=LLMSettingsOut)
def update_settings(payload: LLMSettingsUpdate):
    updated = update_chat_settings(payload.model_dump(exclude_none=True))
    chat = get_chat_settings()
    return LLMSettingsOut(chat_base_url=chat["chat_base_url"], chat_model=chat["chat_model"])

@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")

    safe_name = file.filename.replace("/", "_").replace("\\", "_")
    doc_dir = os.path.join(settings.files_dir, "pdfs")
    os.makedirs(doc_dir, exist_ok=True)
    path = os.path.join(doc_dir, safe_name)

    # Write file
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    # Create doc record
    doc = Document(title=os.path.splitext(safe_name)[0], filename=safe_name, file_path=os.path.abspath(path))
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Ingest synchronously (MVP). Later: background queue
    has_text_layer, pages = extract_pages_text(doc.file_path)
    doc.has_text_layer = bool(has_text_layer)
    db.add(doc)

    # Store pages
    for page_no, text in pages:
        p = Page(document_id=doc.id, page_no=page_no, text_raw=text if text else None)
        db.add(p)

    # Create chunks only if some text exists
    ingest_started = False
    if has_text_layer:
        page_objs = [{"page_no": pn, "text": t} for pn, t in pages if t and t.strip()]
        chunks = chunk_pages(page_objs, max_chars=1800)
        embeddings = await embed_texts([c["chunk_text"] for c in chunks]) if chunks else None
        for idx, c in enumerate(chunks):
            ch = Chunk(
                document_id=doc.id,
                section_path=c.get("section_path"),
                page_start=c["page_start"],
                page_end=c["page_end"],
                chunk_text=c["chunk_text"],
                embedding=(embeddings[idx] if embeddings else None),
            )
            db.add(ch)
        ingest_started = True

    db.commit()
    db.refresh(doc)

    return UploadResponse(
        document=DocumentOut(
            id=doc.id, title=doc.title, filename=doc.filename,
            has_text_layer=doc.has_text_layer
        ),
        ingest_started=ingest_started
    )

@app.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.id.desc()).all()
    return [DocumentOut(id=d.id, title=d.title, filename=d.filename, has_text_layer=d.has_text_layer) for d in docs]

@app.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    file_path = doc.file_path
    db.delete(doc)
    db.commit()
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass
    return {"deleted": True}

@app.get("/files/{doc_id}")
def get_pdf(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    headers = {"Content-Disposition": f"inline; filename=\"{doc.filename}\""}
    return FileResponse(
        doc.file_path,
        media_type="application/pdf",
        headers=headers,
    )

@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest, db: Session = Depends(get_db)):
    # Evidence retrieval: FTS MVP
    query_embedding = None
    embedding_list = await embed_texts([req.question])
    if embedding_list:
        query_embedding = embedding_list[0]

    evidence = hybrid_search(
        db,
        req.question,
        query_embedding=query_embedding,
        source_ids=req.source_ids,
        limit=max(3, min(req.top_k, 12)),
    )

    if not evidence:
        return AskResponse(
            answer="Bu kaynaklarda bulunamadı",
            citations=[],
            evidence=[]
        )

    llm = await answer_with_citations(req.question, evidence)

    answer = llm.get("answer", "")
    if not answer or not answer.strip():
        return AskResponse(
            answer="Bu kaynaklarda bulunamadı",
            citations=[],
            evidence=[]
        )

    citations = llm.get("citations", [])

    if not citations:
        citations = [
            {
                "document_id": e["document_id"],
                "document": e["document_title"],
                "section": e.get("section_path"),
                "pages": f"s.{e['page_start']}" if e["page_start"] == e["page_end"] else f"s.{e['page_start']}-{e['page_end']}",
                "excerpt": e.get("excerpt", ""),
            }
            for e in evidence
        ]

    return AskResponse(
        answer=answer,
        citations=citations,
        evidence=evidence
    )

@app.post("/reindex")
async def reindex_embeddings(doc_id: int | None = None, batch_size: int = 32, db: Session = Depends(get_db)):
    if settings.embeddings_provider.lower() == "none":
        raise HTTPException(400, "Embeddings provider is disabled")

    query = db.query(Chunk).filter(Chunk.embedding.is_(None))
    if doc_id is not None:
        query = query.filter(Chunk.document_id == doc_id)

    total = query.count()
    updated = 0

    offset = 0
    while offset < total:
        batch = query.order_by(Chunk.id).offset(offset).limit(batch_size).all()
        if not batch:
            break
        embeddings = await embed_texts([c.chunk_text for c in batch])
        if not embeddings:
            break
        for c, emb in zip(batch, embeddings):
            c.embedding = emb
            updated += 1
        db.commit()
        offset += batch_size

    return {"updated": updated}
