from pydantic import BaseModel
from typing import Optional, List

class DocumentOut(BaseModel):
    id: int
    title: str
    filename: str
    has_text_layer: bool

class UploadResponse(BaseModel):
    document: DocumentOut
    ingest_started: bool

class AskRequest(BaseModel):
    question: str
    source_ids: Optional[List[int]] = None  # None => all
    top_k: int = 8

class CitationOut(BaseModel):
    document_id: int
    document: str
    section: Optional[str] = None
    pages: str
    excerpt: str

class EvidenceOut(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    section_path: Optional[str] = None
    page_start: int
    page_end: int
    excerpt: str

class AskResponse(BaseModel):
    answer: str
    citations: List[CitationOut]
    evidence: List[EvidenceOut]

class LLMSettingsUpdate(BaseModel):
    chat_base_url: Optional[str] = None
    chat_api_key: Optional[str] = None
    chat_model: Optional[str] = None

class LLMSettingsOut(BaseModel):
    chat_base_url: str
    chat_model: str
