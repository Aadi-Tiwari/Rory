import { X } from "lucide-react";
import { Document, Page, pdfjs } from "react-pdf";
import type { ProtocolCitation } from "./RegulationsChecklist";

pdfjs.GlobalWorkerOptions.workerSrc =
  "https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js";

const SOURCE_LABEL: Record<ProtocolCitation["source"], string> = {
  rorys_regs: "Rory's Regulations (10 NYCRR 405.4)",
  pediatric_ssc: "2020 Pediatric Surviving Sepsis Campaign",
  pals: "PALS 2020 Reference",
};

interface Props {
  citation: ProtocolCitation;
  onClose: () => void;
}

export default function CitationPdfModal({ citation, onClose }: Props) {
  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b border-slate-200 p-4 flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-slate-900">
              {SOURCE_LABEL[citation.source]}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              {citation.section} · page {citation.page}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-slate-100"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-4">
          <Document
            file={citation.pdf_url}
            loading={<div className="text-sm text-slate-500">Loading PDF...</div>}
          >
            <Page pageNumber={citation.page} width={600} />
          </Document>
          <blockquote className="mt-4 p-3 bg-amber-50 border-l-4 border-amber-400 text-sm italic text-slate-800">
            {citation.quote}
          </blockquote>
        </div>
      </div>
    </div>
  );
}
