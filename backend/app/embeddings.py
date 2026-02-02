from typing import List, Optional
import httpx
from .settings import settings

async def embed_texts(texts: List[str]) -> Optional[List[List[float]]]:
    """Optional embeddings. Returns None if provider=none or no API key."""
    if settings.embeddings_provider.lower() == "none":
        return None
    
    # Check if API key is set
    if not settings.openai_api_key or settings.openai_api_key.strip() == "":
        print("Warning: EMBEDDING_API_KEY not set, using FTS only")
        return None

    # OpenAI-compatible embeddings endpoint: POST /embeddings
    url = settings.openai_base_url.rstrip("/") + "/embeddings"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    payload = {"model": settings.openai_model, "input": texts}

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            # Expect: {"data":[{"embedding":[...],...},...]}
            return [d["embedding"] for d in data["data"]]
    except Exception as e:
        print(f"Embedding error: {e}, falling back to FTS only")
        return None
