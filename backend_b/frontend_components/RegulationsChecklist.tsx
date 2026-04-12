import { useState } from "react";
import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import CitationPdfModal from "./CitationPdfModal";

export interface RegulationsCheck {
  check_id: string;
  vital_signs_recorded: boolean;
  mental_status_assessed: boolean;
  sepsis_screen_triggered: boolean;
  escalation_required: boolean;
  re_presentation_flag: boolean;
  wound_source_documented: boolean;
  physician_notified: boolean;
  discharge_criteria_met: boolean;
  missing_items: string[];
}

export interface ProtocolCitation {
  citation_id: string;
  source: "rorys_regs" | "pediatric_ssc" | "pals";
  section: string;
  page: number;
  quote: string;
  pdf_url: string;
}

const REGULATIONS_LABELS: Record<keyof Omit<RegulationsCheck, "check_id" | "missing_items">, string> = {
  vital_signs_recorded: "Vital signs complete",
  mental_status_assessed: "Mental status assessed",
  sepsis_screen_triggered: "Sepsis screen triggered",
  escalation_required: "Escalation required",
  re_presentation_flag: "Re-presenting patient",
  wound_source_documented: "Wound source documented",
  physician_notified: "Physician notified",
  discharge_criteria_met: "Discharge criteria met",
};

interface Props {
  check: RegulationsCheck;
  citations: ProtocolCitation[];
}

export default function RegulationsChecklist({ check, citations }: Props) {
  const [activePdf, setActivePdf] = useState<ProtocolCitation | null>(null);

  return (
    <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-700">
          Rory's Regulations §405.4
        </h3>
        {citations.length > 0 && (
          <button
            onClick={() => setActivePdf(citations[0])}
            className="text-xs text-blue-600 hover:underline"
          >
            [cite]
          </button>
        )}
      </div>
      <ul className="space-y-2">
        {Object.entries(REGULATIONS_LABELS).map(([key, label]) => {
          const passed = check[key as keyof typeof REGULATIONS_LABELS];
          const isWarning = key === "escalation_required" && passed === true;
          return (
            <li key={key} className="flex items-center gap-2 text-sm">
              {passed && !isWarning && (
                <CheckCircle className="w-4 h-4 text-green-600 shrink-0" />
              )}
              {isWarning && (
                <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
              )}
              {!passed && <XCircle className="w-4 h-4 text-slate-300 shrink-0" />}
              <span className={passed ? "text-slate-900" : "text-slate-400"}>
                {label}
              </span>
            </li>
          );
        })}
      </ul>
      {check.missing_items.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-200 text-xs text-amber-700">
          <span className="font-semibold">Missing: </span>
          {check.missing_items.join(", ")}
        </div>
      )}
      {activePdf && (
        <CitationPdfModal
          citation={activePdf}
          onClose={() => setActivePdf(null)}
        />
      )}
    </div>
  );
}
