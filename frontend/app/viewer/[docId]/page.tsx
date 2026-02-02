"use client";


import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
const PdfjsViewer = dynamic(() => import("./PdfjsViewer"), { ssr: false });

export default function Viewer({ params }: { params: { docId: string } }) {
  const sp = useSearchParams();
  const page = sp.get("page") || "1";
  const docId = params.docId;
  // TODO: highlight metni parametre olarak alınabilir
  const highlight = sp.get("highlight") || undefined;

  return (
    <div style={{ height: "calc(100vh - 110px)" }}>
      <div style={{ marginBottom: 10 }}>
        <a href="/" style={{ fontSize: 13 }}>← Geri</a>
        <span style={{ marginLeft: 12, color: "#666" }}>Doc #{docId} • Sayfa {page}</span>
      </div>
      <PdfjsViewer docId={docId} page={page} highlight={highlight ? { text: highlight } : undefined} />
      <div style={{ marginTop: 8, color: "#666", fontSize: 12 }}>
        Not: Highlight (cümle işaretleme) V2. Sarı ile işaretleme eklendi.
      </div>
    </div>
  );
}
