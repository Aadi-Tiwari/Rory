// RORY v2 Backend B - AIP Logic function
// interpret_cluster_drift: converts raw drift number + trend into plain English
// so the AIP Agent and regulations panel never expose raw floats to judges.

import { Function } from "@foundry/functions-api";

export type DriftSeverity = "none" | "stable" | "drifting" | "accelerating";

export interface DriftInterpretation {
  plain_english: string;
  severity: DriftSeverity;
  citation_hint: string; // which Rory's Regs section to cite
}

@Function()
export function interpret_cluster_drift(
  drift: number,
  trend: number[],
): DriftInterpretation {
  if (trend.length < 3) {
    return {
      plain_english: "Insufficient history to assess trajectory.",
      severity: "none",
      citation_hint: "",
    };
  }

  const recent = trend.slice(-3);
  const delta = recent[recent.length - 1] - recent[0];
  const monotonic = recent.every((v, i, arr) => i === 0 || v >= arr[i - 1]);

  if (drift < -0.05 && monotonic && delta > 0.15) {
    return {
      plain_english: "Patient trajectory accelerating toward septic presentation.",
      severity: "accelerating",
      citation_hint: "rorys_regs §405.4.3",
    };
  } else if (drift < -0.02 && delta > 0.08) {
    return {
      plain_english: "Patient drifting toward septic cluster.",
      severity: "drifting",
      citation_hint: "rorys_regs §405.4.1",
    };
  } else if (Math.abs(drift) < 0.02) {
    return {
      plain_english: "Patient trajectory stable.",
      severity: "stable",
      citation_hint: "",
    };
  } else {
    return {
      plain_english: "Patient trajectory improving.",
      severity: "none",
      citation_hint: "",
    };
  }
}
