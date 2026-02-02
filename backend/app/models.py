from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, Index, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List
from pgvector.sqlalchemy import Vector
from .settings import settings
from .db import Base

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=True)  # Local path (optional)
    file_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)  # PDF binary for cloud

    has_text_layer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ocr_status: Mapped[str] = mapped_column(String(32), nullable=False, default="none")  # none|queued|running|done|failed

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

class Page(Base):
    __tablename__ = "pages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_no: Mapped[int] = mapped_column(Integer, nullable=False)

    text_raw: Mapped[str] = mapped_column(Text, nullable=True)
    ocr_text: Mapped[str] = mapped_column(Text, nullable=True)  # V2

    document = relationship("Document", back_populates="pages")

    __table_args__ = (
        Index("ix_pages_doc_page", "document_id", "page_no", unique=True),
    )

class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    # “bölüm” tespiti MVP’de basit: section_path boş olabilir.
    section_path: Mapped[str] = mapped_column(String(1024), nullable=True)

    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)

    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(settings.embedding_dim), nullable=True)

    # Postgres FTS için tsvector sütunu SQL ile eklenir (migrate.sql).
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("ix_chunks_doc_pages", "document_id", "page_start", "page_end"),
    )
