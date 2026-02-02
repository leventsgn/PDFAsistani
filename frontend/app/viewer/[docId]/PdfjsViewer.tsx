
import { useEffect, useRef } from "react";
import "pdfjs-dist/web/pdf_viewer.css";

// Render'da NEXT_PUBLIC_API_URL sadece hostname döner, https:// ekle
const apiHost = process.env.NEXT_PUBLIC_API_URL;
const API_BASE = apiHost 
  ? (apiHost.startsWith("http") ? apiHost : `https://${apiHost}`)
  : (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000");

export default function PdfjsViewer({ docId, page, highlight }: { docId: string; page: number|string; highlight?: { text: string } }) {
  const containerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let pdfjsLib: any;
    let pdfjsViewer: any;
    let pdfDoc: any;
    let pdfLinkService: any;
    let pdfViewer: any;
    let destroyed = false;

    async function load() {
      // @ts-ignore
      pdfjsLib = await import("pdfjs-dist/legacy/build/pdf");
      // @ts-ignore
      pdfjsViewer = await import("pdfjs-dist/legacy/web/pdf_viewer");
      pdfjsLib.GlobalWorkerOptions.workerSrc =
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.2.67/pdf.worker.min.js";
      const url = `${API_BASE}/files/${docId}`;
      pdfDoc = await pdfjsLib.getDocument(url).promise;
      if (destroyed) return;
      const eventBus = new pdfjsViewer.EventBus();
      pdfLinkService = new pdfjsViewer.PDFLinkService({ eventBus });
      pdfViewer = new pdfjsViewer.PDFViewer({
        container: containerRef.current,
        eventBus,
        linkService: pdfLinkService,
      });
      pdfLinkService.setViewer(pdfViewer);
      pdfViewer.setDocument(pdfDoc);
      pdfLinkService.setDocument(pdfDoc);
      pdfViewer.currentPageNumber = Number(page);
      // Highlight
      if (highlight && highlight.text) {
        setTimeout(() => {
          const textLayers = containerRef.current?.querySelectorAll('.textLayer');
          if (textLayers) {
            textLayers.forEach(layer => {
              const nodes = Array.from(layer.childNodes);
              nodes.forEach(node => {
                if (node.nodeType === 3) return; // skip text
                const el = node as HTMLElement;
                if (el.innerText && el.innerText.includes(highlight.text)) {
                  el.style.background = 'yellow';
                }
              });
            });
          }
        }, 1000);
      }
    }
    load();
    return () => { destroyed = true; };
  }, [docId, page, highlight]);

  return <div ref={containerRef} style={{ width: "100%", height: "100%", overflow: "auto" }} />;
}
