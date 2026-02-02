"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import type { ChangeEvent, MouseEvent } from "react";

// Render'da NEXT_PUBLIC_API_URL sadece hostname döner, https:// ekle
const apiHost = process.env.NEXT_PUBLIC_API_URL;
const API_BASE = apiHost 
  ? (apiHost.startsWith("http") ? apiHost : `https://${apiHost}`)
  : (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000");

type Doc = {
  id: number;
  title: string;
  filename: string;
  has_text_layer: boolean;
};

type Citation = {
  document_id: number;
  document: string;
  section?: string | null;
  pages: string;
  excerpt: string;
};

const themes = {
  light: {
    bg: "linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%)",
    cardBg: "#ffffff",
    cardBorder: "#e2e8f0",
    cardShadow: "0 4px 24px rgba(0, 0, 0, 0.06)",
    text: "#1e293b",
    textSecondary: "#64748b",
    textMuted: "#94a3b8",
    accent: "#6366f1",
    accentLight: "#eef2ff",
    accentBorder: "#c7d2fe",
    success: "#10b981",
    successBg: "#ecfdf5",
    successBorder: "#a7f3d0",
    danger: "#ef4444",
    dangerBg: "#fef2f2",
    dangerBorder: "#fecaca",
    inputBg: "#ffffff",
    inputBorder: "#e2e8f0",
    divider: "#e2e8f0",
    dividerHover: "#c7d2fe",
  },
  dark: {
    bg: "linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)",
    cardBg: "#1e293b",
    cardBorder: "#334155",
    cardShadow: "0 4px 24px rgba(0, 0, 0, 0.4)",
    text: "#f1f5f9",
    textSecondary: "#94a3b8",
    textMuted: "#64748b",
    accent: "#818cf8",
    accentLight: "#312e81",
    accentBorder: "#4f46e5",
    success: "#34d399",
    successBg: "#064e3b",
    successBorder: "#10b981",
    danger: "#f87171",
    dangerBg: "#450a0a",
    dangerBorder: "#dc2626",
    inputBg: "#0f172a",
    inputBorder: "#334155",
    divider: "#334155",
    dividerHover: "#4f46e5",
  },
};

export default function Home() {
  const suggestedQuestions = [
    "Dusmanı niteleme",
    "Barıs yapma yolları",
    "Nicin savasılır",
    "Osmanlı askerinin ozellikleri",
    "Osmanlıya gore savas nedir",
    "Osmanlıya gore barıs nedir",
  ];

  const [docs, setDocs] = useState<Doc[]>([]);
  const [uploading, setUploading] = useState(false);
  const [question, setQuestion] = useState("");
  const [sourceIds, setSourceIds] = useState<number[]>([]);
  const [answer, setAnswer] = useState<string>("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [asking, setAsking] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [selectedPage, setSelectedPage] = useState<number>(1);
  const [darkMode, setDarkMode] = useState(false);
  const [leftWidth, setLeftWidth] = useState(50);
  const [dragging, setDragging] = useState(false);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const theme = darkMode ? themes.dark : themes.light;

  const onMouseDown = useCallback((e: MouseEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  useEffect(() => {
    const onMouseMove = (e: globalThis.MouseEvent) => {
      if (!dragging || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const percent = (x / rect.width) * 100;
      setLeftWidth(Math.min(Math.max(percent, 25), 75));
    };
    const onMouseUp = () => setDragging(false);
    if (dragging) {
      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);
    }
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, [dragging]);

  useEffect(() => {
    const saved = localStorage.getItem("theme");
    if (saved === "dark") setDarkMode(true);
  }, []);

  useEffect(() => {
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  async function refreshDocs() {
    try {
      const r = await fetch(API_BASE + "/documents");
      const data = await r.json();
      setDocs(data);
    } catch (e) {
      console.error("Failed to fetch documents:", e);
    }
  }

  useEffect(() => { refreshDocs(); }, []);

  useEffect(() => {
    if (!selectedDocId && docs.length) {
      setSelectedDocId(docs[0].id);
      setSelectedPage(1);
    }
  }, [docs, selectedDocId]);

  async function onUpload(ev: ChangeEvent<HTMLInputElement>) {
    const file = ev.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await fetch(API_BASE + "/upload", { method: "POST", body: fd });
      if (!r.ok) throw new Error(await r.text());
      await refreshDocs();
      ev.target.value = "";
    } catch (e: any) {
      alert(e?.message || String(e));
    } finally {
      setUploading(false);
    }
  }

  async function onAsk() {
    if (!question.trim()) return;
    setAsking(true);
    setAnswer("");
    setCitations([]);
    try {
      const payload: any = { question, top_k: 8 };
      if (sourceIds.length) payload.source_ids = sourceIds;
      const r = await fetch(API_BASE + "/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setAnswer(data.answer || "");
      setCitations(data.citations || []);
    } catch (e: any) {
      alert(e?.message || String(e));
    } finally {
      setAsking(false);
    }
  }

  async function askSuggestion(text: string) {
    setQuestion(text);
    setTimeout(() => onAsk(), 100);
  }

  async function onDelete(docId: number) {
    if (!confirm("Bu PDF silinsin mi?")) return;
    try {
      const r = await fetch(API_BASE + "/documents/" + docId, { method: "DELETE" });
      if (!r.ok) throw new Error(await r.text());
      await refreshDocs();
      if (selectedDocId === docId) {
        setSelectedDocId(null);
        setSelectedPage(1);
      }
    } catch (e: any) {
      alert(e?.message || String(e));
    }
  }

  function toggleSource(id: number) {
    setSourceIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  function openCitation(docId: number, page: number) {
    setSelectedDocId(docId);
    setSelectedPage(page);
  }

  const selectedDoc = docs.find((d) => d.id === selectedDocId) || null;
  const pdfUrl = selectedDoc ? API_BASE + "/files/" + selectedDoc.id + "#page=" + selectedPage : "";

  const cardStyle: React.CSSProperties = {
    padding: 20,
    borderRadius: 16,
    background: theme.cardBg,
    border: "1.5px solid " + theme.cardBorder,
    boxShadow: theme.cardShadow,
    transition: "all 0.2s ease",
  };

  const btnPrimary: React.CSSProperties = {
    padding: "12px 24px",
    borderRadius: 12,
    border: "none",
    background: "linear-gradient(135deg, " + theme.accent + " 0%, #4f46e5 100%)",
    color: "#fff",
    fontWeight: 600,
    fontSize: 15,
    cursor: "pointer",
    boxShadow: "0 4px 16px " + theme.accent + "40",
    transition: "all 0.2s ease",
  };

  const btnSecondary: React.CSSProperties = {
    padding: "10px 18px",
    borderRadius: 10,
    border: "1.5px solid " + theme.accentBorder,
    background: theme.accentLight,
    color: theme.accent,
    fontWeight: 600,
    fontSize: 14,
    cursor: "pointer",
    transition: "all 0.2s ease",
  };

  const btnDanger: React.CSSProperties = {
    padding: "10px 18px",
    borderRadius: 10,
    border: "1.5px solid " + theme.dangerBorder,
    background: theme.dangerBg,
    color: theme.danger,
    fontWeight: 600,
    fontSize: 14,
    cursor: "pointer",
    transition: "all 0.2s ease",
  };

  const btnSuggestion: React.CSSProperties = {
    padding: "8px 16px",
    borderRadius: 20,
    border: "1.5px solid " + theme.accentBorder,
    background: theme.accentLight,
    color: theme.accent,
    fontWeight: 600,
    fontSize: 13,
    cursor: "pointer",
    transition: "all 0.15s ease",
  };

  const inputStyle: React.CSSProperties = {
    flex: 1,
    padding: "14px 18px",
    border: "1.5px solid " + theme.inputBorder,
    borderRadius: 12,
    fontSize: 15,
    outline: "none",
    background: theme.inputBg,
    color: theme.text,
    transition: "all 0.15s ease",
  };

  return (
    <div
      ref={containerRef}
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        background: theme.bg,
      }}
    >
      {/* Header */}
      <div style={{
        padding: "12px 20px",
        borderBottom: "1px solid " + theme.cardBorder,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        background: theme.cardBg,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <b style={{ color: theme.text, fontSize: 16 }}>Osmanlica Arsiv</b>
          <span style={{ color: theme.textSecondary, fontSize: 14 }}>PDF Soru-Cevap Sistemi</span>
        </div>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <a href="/" style={{ color: theme.accent, textDecoration: "none", fontSize: 14, fontWeight: 500 }}>Ana Sayfa</a>
          <a href="/settings" style={{ color: theme.accent, textDecoration: "none", fontSize: 14, fontWeight: 500 }}>Ayarlar</a>
          <button
            onClick={() => setDarkMode(!darkMode)}
            style={{
              padding: "8px 14px",
              borderRadius: 10,
              border: "1.5px solid " + theme.cardBorder,
              background: theme.accentLight,
              color: theme.accent,
              fontWeight: 600,
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            {darkMode ? "Light" : "Dark"}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div
        style={{
          display: "flex",
          flex: 1,
          padding: 16,
          gap: 0,
          userSelect: dragging ? "none" : "auto",
        }}
      >
      <div
        style={{
          width: leftWidth + "%",
          display: "flex",
          flexDirection: "column",
          gap: 16,
          paddingRight: 8,
          overflowY: "auto",
          maxHeight: "calc(100vh - 60px)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800, color: theme.text }}>
            Osmanlica PDF Asistani
          </h1>
        </div>

        <div style={{ ...cardStyle, background: "linear-gradient(135deg, " + theme.accentLight + " 0%, " + theme.cardBg + " 80%)", borderColor: theme.accentBorder }}>
          <h2 style={{ marginTop: 0, marginBottom: 16, fontSize: 18, color: theme.text, fontWeight: 700 }}>
            PDF Yukle
          </h2>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <label style={{ ...btnSecondary, display: "inline-flex", alignItems: "center", gap: 8 }}>
              <span>Dosya Sec</span>
              <input type="file" accept="application/pdf" onChange={onUpload} disabled={uploading} style={{ display: "none" }} />
            </label>
            {uploading && <span style={{ color: theme.accent, fontSize: 14, fontWeight: 500 }}>Yukleniyor...</span>}
          </div>
        </div>

        <div style={cardStyle}>
          <div 
            onClick={() => setSourcesOpen(!sourcesOpen)}
            style={{ 
              display: "flex", 
              justifyContent: "space-between", 
              alignItems: "center", 
              cursor: "pointer",
              marginBottom: sourcesOpen ? 16 : 0,
            }}
          >
            <h2 style={{ margin: 0, fontSize: 18, color: theme.text, fontWeight: 700 }}>
              Kaynaklar ({docs.length})
            </h2>
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: 8,
              color: theme.textSecondary,
              fontSize: 14,
            }}>
              {sourceIds.length > 0 && (
                <span style={{ 
                  background: theme.accent, 
                  color: "#fff", 
                  padding: "2px 8px", 
                  borderRadius: 10, 
                  fontSize: 12 
                }}>
                  {sourceIds.length} secili
                </span>
              )}
              <span style={{ 
                transform: sourcesOpen ? "rotate(180deg)" : "rotate(0deg)", 
                transition: "transform 0.2s ease",
                fontSize: 18,
              }}>
                ▼
              </span>
            </div>
          </div>
          {sourcesOpen && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 300, overflowY: "auto" }}>
            {docs.map((d) => (
              <div
                key={d.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: 12,
                  border: selectedDocId === d.id ? "2px solid " + theme.accent : "1.5px solid " + theme.cardBorder,
                  borderRadius: 12,
                  background: selectedDocId === d.id ? theme.accentLight : theme.cardBg,
                  transition: "all 0.2s ease",
                }}
              >
                <input
                  type="checkbox"
                  checked={sourceIds.includes(d.id)}
                  onChange={() => toggleSource(d.id)}
                  style={{ width: 18, height: 18, accentColor: theme.accent, cursor: "pointer" }}
                />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 14, color: theme.text, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {d.title}
                  </div>
                  <div style={{ color: theme.textSecondary, fontSize: 12 }}>
                    #{d.id}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  <button onClick={() => openCitation(d.id, 1)} style={{ ...btnSecondary, padding: "8px 12px", fontSize: 12 }}>Goster</button>
                  <button onClick={() => onDelete(d.id)} style={{ ...btnDanger, padding: "8px 12px", fontSize: 12 }}>Sil</button>
                </div>
              </div>
            ))}
            {!docs.length && <div style={{ color: theme.textMuted, fontSize: 14, textAlign: "center", padding: 20 }}>Henuz PDF yuklenmedi</div>}
          </div>
          )}
        </div>

        <div style={{ ...cardStyle, borderColor: theme.accentBorder }}>
          <h2 style={{ marginTop: 0, marginBottom: 16, fontSize: 18, color: theme.text, fontWeight: 700 }}>Soru Sor</h2>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
            {suggestedQuestions.map((q) => (
              <button key={q} onClick={() => askSuggestion(q)} style={btnSuggestion}>{q}</button>
            ))}
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onAsk()}
              placeholder="Ornegin: Osmanliya gore savas nedir?"
              style={inputStyle}
            />
            <button onClick={onAsk} disabled={asking} style={{ ...btnPrimary, opacity: asking ? 0.7 : 1 }}>
              {asking ? "..." : "Sor"}
            </button>
          </div>
          <div style={{ color: theme.textSecondary, fontSize: 13, marginTop: 10 }}>Kaynak secmezsen tum kaynaklarda arar</div>
        </div>

        {!!answer && (
          <div style={{ ...cardStyle, background: theme.successBg, borderColor: theme.successBorder }}>
            <div style={{ fontWeight: 700, marginBottom: 10, fontSize: 16, color: theme.success }}>Cevap</div>
            <div style={{ whiteSpace: "pre-wrap", color: theme.text, fontSize: 15, lineHeight: 1.7 }}>
              {answer.split(/(\[\d+\])/).map((part, i) => {
                const match = part.match(/\[(\d+)\]/);
                if (match) {
                  const refNum = parseInt(match[1]);
                  // ref alanına, index+1'e veya document_id'ye göre ara
                  const citation = citations.find((c: any) => 
                    c.ref === refNum || 
                    citations.indexOf(c) + 1 === refNum ||
                    c.document_id === refNum
                  );
                  if (citation) {
                    const pages = citation.pages.replace("s.", "");
                    const firstPage = Number(pages.split("-")[0] || "1");
                    return (
                      <button
                        key={i}
                        onClick={() => openCitation(citation.document_id, firstPage)}
                        style={{
                          background: theme.accent,
                          color: "#fff",
                          border: "none",
                          borderRadius: 4,
                          padding: "2px 6px",
                          fontSize: 13,
                          fontWeight: 600,
                          cursor: "pointer",
                          margin: "0 2px",
                          verticalAlign: "middle",
                        }}
                        title={citation.document + " - " + citation.pages}
                      >
                        {part}
                      </button>
                    );
                  }
                  // Citation bulunamadıysa bile butonu göster (stil farklı)
                  return (
                    <span
                      key={i}
                      style={{
                        background: theme.textMuted,
                        color: "#fff",
                        borderRadius: 4,
                        padding: "2px 6px",
                        fontSize: 13,
                        fontWeight: 600,
                        margin: "0 2px",
                      }}
                    >
                      {part}
                    </span>
                  );
                }
                return <span key={i}>{part}</span>;
              })}
            </div>
          </div>
        )}
      </div>

      <div
        onMouseDown={onMouseDown}
        style={{
          width: 8,
          cursor: "col-resize",
          background: dragging ? theme.accent : theme.divider,
          borderRadius: 4,
          margin: "0 4px",
          transition: dragging ? "none" : "background 0.2s ease",
          flexShrink: 0,
        }}
      />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", paddingLeft: 8, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12, padding: "0 4px" }}>
          <div style={{ fontWeight: 700, fontSize: 16, color: theme.text }}>
            {selectedDoc ? selectedDoc.title : "PDF Onizleme"}
          </div>
          <div
            style={{
              fontSize: 13,
              color: theme.accent,
              fontWeight: 600,
              background: theme.accentLight,
              padding: "6px 14px",
              borderRadius: 20,
              border: "1px solid " + theme.accentBorder,
            }}
          >
            Sayfa {selectedPage}
          </div>
        </div>
        <div
          style={{
            flex: 1,
            border: "2px solid " + theme.cardBorder,
            borderRadius: 16,
            overflow: "hidden",
            background: theme.cardBg,
            boxShadow: theme.cardShadow,
          }}
        >
          {pdfUrl ? (
            <iframe
              key={selectedDocId + "-" + selectedPage}
              src={pdfUrl}
              style={{ width: "100%", height: "100%", border: "0", minHeight: "calc(100vh - 100px)" }}
            />
          ) : (
            <div style={{ padding: 32, color: theme.textMuted, fontSize: 15, textAlign: "center" }}>
              PDF secin veya yukleyin
            </div>
          )}
        </div>
      </div>
      </div>
    </div>
  );
}
