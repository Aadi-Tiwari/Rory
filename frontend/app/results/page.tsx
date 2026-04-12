"use client";

import { useEffect, useState, useRef } from "react";
import { Navigation } from "@/components/landing/navigation";
import { FooterSection } from "@/components/landing/footer-section";
import { ArrowLeft, AlertTriangle, CheckCircle, XCircle, Activity, Shield, Heart, Thermometer, Wind, Droplets, Clock, TrendingUp } from "lucide-react";
import { GridBg } from "@/components/grid-bg";

interface PredictResult {
  recommendation: string; risk: number; confidence: number; completeness: number;
  outlier_flag: boolean; drift_alert: boolean; cluster_drift: number;
  sepsis_confidence_trend: number[];
  reasoning: { bullet: string; weight: number; source_field: string }[];
  model_version: string;
}

function CountUp({ end, suffix = "", decimals = 0, dur = 2000 }: { end: number; suffix?: string; decimals?: number; dur?: number }) {
  const [v, setV] = useState(0);
  useEffect(() => { const s = performance.now(); const t = (n: number) => { const p = Math.min((n - s) / dur, 1); setV((1 - Math.pow(1 - p, 3)) * end); if (p < 1) requestAnimationFrame(t); }; requestAnimationFrame(t); }, [end, dur]);
  return <>{v.toFixed(decimals)}{suffix}</>;
}

function CircleGauge({ value, color, size = 200 }: { value: number; color: string; size?: number }) {
  const [p, setP] = useState(0);
  useEffect(() => { setTimeout(() => setP(value), 200); }, [value]);
  const r = (size - 12) / 2, c = 2 * Math.PI * r;
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth={10} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={10}
          strokeDasharray={c} strokeDashoffset={c * (1 - p)} strokeLinecap="round"
          className="transition-all duration-[2.5s] ease-out" style={{ transform: "rotate(-90deg)", transformOrigin: "center" }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-5xl lg:text-6xl font-display" style={{ color }}><CountUp end={value * 100} suffix="%" decimals={1} dur={2500} /></span>
        <span className="text-xs font-mono text-white/35 mt-2">sepsis risk</span>
      </div>
    </div>
  );
}

function AnimBar({ value, color, delay = 0 }: { value: number; color: string; delay?: number }) {
  const [w, setW] = useState(0);
  useEffect(() => { setTimeout(() => setW(value * 100), 100 + delay); }, [value, delay]);
  return <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden"><div className="h-full rounded-full transition-all duration-[2s] ease-out" style={{ width: `${w}%`, backgroundColor: color }} /></div>;
}

function getVitalInfo(label: string, val: number | null | undefined, age: number) {
  if (val == null) return { flag: false, color: "#444", status: "Missing", detail: "Not provided. RORY uses population average and reduces confidence." };
  const y = age / 12;
  switch (label) {
    case "HR": {
      const lim = y < 5 ? 140 : y < 12 ? 120 : 100;
      if (val > lim) return { flag: true, color: "#ef4444", status: "Elevated", detail: `${val} bpm exceeds ${lim} bpm limit. Tachycardia is a SIRS criterion - the body raises heart rate to compensate for dropping blood pressure in sepsis.` };
      return { flag: false, color: "#22c55e", status: "Normal", detail: `${val} bpm is within range. Normal HR does not rule out early sepsis.` };
    }
    case "RR": {
      const lim = y < 5 ? 30 : y < 12 ? 24 : 20;
      if (val > lim) return { flag: true, color: "#ef4444", status: "Elevated", detail: `${val}/min exceeds ${lim}/min. Rapid breathing compensates for metabolic acidosis from tissue hypoxia.` };
      return { flag: false, color: "#22c55e", status: "Normal", detail: `${val}/min is within range.` };
    }
    case "Temp":
      if (val >= 104) return { flag: true, color: "#ef4444", status: "High Fever", detail: `${val}F exceeds SIRS threshold. Immune system in overdrive. This was a key finding in Rory Staunton's case.` };
      if (val >= 100.4) return { flag: true, color: "#eab308", status: "Fever", detail: `${val}F indicates immune activation. Combined with other flags, it suggests bacterial over viral.` };
      return { flag: false, color: "#22c55e", status: "Normal", detail: `${val}F - no fever detected.` };
    case "SpO2":
      if (val < 90) return { flag: true, color: "#ef4444", status: "Critical", detail: `${val}% - tissues not receiving adequate oxygen. May indicate ARDS or distributive shock.` };
      if (val < 95) return { flag: true, color: "#eab308", status: "Low", detail: `${val}% below 95% threshold. Early respiratory compromise possible.` };
      return { flag: false, color: "#22c55e", status: "Normal", detail: `${val}% - adequate oxygenation.` };
    case "Cap Refill":
      if (val > 3) return { flag: true, color: "#ef4444", status: "Prolonged", detail: `${val}s indicates poor perfusion. Blood shunting to vital organs. This was missed in Rory Staunton's case.` };
      if (val > 2) return { flag: true, color: "#eab308", status: "Borderline", detail: `${val}s is borderline. Normal is under 2 seconds.` };
      return { flag: false, color: "#22c55e", status: "Normal", detail: `${val}s - adequate perfusion.` };
    default: return { flag: false, color: "#22c55e", status: "OK", detail: "" };
  }
}

const icons: Record<string, React.ReactNode> = { HR: <Heart className="w-5 h-5" />, RR: <Wind className="w-5 h-5" />, Temp: <Thermometer className="w-5 h-5" />, SpO2: <Droplets className="w-5 h-5" />, "Cap Refill": <Clock className="w-5 h-5" /> };

export default function ResultsPage() {
  const [result, setResult] = useState<PredictResult | null>(null);
  const [input, setInput] = useState<Record<string, unknown> | null>(null);
  const [rev, setRev] = useState(0);

  useEffect(() => {
    const r = sessionStorage.getItem("rory_result"), i = sessionStorage.getItem("rory_input");
    if (r) { const d = JSON.parse(r); setResult(d); for (let j = 0; j < d.reasoning.length; j++) setTimeout(() => setRev(j + 1), 1000 + j * 350); }
    if (i) setInput(JSON.parse(i));
  }, []);

  if (!result) return (
    <main className="relative min-h-screen"><GridBg /><div className="relative z-10"><Navigation />
      <section className="pt-40 pb-32 flex flex-col items-center justify-center min-h-[60vh]">
        <Activity className="w-10 h-10 text-white/5 mb-6" /><p className="text-white/20 font-mono text-sm mb-6">No results found</p>
        <a href="/demo" className="text-sm text-white/30 hover:text-white transition-colors flex items-center gap-2"><ArrowLeft className="w-4 h-4" /> Run a case first</a>
      </section><FooterSection /></div></main>
  );

  const rc = result.recommendation === "HOME" ? "#22c55e" : result.recommendation === "ED" ? "#eab308" : "#ef4444";
  const age = Number((input as Record<string, unknown>)?.age_months ?? 0);
  const vitals = (input as { vitals?: Record<string, number | null> })?.vitals ?? {};
  const vList = [{ l: "HR", v: vitals.hr, u: "bpm" }, { l: "RR", v: vitals.rr, u: "/min" }, { l: "Temp", v: vitals.temp_f, u: "F" }, { l: "SpO2", v: vitals.spo2, u: "%" }, { l: "Cap Refill", v: vitals.cap_refill_s, u: "s" }];
  const flagCount = vList.filter(v => getVitalInfo(v.l, v.v, age).flag).length;

  const steps = result.recommendation === "HOME"
    ? [{ s: "Monitor 24-48 hours", w: "Viral illness can unmask bacterial infection." }, { s: "Return if fever > 103F or new symptoms", w: "Red-flag escalation indicators." }, { s: "Follow up within 48 hours", w: "Rory Staunton's abnormal labs were never reviewed." }]
    : result.recommendation === "ED"
    ? [{ s: "Transport to pediatric ED", w: "Needs CBC, lactate, blood cultures." }, { s: "Lactate within 30 minutes", w: "Best single biomarker for sepsis severity." }, { s: "Antibiotics within 1 hour", w: "Every hour delay increases mortality ~4%." }]
    : [{ s: "Call 911 immediately", w: "IV access and fluids can begin during transport." }, { s: "Activate Rory's Law (NY 405.4)", w: "Mandates sepsis screening within 15 min of triage." }, { s: "Blood cultures then antibiotics within 1 hour", w: "Each hour delay increases mortality 4-8%." }, { s: "20 mL/kg fluid bolus", w: "Restore circulating volume. May need 40-60 mL/kg." }];

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-background">
      <GridBg />
      <div className="relative z-10">
        <Navigation />

        <section className="pt-36 lg:pt-44 pb-24">
          <div className="max-w-[1100px] mx-auto px-6 lg:px-12">

            <a href="/demo" className="inline-flex items-center gap-2 text-xs font-mono text-white/25 hover:text-white/60 transition-colors mb-8">
              <ArrowLeft className="w-3.5 h-3.5" /> back
            </a>

            {/* ===== HERO ===== */}
            <div className="relative mb-16 overflow-hidden rounded-lg" style={{ background: `linear-gradient(180deg, ${rc}08 0%, transparent 60%)`, border: `1px solid ${rc}15` }}>
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[250px] rounded-full blur-[100px]" style={{ backgroundColor: `${rc}0a` }} />
              <div className="relative grid lg:grid-cols-[1fr_auto] gap-8 items-center px-10 lg:px-16 py-14 lg:py-20">
                <div>
                  <span className="text-xs font-mono text-white/25 tracking-[0.4em] uppercase block mb-6">Triage Result</span>
                  <h1 className="text-[100px] lg:text-[140px] font-display leading-[0.85] mb-4" style={{ color: rc }}>{result.recommendation}</h1>
                  <p className="text-base text-white/40 max-w-lg leading-relaxed">
                    {result.recommendation === "HOME" ? "Vitals are within normal ranges. Clinical description matches low-risk viral illness. No sepsis signature detected."
                      : result.recommendation === "ED" ? "Multiple vitals outside normal range. Pattern matches early bacterial infection that can progress to sepsis."
                      : "Presentation matches the sepsis signature. High fever + tachycardia + poor perfusion. Every hour of delay increases mortality 4-8%."}
                  </p>
                  <div className="flex gap-3 mt-6">
                    <span className="text-xs font-mono text-white/20 px-3 py-1.5 border border-white/[0.06] rounded-sm">{flagCount} vitals flagged</span>
                    <span className="text-xs font-mono text-white/20 px-3 py-1.5 border border-white/[0.06] rounded-sm">{result.model_version}</span>
                  </div>
                </div>
                <CircleGauge value={result.risk} color={rc} />
              </div>
            </div>

            {/* ===== METRICS ===== */}
            <div className="grid grid-cols-4 gap-3 mb-12">
              {[
                { label: "Confidence", val: result.confidence, isPercent: true, alert: false, info: result.confidence >= 0.9 ? "High - strong signal from both text and vitals" : result.confidence >= 0.7 ? "Moderate - some uncertainty present" : "Low - evaluate this patient regardless of recommendation" },
                { label: "Completeness", val: result.completeness, isPercent: true, alert: result.completeness < 1, info: `${Math.round(result.completeness * 5)}/5 vitals provided. ${result.completeness < 1 ? "Missing data reduces model certainty." : "Full data available."}` },
                { label: "Drift", val: result.cluster_drift, isPercent: false, alert: result.drift_alert, info: result.drift_alert ? "Patient trajectory moving toward sepsis centroid in embedding space" : "Stable position - not trending toward danger zone" },
                { label: "Risk Score", val: result.risk, isPercent: true, alert: result.risk > 0.5, info: result.risk > 0.8 ? "Extreme risk - strongly matches known sepsis cases" : result.risk > 0.3 ? "Elevated - further evaluation recommended" : "Low risk - inconsistent with sepsis patterns" },
              ].map((m, i) => (
                <div key={m.label} className={`relative overflow-hidden bg-[#0a0a10]/80 backdrop-blur-md border rounded-lg p-6 group hover:border-white/[0.15] transition-all duration-300 ${m.alert ? "border-[#ef4444]/15" : "border-white/[0.06]"}`}>
                  {/* Subtle top glow */}
                  {m.alert && <div className="absolute top-0 left-0 right-0 h-16 bg-gradient-to-b from-[#ef4444]/[0.04] to-transparent pointer-events-none" />}

                  <span className="text-xs font-mono text-white/30 tracking-widest uppercase block mb-4 relative">{m.label}</span>
                  <span className={`text-5xl font-display block mb-3 relative ${m.alert ? "text-[#ef4444]" : "text-white"}`}>
                    <CountUp end={m.isPercent ? m.val * 100 : m.val} suffix={m.isPercent ? "%" : ""} decimals={m.isPercent ? 0 : 3} dur={1800 + i * 200} />
                  </span>
                  <AnimBar value={m.val} color={m.alert ? "#ef4444" : rc} delay={i * 100} />
                  <p className="text-xs text-white/25 mt-4 leading-relaxed relative">{m.info}</p>
                </div>
              ))}
            </div>

            {/* ===== VITALS ===== */}
            <div className="mb-12">
              <div className="flex items-center gap-3 mb-6">
                <span className="w-6 h-px bg-white/10" />
                <span className="text-xs font-mono text-white/25 tracking-[0.3em] uppercase">Vital Signs</span>
              </div>
              <div className="grid grid-cols-5 gap-3">
                {vList.map((v) => {
                  const info = getVitalInfo(v.l, v.v, age);
                  return (
                    <div key={v.l} className={`bg-[#0a0a10]/80 backdrop-blur-md rounded-lg p-5 border transition-all hover:border-white/[0.12] group ${
                      info.flag ? "border-l-2" : "border border-white/[0.06]"
                    }`} style={info.flag ? { borderLeftColor: info.color, borderTopColor: "rgba(255,255,255,0.04)", borderRightColor: "rgba(255,255,255,0.04)", borderBottomColor: "rgba(255,255,255,0.04)" } : {}}>
                      <div className="flex items-center gap-2 text-white/20 mb-3">{icons[v.l]}<span className="text-xs font-mono">{v.l}</span></div>
                      <span className={`text-3xl font-display block ${v.v == null ? "text-white/10" : "text-white"}`}>{v.v ?? "--"}</span>
                      {v.v != null && <span className="text-xs font-mono text-white/20">{v.u}</span>}
                      <div className="flex items-center gap-1.5 mt-3">
                        {info.flag ? <AlertTriangle className="w-3 h-3" style={{ color: info.color }} /> : v.v != null ? <CheckCircle className="w-3 h-3 text-[#22c55e]/60" /> : null}
                        <span className="text-xs font-mono" style={{ color: info.color }}>{info.status}</span>
                      </div>
                      <p className="text-xs text-white/20 mt-3 leading-relaxed opacity-0 group-hover:opacity-100 transition-opacity duration-300">{info.detail}</p>
                    </div>
                  );
                })}
              </div>
              {result.completeness < 1 && (
                <div className="mt-3 p-4 bg-[#eab308]/[0.04] border border-[#eab308]/10 rounded-lg flex items-start gap-3">
                  <AlertTriangle className="w-4 h-4 text-[#eab308]/60 shrink-0 mt-0.5" />
                  <p className="text-xs text-white/35">Only {Math.round(result.completeness * 5)}/5 vitals provided. Confidence reduced by ~{Math.round((1 - result.completeness) * 30)}% to reflect uncertainty.</p>
                </div>
              )}
            </div>

            {/* ===== REASONING ===== */}
            <div className="mb-12">
              <div className="flex items-center gap-3 mb-6">
                <span className="w-6 h-px bg-white/10" />
                <span className="text-xs font-mono text-white/25 tracking-[0.3em] uppercase">Why This Decision</span>
              </div>
              <div className="bg-[#0a0a10]/80 backdrop-blur-md border border-white/[0.06] rounded-lg p-8">
                <p className="text-xs text-white/20 mb-8">The model analyzed clinical text and vital signs through dual encoders. Each factor's contribution:</p>
                <div className="space-y-3">
                  {result.reasoning.map((r, i) => (
                    <div key={i} className={`flex items-center gap-5 p-4 rounded-lg border border-white/[0.04] hover:border-white/[0.08] hover:bg-white/[0.01] transition-all duration-500 ${i < rev ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-6"}`}>
                      <div className="w-20 shrink-0">
                        <AnimBar value={r.weight} color={rc} delay={i * 200 + 500} />
                        <span className="text-xs font-mono text-white/20 block text-center mt-1">{(r.weight * 100).toFixed(0)}%</span>
                      </div>
                      <p className="text-sm text-white/50 leading-relaxed flex-1">{r.bullet}</p>
                      <span className="text-xs font-mono text-white/15 px-2 py-1 border border-white/[0.04] rounded shrink-0">{r.source_field.replace("vitals.", "")}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* ===== TREND ===== */}
            {result.sepsis_confidence_trend.length > 0 && (() => {
              const trend = result.sepsis_confidence_trend;
              const maxVal = Math.max(...trend, 0.01);
              const rising = trend.length > 1 && trend[trend.length - 1] > trend[0];
              return (
              <div className="mb-12">
                <div className="flex items-center gap-3 mb-6">
                  <span className="w-6 h-px bg-white/10" />
                  <span className="text-xs font-mono text-white/25 tracking-[0.3em] uppercase">Sepsis Confidence Over Time</span>
                </div>
                <div className="bg-[#0a0a10]/80 backdrop-blur-md border border-white/[0.06] rounded-lg p-8">
                  {/* SVG chart */}
                  <svg viewBox="0 0 500 160" className="w-full h-auto mb-4" style={{ overflow: "visible" }}>
                    {/* Grid lines */}
                    {[0, 0.25, 0.5, 0.75, 1].map(p => (
                      <g key={p}>
                        <line x1="40" y1={20 + 120 * (1 - p)} x2="480" y2={20 + 120 * (1 - p)} stroke="rgba(255,255,255,0.03)" strokeWidth="0.5" />
                        <text x="35" y={24 + 120 * (1 - p)} textAnchor="end" fill="rgba(255,255,255,0.1)" fontSize="7" fontFamily="monospace">{(maxVal * p * 100).toFixed(1)}%</text>
                      </g>
                    ))}

                    {/* Area fill */}
                    <defs>
                      <linearGradient id="trendAreaFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={rc} stopOpacity="0.15" />
                        <stop offset="100%" stopColor={rc} stopOpacity="0" />
                      </linearGradient>
                    </defs>
                    <path d={
                      `M ${40 + 0 * (440 / Math.max(trend.length - 1, 1))} ${20 + 120 * (1 - trend[0] / maxVal)} ` +
                      trend.map((v, i) => `L ${40 + i * (440 / Math.max(trend.length - 1, 1))} ${20 + 120 * (1 - v / maxVal)}`).join(" ") +
                      ` L ${40 + (trend.length - 1) * (440 / Math.max(trend.length - 1, 1))} 140 L 40 140 Z`
                    } fill="url(#trendAreaFill)" />

                    {/* Line */}
                    <polyline
                      points={trend.map((v, i) => `${40 + i * (440 / Math.max(trend.length - 1, 1))},${20 + 120 * (1 - v / maxVal)}`).join(" ")}
                      fill="none" stroke={rc} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                    />

                    {/* Dots */}
                    {trend.map((v, i) => {
                      const x = 40 + i * (440 / Math.max(trend.length - 1, 1));
                      const y = 20 + 120 * (1 - v / maxVal);
                      const last = i === trend.length - 1;
                      return (
                        <g key={i}>
                          {last && <circle cx={x} cy={y} r="10" fill={rc} opacity="0.1"><animate attributeName="r" values="8;14;8" dur="2s" repeatCount="indefinite" /><animate attributeName="opacity" values="0.15;0.05;0.15" dur="2s" repeatCount="indefinite" /></circle>}
                          <circle cx={x} cy={y} r={last ? 5 : 4} fill={rc} opacity={0.5 + (i / trend.length) * 0.5} />
                          <circle cx={x} cy={y} r="2" fill="white" opacity="0.8" />
                          <text x={x} y={y - 10} textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="8" fontFamily="monospace">{(v * 100).toFixed(1)}%</text>
                          <text x={x} y="155" textAnchor="middle" fill="rgba(255,255,255,0.1)" fontSize="7" fontFamily="monospace">t{i + 1}</text>
                        </g>
                      );
                    })}
                  </svg>

                  <div className="flex items-center gap-2 text-xs text-white/25">
                    <TrendingUp className="w-3.5 h-3.5" />
                    {rising ? "Rising - sepsis confidence increasing across readings. This trajectory is concerning." : "Stable or declining - no escalation detected."}
                  </div>
                </div>
              </div>
              );
            })()}

            {/* ===== PATIENT + FLAGS side by side ===== */}
            <div className="grid lg:grid-cols-2 gap-3 mb-12">
              {/* Patient */}
              {input && (
                <div className="bg-[#0a0a10]/80 backdrop-blur-md border border-white/[0.06] rounded-lg p-8">
                  <span className="text-xs font-mono text-white/25 tracking-[0.3em] uppercase block mb-6">Patient</span>
                  <div className="grid grid-cols-3 gap-4 mb-5">
                    <div><span className="text-xs font-mono text-white/20 block mb-1">Age</span><span className="text-2xl font-display">{Math.floor(age / 12)}yo</span></div>
                    <div><span className="text-xs font-mono text-white/20 block mb-1">Sex</span><span className="text-2xl font-display">{(input as Record<string, unknown>).sex === "M" ? "M" : "F"}</span></div>
                    <div><span className="text-xs font-mono text-white/20 block mb-1">Weight</span><span className="text-2xl font-display">{String((input as Record<string, unknown>).weight_kg)}kg</span></div>
                  </div>
                  <span className="text-xs font-mono text-white/20 block mb-2">Complaint</span>
                  <p className="text-sm text-white/30 italic leading-relaxed">&ldquo;{String((input as Record<string, unknown>).complaint_text)}&rdquo;</p>
                </div>
              )}

              {/* Flags */}
              <div className="space-y-3">
                <div className={`bg-[#0a0a10]/80 backdrop-blur-md rounded-lg p-6 border ${result.outlier_flag ? "border-[#eab308]/15" : "border-white/[0.06]"}`}>
                  <div className="flex items-center gap-3 mb-2">
                    {result.outlier_flag ? <AlertTriangle className="w-5 h-5 text-[#eab308]" /> : <CheckCircle className="w-5 h-5 text-white/15" />}
                    <span className={`text-base font-display ${result.outlier_flag ? "text-[#eab308]" : "text-white/40"}`}>{result.outlier_flag ? "Outlier Detected" : "Within Clusters"}</span>
                  </div>
                  <p className="text-sm text-white/30 leading-relaxed">{result.outlier_flag ? "This case doesn't match any known cluster. The model hasn't seen this pattern before." : "Fits within known patient clusters. Model has training support."}</p>
                </div>
                <div className={`bg-[#0a0a10]/80 backdrop-blur-md rounded-lg p-6 border ${result.drift_alert ? "border-[#ef4444]/15" : "border-white/[0.06]"}`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      {result.drift_alert ? <XCircle className="w-5 h-5 text-[#ef4444]" /> : <CheckCircle className="w-5 h-5 text-white/15" />}
                      <span className={`text-base font-display ${result.drift_alert ? "text-[#ef4444]" : "text-white/40"}`}>Drift</span>
                    </div>
                    <span className={`text-2xl font-display ${result.drift_alert ? "text-[#ef4444]" : "text-white/30"}`}>{result.cluster_drift.toFixed(3)}</span>
                  </div>
                  <p className="text-sm text-white/30 leading-relaxed">{result.drift_alert ? "Trajectory moving toward sepsis centroid. Individual vitals may look borderline but the combined pattern is deteriorating." : "Stable in embedding space. Not trending toward sepsis."}</p>
                </div>
              </div>
            </div>

            {/* ===== NEXT STEPS ===== */}
            <div className="mb-12">
              <div className="flex items-center gap-3 mb-6">
                <span className="w-6 h-px bg-white/10" />
                <span className="text-xs font-mono text-white/25 tracking-[0.3em] uppercase">Next Steps</span>
              </div>
              <div className="bg-[#0a0a10]/80 backdrop-blur-md border rounded-lg p-8" style={{ borderColor: `${rc}12` }}>
                <div className="space-y-3">
                  {steps.map((item, i) => (
                    <div key={i} className="flex items-start gap-4 p-4 border border-white/[0.04] rounded-lg hover:border-white/[0.08] transition-all">
                      <div className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-mono mt-0.5" style={{ border: `1px solid ${rc}30`, color: rc }}>{i + 1}</div>
                      <div><p className="text-sm text-white/60 font-medium">{item.s}</p><p className="text-xs text-white/25 mt-1 leading-relaxed">{item.w}</p></div>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-white/15 mt-6 pt-4 border-t border-white/[0.04]">AI-generated recommendations. Clinical judgment takes precedence. Refer to Rory&apos;s Law (NY 405.4).</p>
              </div>
            </div>

            {/* ===== ACTIONS ===== */}
            <div className="flex gap-3">
              <a href="/demo" className="flex-1 py-5 text-center text-sm font-mono border border-white/[0.08] bg-[#0a0a10]/60 backdrop-blur-md text-white/40 hover:text-white/70 hover:border-white/[0.15] transition-all rounded-lg flex items-center justify-center gap-2"><ArrowLeft className="w-4 h-4" /> New Patient</a>
              <button onClick={() => window.print()} className="flex-1 py-5 text-center text-sm font-mono border border-white/[0.08] bg-[#0a0a10]/60 backdrop-blur-md text-white/40 hover:text-white/70 hover:border-white/[0.15] transition-all rounded-lg flex items-center justify-center gap-2"><Shield className="w-4 h-4" /> Export</button>
            </div>

          </div>
        </section>
        <FooterSection />
      </div>
    </main>
  );
}
