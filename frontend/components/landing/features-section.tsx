"use client";

import { useEffect, useRef, useState } from "react";

// --- Dimension Transition Canvas: 2D square -> 3D cube -> 4D tesseract -> gradient ---

function DimensionCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let w = 0, h = 0;
    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = rect.width; h = rect.height;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener("resize", resize);

    // 4D tesseract vertices: all combinations of -1/+1 in 4 dimensions
    const verts4D: number[][] = [];
    for (let i = 0; i < 16; i++) {
      verts4D.push([
        (i & 1) ? 1 : -1,
        (i & 2) ? 1 : -1,
        (i & 4) ? 1 : -1,
        (i & 8) ? 1 : -1,
      ]);
    }

    // Edges: connect vertices that differ in exactly one coordinate
    const edges4D: number[][] = [];
    for (let i = 0; i < 16; i++) {
      for (let j = i + 1; j < 16; j++) {
        let diff = 0;
        for (let k = 0; k < 4; k++) {
          if (verts4D[i][k] !== verts4D[j][k]) diff++;
        }
        if (diff === 1) edges4D.push([i, j]);
      }
    }

    // 3D cube vertices and edges
    const verts3D = [
      [-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
      [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1],
    ];
    const edges3D = [
      [0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],
      [0,4],[1,5],[2,6],[3,7],
    ];

    // 2D square vertices and edges
    const verts2D = [[-1,-1],[1,-1],[1,1],[-1,1]];
    const edges2D = [[0,1],[1,2],[2,3],[3,0]];

    // Rotation helpers
    const rot4D = (v: number[], a: number, b: number): number[] => {
      const out = [...v];
      // XW rotation
      const c1 = Math.cos(a), s1 = Math.sin(a);
      const x = out[0] * c1 - out[3] * s1;
      const ww = out[0] * s1 + out[3] * c1;
      out[0] = x; out[3] = ww;
      // YZ rotation
      const c2 = Math.cos(b), s2 = Math.sin(b);
      const y = out[1] * c2 - out[2] * s2;
      const z = out[1] * s2 + out[2] * c2;
      out[1] = y; out[2] = z;
      return out;
    };

    const rot3D = (v: number[], ax: number, ay: number): number[] => {
      let [x, y, z] = v;
      // Y-axis
      const c1 = Math.cos(ay), s1 = Math.sin(ay);
      const x2 = x * c1 + z * s1;
      const z2 = -x * s1 + z * c1;
      x = x2; z = z2;
      // X-axis
      const c2 = Math.cos(ax), s2 = Math.sin(ax);
      const y2 = y * c2 - z * s2;
      const z3 = y * s2 + z * c2;
      return [x, y2, z3];
    };

    // Project 4D -> 2D screen
    const project4D = (v4: number[], scale: number): [number, number] => {
      const d4 = 3;
      const persp4 = d4 / (d4 - v4[3]);
      const x3 = v4[0] * persp4;
      const y3 = v4[1] * persp4;
      const z3 = v4[2] * persp4;
      const d3 = 4;
      const persp3 = d3 / (d3 - z3);
      return [x3 * persp3 * scale, y3 * persp3 * scale];
    };

    // Project 3D -> 2D screen
    const project3D = (v3: number[], scale: number): [number, number] => {
      const d = 4;
      const persp = d / (d - v3[2]);
      return [v3[0] * persp * scale, v3[1] * persp * scale];
    };

    // Phase timing - fast transitions
    const PHASE_HOLD = 0.6;
    const PHASE_MORPH = 0.3;
    const CYCLE = (PHASE_HOLD + PHASE_MORPH) * 4;

    const ease = (t: number) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

    const labels = ["2D", "3D", "4D", "256D"];
    const sublabels = ["square", "cube", "tesseract", "embedding space"];

    let time = 0;

    const render = () => {
      ctx.clearRect(0, 0, w, h);

      const cx = w / 2;
      const cy = h / 2;
      const scale = Math.min(w, h) * 0.25;

      time += 0.016;
      const loopTime = time % CYCLE;
      const phaseLen = PHASE_HOLD + PHASE_MORPH;

      const phaseIdx = Math.floor(loopTime / phaseLen);
      const phaseTime = loopTime - phaseIdx * phaseLen;
      const morphT = phaseTime > PHASE_HOLD
        ? ease((phaseTime - PHASE_HOLD) / PHASE_MORPH)
        : 0;

      const currentPhase = phaseIdx % 4;
      const nextPhase = (phaseIdx + 1) % 4;

      // Faster, more dramatic rotation
      const rotA = time * 1.2;
      const rotB = time * 0.9;

      const drawShape = (phase: number, alpha: number) => {
        if (phase === 0) {
          // 2D Square
          const pts = verts2D.map(v => {
            const a = Math.atan2(v[1], v[0]) + time * 0.3;
            const r = Math.sqrt(v[0] * v[0] + v[1] * v[1]);
            return [Math.cos(a) * r * scale + cx, Math.sin(a) * r * scale + cy] as [number, number];
          });
          drawEdges(pts, edges2D, alpha, [239, 68, 68]);
          drawVertices(pts, alpha, [239, 68, 68]);
        } else if (phase === 1) {
          // 3D Cube
          const pts = verts3D.map(v => {
            const r = rot3D(v, rotA * 0.7, rotB);
            const [px, py] = project3D(r, scale);
            return [px + cx, py + cy] as [number, number];
          });
          drawEdges(pts, edges3D, alpha, [251, 146, 60]);
          drawVertices(pts, alpha, [251, 146, 60]);
        } else if (phase === 2) {
          // 4D Tesseract
          const pts = verts4D.map(v => {
            const r = rot4D(v, rotA, rotB);
            const [px, py] = project4D(r, scale);
            return [px + cx, py + cy] as [number, number];
          });
          drawEdges(pts, edges4D, alpha, [168, 130, 255]);
          drawVertices(pts, alpha, [168, 130, 255]);
        } else {
          // 256D: gradient particle cloud
          drawGradientCloud(alpha);
        }
      };

      const drawEdges = (pts: [number, number][], edges: number[][], alpha: number, color: number[]) => {
        // Outer glow layer
        ctx.save();
        ctx.shadowColor = `rgba(${color[0]},${color[1]},${color[2]},${0.6 * alpha})`;
        ctx.shadowBlur = 15;
        ctx.lineWidth = 4;
        ctx.strokeStyle = `rgba(${color[0]},${color[1]},${color[2]},${0.08 * alpha})`;
        for (const [i, j] of edges) {
          ctx.beginPath();
          ctx.moveTo(pts[i][0], pts[i][1]);
          ctx.lineTo(pts[j][0], pts[j][1]);
          ctx.stroke();
        }
        ctx.restore();

        // Core edge
        ctx.lineWidth = 1.8;
        for (const [i, j] of edges) {
          // Animated shimmer along edge
          const edgePhase = (i + j) * 0.5 + time * 2;
          const shimmer = 0.3 + 0.15 * Math.sin(edgePhase);
          ctx.beginPath();
          ctx.moveTo(pts[i][0], pts[i][1]);
          ctx.lineTo(pts[j][0], pts[j][1]);
          ctx.strokeStyle = `rgba(${color[0]},${color[1]},${color[2]},${shimmer * alpha})`;
          ctx.stroke();
        }
      };

      const drawVertices = (pts: [number, number][], alpha: number, color: number[]) => {
        for (let vi = 0; vi < pts.length; vi++) {
          const [px, py] = pts[vi];
          const pulse = 0.6 + 0.4 * Math.sin(vi * 1.7 + time * 3);

          // Outer glow ring
          ctx.save();
          ctx.shadowColor = `rgba(${color[0]},${color[1]},${color[2]},${0.7 * alpha * pulse})`;
          ctx.shadowBlur = 12;
          ctx.beginPath();
          ctx.arc(px, py, 3.5 * pulse, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${color[0]},${color[1]},${color[2]},${0.5 * alpha})`;
          ctx.fill();
          ctx.restore();

          // Bright white core
          ctx.beginPath();
          ctx.arc(px, py, 1.8, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255,255,255,${0.7 * alpha * pulse})`;
          ctx.fill();
        }
      };

      const drawGradientCloud = (alpha: number) => {
        const count = 180;

        // Central nebula glow
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, scale * 1.2);
        grad.addColorStop(0, `rgba(239, 80, 80, ${0.06 * alpha})`);
        grad.addColorStop(0.4, `rgba(168, 100, 255, ${0.03 * alpha})`);
        grad.addColorStop(1, `rgba(0, 0, 0, 0)`);
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);

        for (let i = 0; i < count; i++) {
          const phi = (i * 2.399963) + time * 0.35;
          const cosTheta = 1 - (2 * (i + 0.5)) / count;
          const sinTheta = Math.sqrt(1 - cosTheta * cosTheta);
          const r = scale * (0.5 + 0.5 * Math.sin(i * 0.7 + time * 0.5));

          const x = cx + Math.cos(phi) * sinTheta * r;
          const y = cy + cosTheta * r;

          const t = i / count;
          const cr = Math.floor(200 + 55 * Math.sin(t * Math.PI * 2 + time * 0.5));
          const cg = Math.floor(60 + 120 * Math.sin(t * Math.PI * 2 + 2));
          const cb = Math.floor(100 + 155 * Math.sin(t * Math.PI * 2 + 4));

          const pulse = 0.3 + 0.7 * Math.pow(Math.sin(i * 0.3 + time * 1.2), 2);

          ctx.beginPath();
          ctx.arc(x, y, 1.5 + pulse * 1.5, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(${cr},${cg},${cb},${0.4 * alpha * pulse})`;
          ctx.fill();

          if (i % 6 === 0) {
            ctx.save();
            ctx.shadowColor = `rgba(${cr},${cg},${cb},${0.4 * alpha})`;
            ctx.shadowBlur = 10;
            ctx.beginPath();
            ctx.arc(x, y, 2, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255,255,255,${0.2 * alpha * pulse})`;
            ctx.fill();
            ctx.restore();
          }
        }
      };

      // Draw current shape and blend with next during morph
      if (morphT > 0) {
        drawShape(currentPhase, 1 - morphT);
        drawShape(nextPhase, morphT);
      } else {
        drawShape(currentPhase, 1);
      }

      // Draw dimension label
      const labelPhase = morphT > 0 ? (morphT > 0.5 ? nextPhase : currentPhase) : currentPhase;
      const labelAlpha = morphT > 0
        ? (morphT > 0.5 ? (morphT - 0.5) * 2 : 1 - morphT * 2)
        : 1;

      ctx.textAlign = "center";
      ctx.fillStyle = `rgba(255,255,255,${0.5 * labelAlpha})`;
      ctx.font = `bold ${Math.min(w, h) * 0.08}px var(--font-display), Georgia, serif`;
      ctx.fillText(labels[labelPhase], cx, cy + scale + 40);

      ctx.fillStyle = `rgba(255,255,255,${0.2 * labelAlpha})`;
      ctx.font = `${Math.min(w, h) * 0.03}px var(--font-mono), monospace`;
      ctx.fillText(sublabels[labelPhase], cx, cy + scale + 60);

      frameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(frameRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none"
      style={{ width: "100%", height: "100%" }}
    />
  );
}

const features = [
  {
    number: "01",
    title: "Reads Text + Vitals Together",
    description: "The nurse types what she sees. RORY reads that text with a medical AI (Bio_ClinicalBERT) and combines it with vital sign numbers. Two signals, one decision - because fever + 'leg pain, looks pale' means more than either alone.",
    stats: { value: "2", label: "AI models fused into one" },
  },
  {
    number: "02",
    title: "Works with Missing Vitals",
    description: "School nurse only has a thermometer and a pulse? RORY still works. It fills in the gaps intelligently and lowers its confidence to tell you exactly how sure it is. No crash, no refusal - just honest answers.",
    stats: { value: "2-5", label: "vitals needed (adapts)" },
  },
  {
    number: "03",
    title: "Catches What It Has Never Seen",
    description: "RORY groups similar patients into clusters. If a new patient does not fit any known group, it raises a flag: 'this case is unusual.' Better to over-alert than to miss something the model was never trained on.",
    stats: { value: "!", label: "instant outlier alert" },
  },
  {
    number: "04",
    title: "Watches for Deterioration",
    description: "Even if each vital sign looks borderline okay, RORY tracks the overall trajectory. It remembers the last 5 readings and notices when the pattern is drifting toward sepsis - before any single number crosses a threshold.",
    stats: { value: "5", label: "readings tracked over time" },
  },
];

function ParticleVisualization() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef(0);
  const mouseRef = useRef({ x: 0.5, y: 0.5 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener("resize", resize);

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current = {
        x: (e.clientX - rect.left) / rect.width,
        y: (e.clientY - rect.top) / rect.height,
      };
    };
    canvas.addEventListener("mousemove", handleMouseMove);

    const COUNT = 70;
    const particles = Array.from({ length: COUNT }, (_, i) => {
      const seed = i * 1.618;
      return {
        bx: ((seed * 127.1) % 1),
        by: ((seed * 311.7) % 1),
        phase: seed * Math.PI * 2,
        speed: 0.4 + (seed % 0.4),
        radius: 1.2 + (seed % 2.2),
      };
    });

    let time = 0;
    const render = () => {
      const rect = canvas.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;

      ctx.clearRect(0, 0, w, h);

      const mx = mouseRef.current.x;
      const my = mouseRef.current.y;

      particles.forEach((p) => {
        const flowX = Math.sin(time * p.speed * 0.4 + p.phase) * 38;
        const flowY = Math.cos(time * p.speed * 0.3 + p.phase * 0.7) * 24;

        const bx = p.bx * w;
        const by = p.by * h;
        const dx = p.bx - mx;
        const dy = p.by - my;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const influence = Math.max(0, 1 - dist * 2.8);

        const x = bx + flowX + influence * Math.cos(time + p.phase) * 36;
        const y = by + flowY + influence * Math.sin(time + p.phase) * 36;

        const pulse = Math.sin(time * p.speed + p.phase) * 0.5 + 0.5;
        const alpha = 0.08 + pulse * 0.18 + influence * 0.3;

        ctx.beginPath();
        ctx.arc(x, y, p.radius + pulse * 0.8, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(239, 68, 68, ${alpha})`;
        ctx.fill();
      });

      time += 0.016;
      frameRef.current = requestAnimationFrame(render);
    };
    render();

    return () => {
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("mousemove", handleMouseMove);
      cancelAnimationFrame(frameRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-auto"
      style={{ width: "100%", height: "100%" }}
    />
  );
}

export function FeaturesSection() {
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

  return (
    <section
      id="features"
      ref={sectionRef}
      className="relative py-24 lg:py-32 overflow-hidden"
    >
      <div className="max-w-[1400px] mx-auto px-6 lg:px-12">
        <div className="relative mb-24 lg:mb-32">
          <div className="grid lg:grid-cols-12 gap-8 items-end">
            <div className="lg:col-span-7">
              <span className="inline-flex items-center gap-3 text-sm font-mono text-muted-foreground mb-6">
                <span className="w-12 h-px bg-foreground/30" />
                Capabilities
              </span>
              <h2
                className={`text-6xl md:text-7xl lg:text-[128px] font-display tracking-tight leading-[0.9] transition-all duration-1000 ${
                  isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
                }`}
              >
                Intelligent
                <br />
                <span className="text-muted-foreground">triage.</span>
              </h2>
            </div>
            <div className="lg:col-span-5 lg:pb-4">
              <p className={`text-xl text-muted-foreground leading-relaxed transition-all duration-1000 delay-200 ${
                isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
              }`}>
                A nurse types what she sees, enters vitals, and RORY combines both to decide: safe to go home, needs the ER, or call 911. In under 2 seconds.
              </p>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-12 gap-4 lg:gap-6">
          {/* Large feature card */}
          <div
            className={`lg:col-span-12 relative bg-black border border-foreground/10 min-h-[500px] overflow-hidden group transition-all duration-700 flex ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
            }`}
          >
            <div className="relative flex-1 p-8 lg:p-12 bg-black">
              <ParticleVisualization />
              <div className="relative z-10">
                <span className="font-mono text-sm text-muted-foreground">{features[0].number}</span>
                <h3 className="text-3xl lg:text-4xl font-display mt-4 mb-6 group-hover:translate-x-2 transition-transform duration-500">
                  {features[0].title}
                </h3>
                <p className="text-lg text-muted-foreground leading-relaxed max-w-md mb-8">
                  {features[0].description}
                </p>
                <div>
                  <span className="text-5xl lg:text-6xl font-display">{features[0].stats.value}</span>
                  <span className="block text-sm text-muted-foreground font-mono mt-2">{features[0].stats.label}</span>
                </div>
              </div>
            </div>

            {/* Right side: dimension transition animation */}
            <div className="hidden lg:flex relative w-[42%] shrink-0 overflow-hidden items-center justify-center bg-black">
              <DimensionCanvas />
              <div className="absolute inset-0 bg-gradient-to-r from-black via-transparent to-transparent pointer-events-none" />
            </div>
          </div>

          {/* Card 02: Works with Missing Vitals */}
          <div
            className={`lg:col-span-4 relative p-8 lg:p-10 bg-black border border-foreground/10 group transition-all duration-700 overflow-hidden ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
            }`}
            style={{ transitionDelay: "100ms" }}
          >
            {/* Subtle background glow */}
            <div className="absolute top-0 right-0 w-40 h-40 rounded-full bg-[#ef4444]/[0.03] blur-[60px] pointer-events-none" />

            <span className="font-mono text-sm text-muted-foreground">02</span>
            <h3 className="text-2xl font-display mt-4 mb-8 group-hover:translate-x-2 transition-transform duration-500">
              {features[1].title}
            </h3>

            {/* Vitals indicator row */}
            <div className="grid grid-cols-5 gap-2 mb-8">
              {[
                { label: "HR", lit: true, val: "138" },
                { label: "RR", lit: false, val: null },
                { label: "Temp", lit: true, val: "104" },
                { label: "SpO2", lit: false, val: null },
                { label: "Cap", lit: false, val: null },
              ].map((v) => (
                <div
                  key={v.label}
                  className={`relative rounded-lg p-3 text-center transition-all ${
                    v.lit
                      ? "bg-gradient-to-b from-[#ef4444]/15 to-[#ef4444]/5 border border-[#ef4444]/30"
                      : "bg-white/[0.02] border border-white/[0.04]"
                  }`}
                >
                  {v.lit && <div className="absolute inset-0 rounded-lg bg-[#ef4444]/5 animate-pulse" style={{ animationDuration: "3s" }} />}
                  <span className={`text-lg font-display block relative ${v.lit ? "text-white" : "text-white/10"}`}>
                    {v.val ?? "--"}
                  </span>
                  <span className={`text-[9px] font-mono block mt-1 relative ${v.lit ? "text-[#ef4444]/70" : "text-white/15"}`}>
                    {v.label}
                  </span>
                </div>
              ))}
            </div>

            {/* Confidence bar */}
            <div className="mb-6">
              <div className="flex justify-between text-[9px] font-mono text-white/25 mb-1.5">
                <span>confidence</span>
                <span className="text-white/40">72%</span>
              </div>
              <div className="h-1 bg-white/[0.06] rounded-full overflow-hidden">
                <div className="h-full rounded-full bg-gradient-to-r from-[#ef4444]/60 to-[#ef4444]/30" style={{ width: "72%" }} />
              </div>
            </div>

            <p className="text-sm text-muted-foreground leading-relaxed relative">
              Only have a thermometer and pulse? RORY still works. It adapts and tells you how confident it is.
            </p>
          </div>

          {/* Card 03: Catches the Unusual */}
          <div
            className={`lg:col-span-4 relative p-8 lg:p-10 bg-black border border-foreground/10 group transition-all duration-700 overflow-hidden ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
            }`}
            style={{ transitionDelay: "200ms" }}
          >
            <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full bg-[#ef4444]/[0.02] blur-[80px] pointer-events-none" />

            <span className="font-mono text-sm text-muted-foreground">03</span>
            <h3 className="text-2xl font-display mt-4 mb-8 group-hover:translate-x-2 transition-transform duration-500">
              {features[2].title}
            </h3>

            {/* Cluster visualization */}
            <div className="relative h-[140px] mb-8">
              {/* Known cluster - soft grouped dots with glow */}
              <div className="absolute left-6 top-4 w-24 h-24">
                <div className="absolute inset-0 rounded-full bg-[#22c55e]/[0.04] border border-[#22c55e]/10" />
                {[
                  { x: 35, y: 30 }, { x: 50, y: 45 }, { x: 42, y: 55 },
                  { x: 58, y: 35 }, { x: 48, y: 42 }, { x: 38, y: 48 },
                  { x: 55, y: 52 },
                ].map((d, i) => (
                  <div
                    key={i}
                    className="absolute w-2 h-2 rounded-full bg-[#22c55e]/50"
                    style={{ left: `${d.x}%`, top: `${d.y}%` }}
                  />
                ))}
                <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[9px] font-mono text-[#22c55e]/30">known</span>
              </div>

              {/* Second cluster */}
              <div className="absolute left-[45%] top-2 w-20 h-20">
                <div className="absolute inset-0 rounded-full bg-[#eab308]/[0.03] border border-[#eab308]/8" />
                {[
                  { x: 40, y: 35 }, { x: 55, y: 50 }, { x: 45, y: 55 },
                  { x: 52, y: 40 }, { x: 48, y: 48 },
                ].map((d, i) => (
                  <div
                    key={i}
                    className="absolute w-2 h-2 rounded-full bg-[#eab308]/40"
                    style={{ left: `${d.x}%`, top: `${d.y}%` }}
                  />
                ))}
              </div>

              {/* Outlier - dramatic */}
              <div className="absolute right-4 bottom-2">
                <div className="relative">
                  <div className="w-5 h-5 rounded-full bg-[#ef4444] shadow-[0_0_20px_rgba(239,68,68,0.5)] animate-pulse" />
                  <div className="absolute -inset-3 rounded-full border border-[#ef4444]/20 animate-ping" style={{ animationDuration: "2s" }} />
                  <div className="absolute -inset-6 rounded-full border border-[#ef4444]/10 animate-ping" style={{ animationDuration: "3s" }} />
                </div>
                <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[10px] font-mono text-[#ef4444]/60 whitespace-nowrap">outlier</span>
              </div>

              {/* Dashed connection line */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ overflow: "visible" }}>
                <line x1="55%" y1="50%" x2="82%" y2="75%" stroke="rgba(239,68,68,0.12)" strokeWidth="1" strokeDasharray="4 4" />
              </svg>
            </div>

            <p className="text-sm text-muted-foreground leading-relaxed relative">
              If a patient does not match any known pattern, RORY flags it. Better to over-alert than to miss something new.
            </p>
          </div>

          {/* Card 04: Watches for Deterioration */}
          <div
            className={`lg:col-span-4 relative p-8 lg:p-10 bg-black border border-foreground/10 group transition-all duration-700 overflow-hidden ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
            }`}
            style={{ transitionDelay: "300ms" }}
          >
            <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-[#ef4444]/[0.02] to-transparent pointer-events-none" />

            <span className="font-mono text-sm text-muted-foreground">04</span>
            <h3 className="text-2xl font-display mt-4 mb-8 group-hover:translate-x-2 transition-transform duration-500">
              {features[3].title}
            </h3>

            {/* Trend line with glowing dots */}
            <div className="relative h-[130px] mb-6">
              <svg viewBox="0 0 200 100" className="w-full h-full" style={{ overflow: "visible" }}>
                {/* Gradient fill under curve */}
                <defs>
                  <linearGradient id="trendLine" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#22c55e" />
                    <stop offset="50%" stopColor="#eab308" />
                    <stop offset="100%" stopColor="#ef4444" />
                  </linearGradient>
                  <linearGradient id="trendFill" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#22c55e" stopOpacity="0.08" />
                    <stop offset="100%" stopColor="#ef4444" stopOpacity="0.15" />
                  </linearGradient>
                </defs>

                {/* Area fill */}
                <path d="M20,80 Q55,72 80,60 Q110,45 140,32 Q165,22 185,12 L185,100 L20,100 Z" fill="url(#trendFill)" />

                {/* Trend curve */}
                <path d="M20,80 Q55,72 80,60 Q110,45 140,32 Q165,22 185,12" fill="none" stroke="url(#trendLine)" strokeWidth="2.5" strokeLinecap="round" />

                {/* Dots with glow */}
                {[
                  { x: 20, y: 80, c: "#22c55e" },
                  { x: 60, y: 68, c: "#22c55e" },
                  { x: 100, y: 52, c: "#eab308" },
                  { x: 140, y: 32, c: "#eab308" },
                  { x: 185, y: 12, c: "#ef4444" },
                ].map((pt, i) => (
                  <g key={i}>
                    <circle cx={pt.x} cy={pt.y} r="8" fill={pt.c} opacity="0.08" />
                    <circle cx={pt.x} cy={pt.y} r="4" fill={pt.c} opacity="0.6">
                      {i === 4 && <animate attributeName="r" values="4;6;4" dur="1.5s" repeatCount="indefinite" />}
                      {i === 4 && <animate attributeName="opacity" values="0.6;1;0.6" dur="1.5s" repeatCount="indefinite" />}
                    </circle>
                    <circle cx={pt.x} cy={pt.y} r="1.5" fill="white" opacity="0.8" />
                  </g>
                ))}
              </svg>

              {/* Labels */}
              <div className="absolute bottom-0 left-0 right-0 flex justify-between text-[9px] font-mono px-1">
                <span className="text-[#22c55e]/40">safe</span>
                <span className="text-[#ef4444]/40">danger</span>
              </div>
            </div>

            <p className="text-sm text-muted-foreground leading-relaxed relative">
              Tracks 5 readings over time. Even if each vital looks okay alone, RORY catches the overall trend toward danger.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
