"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, AlertTriangle, CheckCircle, XCircle, Activity, RotateCcw } from "lucide-react";

const BACKEND_URL = "http://localhost:8000";

const presets = [
  { label: "Viral mimic", desc: "9yo girl, cold symptoms", data: { age_months: 108, sex: "F", weight_kg: 30, complaint_text: "9yo girl, fever 101, runny nose, mom says just a cold, active and alert", hr: 98, rr: 20, temp_f: 101, spo2: 98, cap_refill_s: 1.8 } },
  { label: "Rory Staunton", desc: "12yo boy, wound + fever", data: { age_months: 144, sex: "M", weight_kg: 43, complaint_text: "12yo boy scraped arm 2 days ago, fever 104, leg pain, looks pale", hr: 138, rr: 28, temp_f: 104, spo2: 95, cap_refill_s: 3.2 } },
  { label: "Limited vitals", desc: "Same boy, only HR + temp", data: { age_months: 144, sex: "M", weight_kg: 43, complaint_text: "12yo boy scraped arm 2 days ago, fever 104, leg pain, looks pale", hr: 138, rr: null, temp_f: 104, spo2: null, cap_refill_s: null } },
];

const demoResponses: Record<string, PredictResult> = {
  "Viral mimic": {
    recommendation: "HOME", risk: 0.003, confidence: 0.94, completeness: 1.0,
    outlier_flag: false, drift_alert: false, cluster_drift: 0.12,
    sepsis_confidence_trend: [0.006, 0.003],
    reasoning: [
      { bullet: "Temp 101F is low-grade, below SIRS threshold for age", weight: 0.3, source_field: "vitals.temp_f" },
      { bullet: "Heart rate 98 bpm is normal for 9yo", weight: 0.25, source_field: "vitals.hr" },
      { bullet: "Clinical text suggests upper respiratory infection", weight: 0.35, source_field: "complaint_text" },
      { bullet: "SpO2 98% and cap refill 1.8s both within normal range", weight: 0.1, source_field: "vitals" },
    ],
    model_version: "rory-demo",
  },
  "Rory Staunton": {
    recommendation: "911", risk: 0.9999, confidence: 0.97, completeness: 1.0,
    outlier_flag: false, drift_alert: true, cluster_drift: 0.847,
    sepsis_confidence_trend: [0.82, 0.91, 0.97, 0.999],
    reasoning: [
      { bullet: "Temp 104F exceeds SIRS threshold for age", weight: 0.35, source_field: "vitals.temp_f" },
      { bullet: "HR 138 bpm is tachycardic, exceeds age-adjusted limit of 120", weight: 0.25, source_field: "vitals.hr" },
      { bullet: "Clinical text: wound + fever + pain + pallor matches sepsis pattern", weight: 0.25, source_field: "complaint_text" },
      { bullet: "Cap refill 3.2s indicates poor peripheral perfusion", weight: 0.15, source_field: "vitals.cap_refill_s" },
    ],
    model_version: "rory-demo",
  },
  "Limited vitals": {
    recommendation: "911", risk: 0.9987, confidence: 0.72, completeness: 0.4,
    outlier_flag: true, drift_alert: true, cluster_drift: 0.791,
    sepsis_confidence_trend: [0.85, 0.94, 0.998],
    reasoning: [
      { bullet: "Temp 104F exceeds SIRS threshold for age", weight: 0.4, source_field: "vitals.temp_f" },
      { bullet: "HR 138 bpm is tachycardic for 12yo", weight: 0.3, source_field: "vitals.hr" },
      { bullet: "Clinical text: wound history + high fever + pain + pallor", weight: 0.2, source_field: "complaint_text" },
      { bullet: "3 of 5 vitals missing - confidence penalized, threshold lowered", weight: 0.1, source_field: "completeness" },
    ],
    model_version: "rory-demo",
  },
};

interface PredictResult {
  recommendation: string; risk: number; confidence: number; completeness: number;
  outlier_flag: boolean; drift_alert: boolean; cluster_drift: number;
  sepsis_confidence_trend: number[];
  reasoning: { bullet: string; weight: number; source_field: string }[];
  model_version: string;
}

function RiskBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden mt-2">
      <div className="h-full rounded-full transition-all duration-1000 ease-out" style={{ width: `${value * 100}%`, backgroundColor: color }} />
    </div>
  );
}

export function DemoContent() {
  const router = useRouter();
  const [ageMonths, setAgeMonths] = useState<number | "">("");
  const [sex, setSex] = useState<"M" | "F">("M");
  const [weight, setWeight] = useState<number | "">("");
  const [complaint, setComplaint] = useState("");
  const [hr, setHr] = useState<number | "">("");
  const [rr, setRr] = useState<number | "">("");
  const [tempF, setTempF] = useState<number | "">("");
  const [spo2, setSpo2] = useState<number | "">("");
  const [capRefill, setCapRefill] = useState<number | "">("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<PredictResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [revealedReasons, setRevealedReasons] = useState(0);
  const [activePreset, setActivePreset] = useState<number | null>(null);
  const [demoMode, setDemoMode] = useState(false);

  const fillPreset = (idx: number) => {
    const d = presets[idx].data;
    setAgeMonths(d.age_months); setSex(d.sex as "M" | "F"); setWeight(d.weight_kg);
    setComplaint(d.complaint_text);
    setHr(d.hr ?? ""); setRr(d.rr ?? ""); setTempF(d.temp_f ?? "");
    setSpo2(d.spo2 ?? ""); setCapRefill(d.cap_refill_s ?? "");
    setActivePreset(idx);
  };

  const loadPreset = (idx: number) => {
    fillPreset(idx);
    setResult(null); setError(null);
  };

  const toggleDemo = () => {
    const next = !demoMode;
    setDemoMode(next);
    if (next) {
      // Auto-fill a random preset when turning demo on
      const idx = Math.floor(Math.random() * presets.length);
      fillPreset(idx);
      setResult(null); setError(null);
    }
  };

  const clearForm = () => {
    setAgeMonths(""); setSex("M"); setWeight(""); setComplaint("");
    setHr(""); setRr(""); setTempF(""); setSpo2(""); setCapRefill("");
    setResult(null); setError(null); setRevealedReasons(0); setActivePreset(null);
  };

  const canRun = demoMode || (ageMonths !== "" && weight !== "" && complaint.trim().length > 0);

  const navigateToResults = (data: PredictResult, patientInput: Record<string, unknown>) => {
    // Store in sessionStorage so results page can read it
    sessionStorage.setItem("rory_result", JSON.stringify(data));
    sessionStorage.setItem("rory_input", JSON.stringify(patientInput));
    setRunning(false);
    router.push("/results");
  };

  const runAnalysis = async () => {
    if (!canRun) return;
    setRunning(true); setResult(null); setError(null); setRevealedReasons(0);

    if (demoMode) {
      const idx = activePreset ?? Math.floor(Math.random() * presets.length);
      fillPreset(idx);
      const p = presets[idx];
      const label = p.label;
      await new Promise(r => setTimeout(r, 600 + Math.random() * 400));
      navigateToResults(demoResponses[label] ?? demoResponses["Viral mimic"], p.data);
      return;
    }

    const inputData = {
      age_months: Number(ageMonths), sex, weight_kg: Number(weight), complaint_text: complaint,
      vitals: { hr: hr !== "" ? Number(hr) : null, rr: rr !== "" ? Number(rr) : null, temp_f: tempF !== "" ? Number(tempF) : null, spo2: spo2 !== "" ? Number(spo2) : null, cap_refill_s: capRefill !== "" ? Number(capRefill) : null },
    };
    const body = { patient_id: `LIVE-${Date.now()}`, ...inputData };
    try {
      const res = await fetch(`${BACKEND_URL}/predict`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      navigateToResults(await res.json(), inputData);
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to reach Backend A"); setRunning(false); }
  };

  const recColor = !result ? "#666" : result.recommendation === "HOME" ? "#22c55e" : result.recommendation === "ED" ? "#eab308" : "#ef4444";

  const vitalsArr = [
    { label: "HR", unit: "bpm", val: hr, set: setHr, ph: "98" },
    { label: "RR", unit: "/min", val: rr, set: setRr, ph: "20" },
    { label: "Temp", unit: "F", val: tempF, set: setTempF, ph: "101" },
    { label: "SpO2", unit: "%", val: spo2, set: setSpo2, ph: "98" },
    { label: "Cap", unit: "s", val: capRefill, set: setCapRefill, ph: "1.8" },
  ];

  const filledVitals = vitalsArr.filter(v => v.val !== "").length;

  const inputCls = "w-full bg-[#0a0a0f] border border-foreground/10 px-4 py-4 text-base font-mono text-foreground focus:outline-none focus:border-[#ef4444]/30 focus:bg-[#0d0d12] transition-all placeholder:text-foreground/15 rounded-sm";

  return (
    <section className="relative pt-32 lg:pt-40 pb-24 lg:pb-32 overflow-hidden">
      <div className="relative max-w-[1000px] mx-auto px-6 lg:px-12">

        {/* Header */}
        <div className="text-center mb-16">
          <span className="inline-flex items-center gap-3 text-xs font-mono text-muted-foreground tracking-[0.3em] uppercase mb-6">
            <span className="w-8 h-px bg-foreground/15" />
            Triage
            <span className="w-8 h-px bg-foreground/15" />
          </span>
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-display tracking-tight">
            Enter a patient.
          </h1>
        </div>

        {/* Main card */}
        <div className="bg-[#08080c]/90 backdrop-blur-xl border border-foreground/[0.08] rounded-sm shadow-2xl shadow-black/50">

          {/* Top bar: mode + presets + clear */}
          <div className="flex items-center justify-between px-8 py-4 border-b border-foreground/[0.06]">
            <div className="flex items-center gap-2">
              {presets.map((p, i) => (
                <button key={p.label} onClick={() => loadPreset(i)}
                  className={`px-4 py-2 text-xs font-mono rounded-sm transition-all ${
                    activePreset === i ? "bg-[#ef4444]/10 text-[#ef4444] border border-[#ef4444]/20" : "text-muted-foreground hover:text-foreground border border-transparent hover:border-foreground/10"
                  }`}>
                  {p.label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-3">
              <button onClick={toggleDemo}
                className={`text-xs font-mono flex items-center gap-1.5 px-3 py-1.5 rounded-sm transition-all ${
                  demoMode ? "bg-[#22c55e]/10 text-[#22c55e] border border-[#22c55e]/20" : "text-muted-foreground border border-foreground/10 hover:border-foreground/20"
                }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${demoMode ? "bg-[#22c55e]" : "bg-foreground/20"}`} />
                {demoMode ? "Demo" : "Live"}
              </button>
              <button onClick={clearForm} className="text-xs font-mono text-foreground/20 hover:text-foreground/50 transition-colors">
                <RotateCcw className="w-3 h-3" />
              </button>
            </div>
          </div>

          {/* Form body */}
          <div className="p-8 lg:p-10 space-y-6">

            {/* Row 1: Patient info */}
            <div>
              <span className="text-xs font-mono text-muted-foreground tracking-widest uppercase block mb-3">Patient</span>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-mono text-foreground/30 block mb-1.5">Age (months)</label>
                  <input type="number" value={ageMonths} onChange={(e) => setAgeMonths(e.target.value ? Number(e.target.value) : "")} placeholder="144" className={inputCls} />
                </div>
                <div>
                  <label className="text-xs font-mono text-foreground/30 block mb-1.5">Sex</label>
                  <div className="grid grid-cols-2 gap-0">
                    {(["M", "F"] as const).map((s) => (
                      <button key={s} onClick={() => setSex(s)}
                        className={`py-3.5 text-sm font-mono border rounded-sm transition-all ${
                          sex === s ? "bg-foreground/[0.08] border-foreground/20 text-foreground" : "bg-[#0a0a0f] border-foreground/10 text-foreground/25"
                        }`}>
                        {s === "M" ? "Male" : "Female"}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-xs font-mono text-foreground/30 block mb-1.5">Weight (kg)</label>
                  <input type="number" value={weight} onChange={(e) => setWeight(e.target.value ? Number(e.target.value) : "")} placeholder="43" className={inputCls} />
                </div>
              </div>
            </div>

            {/* Divider */}
            <div className="h-px bg-foreground/[0.04]" />

            {/* Row 2: Complaint */}
            <div>
              <span className="text-xs font-mono text-muted-foreground tracking-widest uppercase block mb-3">What do you see?</span>
              <textarea value={complaint} onChange={(e) => setComplaint(e.target.value)} placeholder="12yo boy scraped arm 2 days ago, fever 104, leg pain, looks pale..."
                rows={3} className={`${inputCls} resize-none leading-relaxed`} />
            </div>

            {/* Divider */}
            <div className="h-px bg-foreground/[0.04]" />

            {/* Row 3: Vitals */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono text-muted-foreground tracking-widest uppercase">Vitals</span>
                <span className="text-xs font-mono text-foreground/20">{filledVitals}/5 entered - leave blank if unavailable</span>
              </div>
              <div className="grid grid-cols-5 gap-3">
                {vitalsArr.map((v) => (
                  <div key={v.label}>
                    <label className="text-xs font-mono text-foreground/30 block mb-1.5 text-center">{v.label}</label>
                    <input type="number" step="any" value={v.val} onChange={(e) => v.set(e.target.value ? Number(e.target.value) : "")} placeholder={v.ph}
                      className={`${inputCls} text-center text-lg font-display`} />
                    <span className="text-[10px] font-mono text-foreground/15 block text-center mt-1">{v.unit}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Run button - bottom of card */}
          <div className="px-8 lg:px-10 pb-8 lg:pb-10">
            <button onClick={runAnalysis} disabled={running || !canRun}
              className={`w-full py-5 text-base font-display tracking-wide transition-all duration-500 flex items-center justify-center gap-3 rounded-sm ${
                running ? "bg-[#ef4444]/10 text-[#ef4444] border border-[#ef4444]/20"
                : !canRun ? "bg-foreground/[0.03] text-foreground/15 cursor-not-allowed border border-foreground/[0.05]"
                : "bg-foreground text-background hover:shadow-[0_0_30px_rgba(255,255,255,0.08)] border border-foreground"
              }`}>
              {running ? (
                <><div className="w-4 h-4 border-2 border-[#ef4444]/30 border-t-[#ef4444] rounded-full animate-spin" /> Analyzing...</>
              ) : (
                <><ArrowRight className="w-4 h-4" /> Run Analysis</>
              )}
            </button>

            {error && (
              <div className="border border-[#ef4444]/15 bg-[#ef4444]/[0.04] p-5 mt-4 rounded-sm">
                <div className="flex items-center gap-2 mb-1"><XCircle className="w-4 h-4 text-[#ef4444]" /><span className="text-xs">Connection failed</span></div>
                <p className="text-[10px] text-muted-foreground">{error}. Turn on Demo mode for cached results.</p>
              </div>
            )}
          </div>
        </div>

      </div>
    </section>
  );
}
