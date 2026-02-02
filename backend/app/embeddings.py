from typing import List, Optional
import httpx
from .settings import settings

async def embed_texts(texts: List[str]) -> Optional[List[List[float]]]:
    """Optional embeddings. Returns None if provider=none."""
    if settings.embeddings_provider.lower() == "none":
        return None

    # OpenAI-compatible embeddings endpoint: POST /embeddings
    url = settings.openai_base_url.rstrip("/") + "/embeddings"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    payload = {"model": settings.openai_model, "input": texts}

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        # Expect: {"data":[{"embedding":[...],...},...]}
        return [d["embedding"] for d in data["data"]]
