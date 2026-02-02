# Osmanlı / Tez PDF RAG (TEXT-ONLY) — Starter Project

Bu proje, **OCR olmadan** (yalnızca PDF içindeki **text layer** üzerinden) çalışır:
- PDF yükle
- Metni sayfa numarasıyla çıkar
- Chunk’la, Postgres’e yaz
- Soru sor → **cevap + kaynaklar (PDF / bölüm / sayfa)** döndür
- Kaynağa tıkla → orijinal PDF ilgili sayfada açılır

> OCR kullanılmaz. Sistem yalnızca PDF text layer üzerinden çalışır.

---

## 0) Gereksinimler
- Docker + Docker Compose
- Node.js >= 18
- Python >= 3.10

---

## 1) Çalıştırma (local)

### A) Postgres (pgvector dahil)
```bash
cd infra
docker compose up -d
```

### B) Backend (FastAPI)
```bash
cd backend
python -m venv .venv
# Windows:
# .venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### C) Frontend (Next.js)
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Adminer: http://localhost:8080

---

## 2) Ortam Değişkenleri

### Backend (`backend/.env`)
- `DATABASE_URL=postgresql+psycopg://rag:rag@localhost:5432/rag`
- `FILES_DIR=../storage` (PDF’lerin saklanacağı klasör)
- `EMBEDDINGS_PROVIDER=none|openai_compatible`  (MVP’de `none` bırak)
- `OPENAI_BASE_URL=http://localhost:11434/v1` (OpenAI compatible)
- `OPENAI_API_KEY=...`
- `OPENAI_MODEL=text-embedding-3-small`
- `EMBEDDING_DIM=1536`

**Cevaplama için LLM (OpenAI-compatible):**
- `CHAT_BASE_URL=http://localhost:11434/v1`
- `CHAT_API_KEY=...`
- `CHAT_MODEL=gpt-oss-20b`

### Frontend (`frontend/.env.local`)
- `NEXT_PUBLIC_API_BASE=http://localhost:8000`

---

## 3) Notlar / Kapsam
- **TEXT-ONLY**: Tarama/görsel PDF’lerde `has_text_layer=false` olur. Sistem bu PDF’leri “text layer yok” olarak gösterir.
- Arama: MVP’de **Postgres Full-Text Search** (FTS) var.
- Embedding & vektör arama: iskelet hazır; `EMBEDDINGS_PROVIDER=openai_compatible` ile eklenebilir.
	- Vektör arama için embeddings sağlayıcısı zorunlu; mevcut chunk’lar için `/reindex` çağrısı gerekir.

---

## 4) Yol Haritası (V2)
- (İsteğe bağlı) OCR entegrasyonu yapılmayacak.
- Highlight (text-layer search veya bbox)
- Multi-tenant & RBAC
- Vector + rerank (hybrid)

