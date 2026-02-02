import httpx
from typing import List, Dict, Any
from .settings import get_chat_settings

SYSTEM = (
    "Sen akademik bir asistan olarak çalışıyorsun. "
    "SADECE verilen kanıt metinlerine dayanarak cevap ver. "
    "Kanıt yoksa 'Bu kaynaklarda bulunamadı' de. "
    "Kesinlikle uydurma bilgi ekleme. "
    "Yanıtları akademik, açıklayıcı ve bağlamlı bir üslupla yaz; "
    "kısa cümlelerle geçiştirme. "
    "En az üç cümle kur. "
    "Gerekirse 2-4 paragraf kullan, ancak kanıt dışına çıkma."
)

async def answer_with_citations(question: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    # evidence items: {document_title, section_path, page_start, page_end, excerpt}
    # Build compact context
    blocks = []
    for i, e in enumerate(evidence, start=1):
        sec = e.get("section_path") or ""
        pages = f"s.{e['page_start']}" if e["page_start"] == e["page_end"] else f"s.{e['page_start']}-{e['page_end']}"
        header = f"[{i}] {e['document_title']} | {sec} | {pages}"
        blocks.append(header + "\n" + e["excerpt"])
    context = "\n\n".join(blocks) if blocks else "(KANIT YOK)"

    user = (
        f"Soru: {question}\n\n"
        f"KANIT METİNLERİ:\n{context}\n\n"
        "ÖNEMLİ KURALLAR:\n"
        "1. Sadece JSON formatında yanıt ver, başka hiçbir şey yazma.\n"
        "2. Cevabında referansları [1], [2] şeklinde göster (KANIT METİNLERİ yazma).\n"
        "3. Yanıt akademik ve açıklayıcı olsun, en az 3 paragraf yaz.\n\n"
        "JSON formatı:\n"
        "{\n"
        '  "answer": "Cevap metni burada... [1] referansı... [2] referansı...",\n'
        '  "citations": [\n'
        '    {"ref": 1, "document": "Belge adı", "section": "Bölüm", "pages": "s.X-Y", "excerpt": "Alıntı..."}\n'
        "  ]\n"
        "}\n"
    )

    chat_settings = get_chat_settings()
    url = chat_settings["chat_base_url"].rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {chat_settings['chat_api_key']}"}
    payload = {
        "model": chat_settings["chat_model"],
        "temperature": 0.2,
        "max_tokens": 2000,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"]
    except Exception:
        if not evidence:
            return {"answer": "Bu kaynaklarda bulunamadı", "citations": []}

        citations = []
        for e in evidence:
            pages = f"s.{e['page_start']}" if e["page_start"] == e["page_end"] else f"s.{e['page_start']}-{e['page_end']}"
            citations.append({
                "document_id": e["document_id"],
                "document": e["document_title"],
                "section": e.get("section_path"),
                "pages": pages,
                "excerpt": e.get("excerpt") or e.get("chunk_text") or "",
            })
        return {"answer": "LLM erişilemedi. Kanıtlar aşağıda listelenmiştir.", "citations": citations}
    # Best-effort JSON parse - try to extract JSON from mixed content
    import json
    import re
    
    parsed = None
    content = content.strip()
    
    # Markdown code block içindeki JSON'u çıkar
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
    if code_block_match:
        content = code_block_match.group(1).strip()
    
    # İlk olarak direkt JSON parse dene
    try:
        parsed = json.loads(content)
    except Exception:
        # { ile başlayıp } ile biten kısmı bul (en dış JSON objesi)
        brace_start = content.find('{')
        brace_end = content.rfind('}')
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            json_str = content[brace_start:brace_end + 1]
            try:
                parsed = json.loads(json_str)
            except Exception:
                # JSON kesilmiş olabilir, answer kısmını çıkarmaya çalış
                answer_match = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', json_str)
                if answer_match:
                    parsed = {"answer": answer_match.group(1), "citations": []}
    
    if not parsed:
        # Hala parse edemediyse, düz metin olarak kullan
        clean_answer = re.sub(r'KANIT METİNLERİ \[(\d+)\]', r'[\1]', content)
        clean_answer = re.sub(r'\{[\s\S]*$', '', clean_answer).strip()  # Yarım JSON'u sil
        return {"answer": clean_answer if clean_answer else content, "citations": []}

    answer = parsed.get("answer", "") if isinstance(parsed, dict) else ""
    raw_citations = parsed.get("citations", []) if isinstance(parsed, dict) else []

    # Normalize citations strictly from provided evidence to avoid hallucination
    evidence_map = {i + 1: e for i, e in enumerate(evidence)}
    citations = []
    for c in raw_citations or []:
        if not isinstance(c, dict):
            continue
        ref = c.get("ref")
        if isinstance(ref, int) and ref in evidence_map:
            e = evidence_map[ref]
            pages = f"s.{e['page_start']}" if e["page_start"] == e["page_end"] else f"s.{e['page_start']}-{e['page_end']}"
            citations.append({
                "ref": ref,  # Frontend için ref numarasını ekle
                "document_id": e["document_id"],
                "document": e["document_title"],
                "section": e.get("section_path"),
                "pages": pages,
                "excerpt": e.get("excerpt") or e.get("chunk_text") or "",
            })

    return {"answer": answer, "citations": citations}
