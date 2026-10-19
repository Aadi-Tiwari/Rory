"use client";

import { useEffect, useRef, useState } from "react";

function GpuAnimation({ activeStep }: { activeStep: number }) {
  // Separation: 0=assembled, 1=half exploded, 2=fully exploded
  const sep = activeStep === 0 ? 0 : activeStep === 1 ? 55 : 110;

  // Layer config: label, yOffset when assembled, color, height, details
  const layers = [
    { id: "shroud",    label: "Shroud",    baseY: 0,   h: 70,  color: "#1c1c1e", stroke: "#444", sepMul: 1.0 },
    { id: "fans",      label: "Fans",      baseY: 10,  h: 55,  color: "#2a2a2e", stroke: "#555", sepMul: 0.75 },
    { id: "heatsink",  label: "Heatsink",  baseY: 25,  h: 45,  color: "#3a3a40", stroke: "#666", sepMul: 0.5 },
    { id: "die",       label: "GPU Die",   baseY: 55,  h: 25,  color: "#1a1a1e", stroke: "#c00c3d", sepMul: 0.25 },
    { id: "pcb",       label: "PCB",       baseY: 70,  h: 55,  color: "#0a1a0e", stroke: "#2d5a35", sepMul: 0 },
    { id: "vrm",       label: "VRM",       baseY: 95,  h: 20,  color: "#1a1508", stroke: "#8a7020", sepMul: -0.2 },
    { id: "backplate", label: "Backplate",  baseY: 110, h: 35,  color: "#151518", stroke: "#333", sepMul: -0.45 },
  ];

  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <svg viewBox="0 0 520 500" className="w-full h-full max-w-[500px]" style={{ overflow: "visible" }}>
        <defs>
          {/* Gradients */}
          <linearGradient id="gpuPcbGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#0f2a14" />
            <stop offset="100%" stopColor="#051008" />
          </linearGradient>
          <linearGradient id="gpuHeatGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#5a5a60" />
            <stop offset="100%" stopColor="#2a2a30" />
          </linearGradient>
          <linearGradient id="gpuDieGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#2a0a0a" />
            <stop offset="100%" stopColor="#1a0505" />
          </linearGradient>
          <linearGradient id="copperGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8a5a30" />
            <stop offset="50%" stopColor="#c4884a" />
            <stop offset="100%" stopColor="#8a5a30" />
          </linearGradient>
          {/* Glow filter */}
          <filter id="gpuGlow">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        {/* Render layers bottom-to-top so top layers overlay */}
        {[...layers].reverse().map((layer, ri) => {
          const i = layers.length - 1 - ri;
          const yShift = sep * layer.sepMul;
          const cy = 100 + layer.baseY + yShift;
          const lx = 80;
          const lw = 360;
          const isActive = (layer.id === "die" && activeStep >= 1) || (layer.id === "pcb" && activeStep >= 2);

          return (
            <g
              key={layer.id}
              style={{
                transition: "transform 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
                transform: `translateY(${yShift}px)`,
              }}
            >
              {/* 3D depth - bottom face */}
              <path
                d={`M ${lx} ${cy + layer.h} L ${lx + 8} ${cy + layer.h + 5} L ${lx + lw + 8} ${cy + layer.h + 5} L ${lx + lw} ${cy + layer.h} Z`}
                fill={layer.color}
                opacity="0.4"
              />
              {/* 3D depth - right face */}
              <path
                d={`M ${lx + lw} ${cy} L ${lx + lw + 8} ${cy + 5} L ${lx + lw + 8} ${cy + layer.h + 5} L ${lx + lw} ${cy + layer.h} Z`}
                fill={layer.color}
                opacity="0.6"
              />

              {/* Main face */}
              <rect
                x={lx} y={cy} width={lw} height={layer.h} rx="4"
                fill={
                  layer.id === "pcb" ? "url(#gpuPcbGrad)"
                  : layer.id === "heatsink" ? "url(#gpuHeatGrad)"
                  : layer.id === "die" ? "url(#gpuDieGrad)"
                  : layer.color
                }
                stroke={layer.stroke}
                strokeWidth={isActive ? "1.5" : "0.8"}
                opacity="0.9"
              />

              {/* Active glow */}
              {isActive && (
                <rect
                  x={lx} y={cy} width={lw} height={layer.h} rx="4"
                  fill="none"
                  stroke={layer.stroke}
                  strokeWidth="2"
                  filter="url(#gpuGlow)"
                  opacity="0.6"
                >
                  <animate attributeName="opacity" values="0.3;0.7;0.3" dur="2s" repeatCount="indefinite" />
                </rect>
              )}

              {/* Layer-specific details */}
              {layer.id === "shroud" && (
                <>
                  {/* RADEON text */}
                  <text x={lx + lw / 2} y={cy + 20} textAnchor="middle" fill="#c00c3d" fontSize="14" fontWeight="bold" fontFamily="Arial, sans-serif" letterSpacing="3" opacity="0.7">RADEON</text>
                  {/* Triple fan cutouts */}
                  {[0, 1, 2].map((fi) => (
                    <circle key={fi} cx={lx + 70 + fi * 110} cy={cy + 45} r="25" fill="none" stroke="#333" strokeWidth="1.5" opacity="0.5" />
                  ))}
                </>
              )}

              {layer.id === "fans" && (
                <>
                  {/* Fan blades - spinning */}
                  {[0, 1, 2].map((fi) => (
                    <g key={fi}>
                      <circle cx={lx + 70 + fi * 110} cy={cy + 28} r="22" fill="#1a1a1e" stroke="#444" strokeWidth="0.5" />
                      {[0, 60, 120, 180, 240, 300].map((angle) => (
                        <line
                          key={angle}
                          x1={lx + 70 + fi * 110}
                          y1={cy + 28}
                          x2={lx + 70 + fi * 110 + Math.cos(angle * Math.PI / 180) * 18}
                          y2={cy + 28 + Math.sin(angle * Math.PI / 180) * 18}
                          stroke="#555"
                          strokeWidth="2"
                          strokeLinecap="round"
                          opacity="0.4"
                        >
                          <animateTransform
                            attributeName="transform"
                            type="rotate"
                            from={`0 ${lx + 70 + fi * 110} ${cy + 28}`}
                            to={`360 ${lx + 70 + fi * 110} ${cy + 28}`}
                            dur={`${2 + fi * 0.3}s`}
                            repeatCount="indefinite"
                          />
                        </line>
                      ))}
                      <circle cx={lx + 70 + fi * 110} cy={cy + 28} r="4" fill="#333" stroke="#555" strokeWidth="0.5" />
                    </g>
                  ))}
                </>
              )}

              {layer.id === "heatsink" && (
                <>
                  {/* Fin lines */}
                  {Array.from({ length: 20 }, (_, fi) => (
                    <line key={fi} x1={lx + 15 + fi * 17} y1={cy + 4} x2={lx + 15 + fi * 17} y2={cy + layer.h - 4} stroke="#555" strokeWidth="0.5" opacity="0.3" />
                  ))}
                  {/* Copper heatpipes */}
                  {[0.3, 0.5, 0.7].map((pos, pi) => (
                    <line key={pi} x1={lx + 10} y1={cy + layer.h * pos} x2={lx + lw - 10} y2={cy + layer.h * pos} stroke="url(#copperGrad)" strokeWidth="3" strokeLinecap="round" opacity="0.6" />
                  ))}
                </>
              )}

              {layer.id === "die" && (
                <>
                  {/* GPU die chip */}
                  <rect x={lx + lw / 2 - 30} y={cy + 4} width="60" height="17" rx="2" fill="#0a0505" stroke="#c00c3d" strokeWidth="0.8" opacity="0.8" />
                  <text x={lx + lw / 2} y={cy + 16} textAnchor="middle" fill="#c00c3d" fontSize="7" fontFamily="monospace" opacity="0.5">NAVI 31</text>
                </>
              )}

              {layer.id === "pcb" && (
                <>
                  {/* Circuit traces */}
                  {Array.from({ length: 8 }, (_, ci) => (
                    <line key={ci} x1={lx + 20 + ci * 42} y1={cy + 8} x2={lx + 25 + ci * 42} y2={cy + layer.h - 8} stroke="#1a4a22" strokeWidth="0.6" opacity="0.4" />
                  ))}
                  {/* Chip placeholders */}
                  {[0.2, 0.5, 0.8].map((pos, ci) => (
                    <rect key={ci} x={lx + lw * pos - 12} y={cy + 15} width="24" height="10" rx="1" fill="#0a0a0a" stroke="#2d5a35" strokeWidth="0.5" opacity="0.5" />
                  ))}
                  <text x={lx + 15} y={cy + layer.h - 8} fill="#1a4a22" fontSize="6" fontFamily="monospace" opacity="0.3">AMD RDNA 3 - RX 7900 XTX</text>
                </>
              )}

              {layer.id === "vrm" && (
                <>
                  {/* VRM modules */}
                  {Array.from({ length: 12 }, (_, vi) => (
                    <rect key={vi} x={lx + 12 + vi * 28} y={cy + 4} width="20" height="12" rx="1" fill="#2a2008" stroke="#8a7020" strokeWidth="0.5" opacity="0.5" />
                  ))}
                </>
              )}

              {layer.id === "backplate" && (
                <>
                  <text x={lx + lw - 15} y={cy + layer.h - 8} textAnchor="end" fill="#444" fontSize="8" fontFamily="Arial, sans-serif" letterSpacing="2" opacity="0.3">7900 XTX</text>
                </>
              )}

              {/* Label - visible when separated */}
              <text
                x={lx - 10}
                y={cy + layer.h / 2 + 3}
                textAnchor="end"
                fill="white"
                fontSize="9"
                fontFamily="monospace"
                opacity={sep > 30 ? 0.35 : 0}
                style={{ transition: "opacity 0.8s" }}
              >
                {layer.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Bottom label */}
      <div className="absolute bottom-4 left-0 right-0 text-center">
        <span className="text-[11px] font-mono text-white/20">
          AMD Radeon RX 7900 XTX
        </span>
      </div>

      {/* Edge vignette */}
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-t from-[oklch(0.09_0.01_260)] via-transparent to-[oklch(0.09_0.01_260)]/40" />
    </div>
  );
}

const steps = [
  {
    number: "01",
    title: "Enter",
    subtitle: "what you see",
    description: "Type what the nurse observes. Enter whatever vitals are available. RORY works with as little as two.",
  },
  {
    number: "02",
    title: "Analyze",
    subtitle: "under 2 seconds",
    description: "Two AI models read the text and vitals together, then check for unusual patterns and track trends.",
  },
  {
    number: "03",
    title: "Decide",
    subtitle: "with reasoning",
    description: "HOME, ED, or 911. Every recommendation comes with a confidence score and an explanation of why.",
  },
];

export function HowItWorksSection() {
  const [activeStep, setActiveStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const sectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setIsVisible(true);
      },
      { threshold: 0.1 }
    );

    if (sectionRef.current) observer.observe(sectionRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % steps.length);
    }, 3500);
    return () => clearInterval(interval);
  }, []);

  return (
    <section
      id="how-it-works"
      ref={sectionRef}
      className="relative py-24 lg:py-32 bg-[oklch(0.09_0.01_260)] text-white overflow-hidden"
    >
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full bg-white/[0.02] blur-[100px] pointer-events-none" />

      <div className="relative z-10 max-w-[1400px] mx-auto px-6 lg:px-12">
        <div className="relative mb-0 lg:mb-0 grid lg:grid-cols-2 gap-4 lg:gap-12 items-end">
          <div className="overflow-hidden pb-0 lg:pb-32">
            <div className={`transition-all duration-1000 ${isVisible ? "translate-x-0 opacity-100" : "-translate-x-12 opacity-0"}`}>
              <span className="inline-flex items-center gap-3 text-sm font-mono text-white/40 mb-8">
                <span className="w-12 h-px bg-white/20" />
                Process
              </span>
            </div>

            <h2 className={`text-6xl md:text-7xl lg:text-[128px] font-display tracking-tight leading-[0.85] transition-all duration-1000 delay-100 ${
              isVisible ? "translate-y-0 opacity-100" : "translate-y-16 opacity-0"
            }`}>
              <span className="block">Enter.</span>
              <span className="block text-white/30">Analyze.</span>
              <span className="block text-white/10">Decide.</span>
            </h2>
          </div>

          <div className={`relative h-[320px] lg:h-[640px] overflow-hidden transition-all duration-1000 delay-200 ${
            isVisible ? "opacity-100" : "opacity-0"
          }`}>
            <GpuAnimation activeStep={activeStep} />
            {/* Vignette edges */}
            <div className="absolute inset-0 pointer-events-none" style={{
              boxShadow: "inset 0 0 80px 40px oklch(0.09 0.01 260), inset 0 0 160px 60px oklch(0.09 0.01 260 / 0.6)"
            }} />
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-4">
          {steps.map((step, index) => {
            const active = activeStep === index;
            return (
              <button
                key={step.number}
                type="button"
                onClick={() => setActiveStep(index)}
                className={`relative text-left overflow-hidden transition-all duration-500 ${
                  active
                    ? "bg-[#000000] border border-white/40 shadow-[0_0_40px_rgba(239,68,68,0.06)]"
                    : "bg-[#000000] border border-white/10 hover:border-white/25"
                }`}
              >
                {/* Background glow when active */}
                {active && (
                  <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-[#ef4444]/[0.04] to-transparent pointer-events-none" />
                )}

                <div className="relative p-8 lg:p-10">
                  {/* Number + progress */}
                  <div className="flex items-center gap-3 mb-6">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center border transition-all duration-500 ${
                      active
                        ? "border-[#ef4444]/60 bg-[#ef4444]/10"
                        : "border-white/10 bg-white/[0.02]"
                    }`}>
                      <span className={`text-sm font-mono transition-colors duration-300 ${
                        active ? "text-[#ef4444]" : "text-white/25"
                      }`}>
                        {step.number}
                      </span>
                    </div>
                    <div className="flex-1 h-px bg-white/[0.06] overflow-hidden rounded-full">
                      {active && (
                        <div className="h-full bg-gradient-to-r from-[#ef4444]/70 to-[#ef4444]/20 animate-progress rounded-full" />
                      )}
                    </div>
                  </div>

                  {/* Title */}
                  <h3 className={`text-4xl lg:text-5xl font-display mb-1 transition-colors duration-500 ${
                    active ? "text-white" : "text-white/60"
                  }`}>
                    {step.title}
                  </h3>
                  <span className={`text-sm font-mono block mb-5 transition-colors duration-500 ${
                    active ? "text-[#ef4444]/70" : "text-white/20"
                  }`}>
                    {step.subtitle}
                  </span>

                  {/* Visual element per card */}
                  {index === 0 && (
                    <div className={`flex gap-1.5 mb-5 transition-opacity duration-500 ${active ? "opacity-100" : "opacity-30"}`}>
                      {["Temp", "HR", "SpO2", "RR", "Cap"].map((v, vi) => (
                        <div key={v} className={`h-1 flex-1 rounded-full ${vi < 2 ? "bg-[#ef4444]/40" : "bg-white/[0.06]"}`} />
                      ))}
                    </div>
                  )}
                  {index === 1 && (
                    <div className={`flex items-center gap-2 mb-5 transition-opacity duration-500 ${active ? "opacity-100" : "opacity-30"}`}>
                      <div className="h-6 w-6 rounded border border-white/10 bg-white/[0.03] flex items-center justify-center">
                        <div className="w-2 h-2 rounded-sm bg-[#ef4444]/40" />
                      </div>
                      <div className="flex-1 h-px bg-white/[0.08]" />
                      <div className="h-6 w-6 rounded border border-white/10 bg-white/[0.03] flex items-center justify-center">
                        <div className="w-2 h-2 rounded-sm bg-[#ef4444]/40" />
                      </div>
                      <div className="flex-1 h-px bg-white/[0.08]" />
                      <div className="h-6 w-8 rounded border border-[#ef4444]/20 bg-[#ef4444]/[0.06] flex items-center justify-center">
                        <div className="w-3 h-1 rounded-full bg-[#ef4444]/50" />
                      </div>
                    </div>
                  )}
                  {index === 2 && (
                    <div className={`flex items-center gap-3 mb-5 transition-opacity duration-500 ${active ? "opacity-100" : "opacity-30"}`}>
                      {[
                        { label: "HOME", c: "bg-green-500/30 border-green-500/20" },
                        { label: "ED", c: "bg-yellow-500/20 border-yellow-500/15" },
                        { label: "911", c: "bg-[#ef4444]/30 border-[#ef4444]/20" },
                      ].map((o) => (
                        <span key={o.label} className={`text-[9px] font-mono px-2.5 py-1 rounded border ${o.c}`}>
                          {o.label}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Description */}
                  <p className={`text-sm leading-relaxed transition-all duration-500 ${
                    active ? "text-white/50" : "text-white/25"
                  }`}>
                    {step.description}
                  </p>
                </div>

                {/* Bottom progress bar */}
                <div className={`absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#ef4444] to-[#ef4444]/40 transition-transform duration-300 origin-left ${
                  active ? "scale-x-100" : "scale-x-0"
                }`} />
              </button>
            );
          })}
        </div>
      </div>

      <style jsx>{`
        @keyframes progress {
          from { width: 0%; }
          to { width: 100%; }
        }
        .animate-progress {
          animation: progress 3.5s linear forwards;
        }
      `}</style>
    </section>
  );
}
