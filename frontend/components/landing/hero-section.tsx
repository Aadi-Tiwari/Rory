"use client";

import { useEffect, useState, useRef } from "react";

const words = ["detects", "alerts", "protects", "saves"];

function BlurWord({ word, trigger }: { word: string; trigger: number }) {
  const letters = word.split("");
  const STAGGER = 45;
  const DURATION = 500;
  const GRADIENT_HOLD = STAGGER * letters.length + DURATION + 200;

  const [letterStates, setLetterStates] = useState<{ opacity: number; blur: number }[]>(
    letters.map(() => ({ opacity: 0, blur: 20 }))
  );
  const [showGradient, setShowGradient] = useState(true);
  const framesRef = useRef<number[]>([]);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    framesRef.current.forEach(cancelAnimationFrame);
    timersRef.current.forEach(clearTimeout);
    framesRef.current = [];
    timersRef.current = [];

    setLetterStates(letters.map(() => ({ opacity: 0, blur: 20 })));
    setShowGradient(true);

    letters.forEach((_, i) => {
      const t = setTimeout(() => {
        const start = performance.now();
        const tick = (now: number) => {
          const progress = Math.min((now - start) / DURATION, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          setLetterStates(prev => {
            const next = [...prev];
            next[i] = { opacity: eased, blur: 20 * (1 - eased) };
            return next;
          });
          if (progress < 1) {
            const id = requestAnimationFrame(tick);
            framesRef.current.push(id);
          }
        };
        const id = requestAnimationFrame(tick);
        framesRef.current.push(id);
      }, i * STAGGER);
      timersRef.current.push(t);
    });

    const gt = setTimeout(() => setShowGradient(false), GRADIENT_HOLD);
    timersRef.current.push(gt);

    return () => {
      framesRef.current.forEach(cancelAnimationFrame);
      timersRef.current.forEach(clearTimeout);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trigger]);

  const gradientColors = ["#ef4444", "#f97316", "#fbbf24", "#ef4444", "#f97316"];

  return (
    <>
      {letters.map((char, i) => {
        const colorIndex = (i / Math.max(letters.length - 1, 1)) * (gradientColors.length - 1);
        const lower = Math.floor(colorIndex);
        const upper = Math.min(lower + 1, gradientColors.length - 1);
        const t = colorIndex - lower;

        const hex2rgb = (hex: string) => {
          const r = parseInt(hex.slice(1, 3), 16);
          const g = parseInt(hex.slice(3, 5), 16);
          const b = parseInt(hex.slice(5, 7), 16);
          return [r, g, b];
        };
        const [r1, g1, b1] = hex2rgb(gradientColors[lower]);
        const [r2, g2, b2] = hex2rgb(gradientColors[upper]);
        const r = Math.round(r1 + (r2 - r1) * t);
        const g = Math.round(g1 + (g2 - g1) * t);
        const b = Math.round(b1 + (b2 - b1) * t);

        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              opacity: letterStates[i]?.opacity ?? 0,
              filter: `blur(${letterStates[i]?.blur ?? 20}px)`,
              color: showGradient ? `rgb(${r},${g},${b})` : "white",
              transition: "color 0.4s ease",
            }}
          >
            {char}
          </span>
        );
      })}
    </>
  );
}

function NervousSystemCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let w = 0;
    let h = 0;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = rect.width;
      h = rect.height;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener("resize", resize);

    // --- Build the nerve network once ---

    interface Neuron {
      x: number; y: number;
      radius: number;
      firePhase: number;   // where in its fire cycle (0 = dormant)
      fireCooldown: number;
      fireRate: number;    // seconds between spontaneous fires
      connections: number[];
    }

    interface Signal {
      from: number;
      to: number;
      progress: number; // 0..1
      speed: number;
    }

    // Seed-based pseudo-random for deterministic layout
    let seed = 42;
    const rng = () => { seed = (seed * 16807 + 0) % 2147483647; return (seed - 1) / 2147483646; };

    // Generate neurons spread across the canvas
    const NEURON_COUNT = 80;
    const neurons: Neuron[] = [];
    for (let i = 0; i < NEURON_COUNT; i++) {
      neurons.push({
        x: rng() * 1.1 - 0.05, // normalized 0..1 with slight overflow
        y: rng() * 1.1 - 0.05,
        radius: 1.5 + rng() * 2.5,
        firePhase: 0,
        fireCooldown: rng() * 8,
        fireRate: 4 + rng() * 10,
        connections: [],
      });
    }

    // Connect nearby neurons (like dendrites)
    const MAX_DIST = 0.18;
    const MAX_CONNECTIONS = 4;
    for (let i = 0; i < neurons.length; i++) {
      const distances: { idx: number; dist: number }[] = [];
      for (let j = 0; j < neurons.length; j++) {
        if (i === j) continue;
        const dx = neurons[i].x - neurons[j].x;
        const dy = neurons[i].y - neurons[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < MAX_DIST) distances.push({ idx: j, dist });
      }
      distances.sort((a, b) => a.dist - b.dist);
      neurons[i].connections = distances.slice(0, MAX_CONNECTIONS).map(d => d.idx);
    }

    const signals: Signal[] = [];

    // Fire a neuron: create signals to all its connections
    const fireNeuron = (idx: number) => {
      const n = neurons[idx];
      if (n.firePhase > 0) return; // already firing
      n.firePhase = 1.0;
      n.fireCooldown = n.fireRate;
      for (const target of n.connections) {
        signals.push({
          from: idx,
          to: target,
          progress: 0,
          speed: 0.3 + rng() * 0.5,
        });
      }
    };

    let time = 0;
    const dt = 0.016;

    const render = () => {
      ctx.clearRect(0, 0, w, h);

      // --- Update ---
      time += dt;

      // Spontaneous fires
      for (let i = 0; i < neurons.length; i++) {
        const n = neurons[i];
        n.fireCooldown -= dt;
        if (n.fireCooldown <= 0) {
          fireNeuron(i);
        }
        // Decay fire glow
        if (n.firePhase > 0) {
          n.firePhase = Math.max(0, n.firePhase - dt * 1.8);
        }
      }

      // Update signals
      for (let i = signals.length - 1; i >= 0; i--) {
        const s = signals[i];
        s.progress += dt * s.speed;
        if (s.progress >= 1) {
          // Signal arrived - trigger target neuron
          fireNeuron(s.to);
          signals.splice(i, 1);
        }
      }

      // --- Draw ---

      // Draw connections (dendrites/axons) as subtle curves
      ctx.lineWidth = 0.5;
      for (let i = 0; i < neurons.length; i++) {
        const n = neurons[i];
        const nx = n.x * w;
        const ny = n.y * h;
        for (const j of n.connections) {
          if (j <= i) continue; // draw each connection once
          const m = neurons[j];
          const mx = m.x * w;
          const my = m.y * h;

          // Curve via midpoint offset
          const midX = (nx + mx) / 2 + (n.y - m.y) * w * 0.08;
          const midY = (ny + my) / 2 + (m.x - n.x) * h * 0.08;

          ctx.beginPath();
          ctx.moveTo(nx, ny);
          ctx.quadraticCurveTo(midX, midY, mx, my);
          ctx.strokeStyle = "rgba(239, 68, 68, 0.04)";
          ctx.stroke();
        }
      }

      // Draw signals traveling along connections
      for (const s of signals) {
        const from = neurons[s.from];
        const to = neurons[s.to];
        const fx = from.x * w;
        const fy = from.y * h;
        const tx = to.x * w;
        const ty = to.y * h;
        const midX = (fx + tx) / 2 + (from.y - to.y) * w * 0.08;
        const midY = (fy + ty) / 2 + (to.x - from.x) * h * 0.08;

        // Quadratic bezier interpolation
        const t = s.progress;
        const px = (1 - t) * (1 - t) * fx + 2 * (1 - t) * t * midX + t * t * tx;
        const py = (1 - t) * (1 - t) * fy + 2 * (1 - t) * t * midY + t * t * ty;

        // Bright glow for the signal
        const intensity = Math.sin(t * Math.PI); // brightest in middle
        ctx.save();
        ctx.shadowColor = `rgba(239, 120, 80, ${0.6 * intensity})`;
        ctx.shadowBlur = 12;
        ctx.beginPath();
        ctx.arc(px, py, 2 + intensity * 1.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 160, 100, ${0.7 * intensity})`;
        ctx.fill();
        ctx.restore();

        // Trail
        const trailLen = 0.12;
        for (let ti = 1; ti <= 3; ti++) {
          const tt = Math.max(0, t - trailLen * ti * 0.3);
          const tpx = (1 - tt) * (1 - tt) * fx + 2 * (1 - tt) * tt * midX + tt * tt * tx;
          const tpy = (1 - tt) * (1 - tt) * fy + 2 * (1 - tt) * tt * midY + tt * tt * ty;
          ctx.beginPath();
          ctx.arc(tpx, tpy, 1.2 - ti * 0.2, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(239, 100, 70, ${0.15 / ti})`;
          ctx.fill();
        }

        // Light up the connection path as signal passes
        ctx.beginPath();
        ctx.moveTo(fx, fy);
        ctx.quadraticCurveTo(midX, midY, tx, ty);
        ctx.strokeStyle = `rgba(239, 120, 80, ${0.06 * intensity})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Draw neurons (cell bodies)
      for (const n of neurons) {
        const nx = n.x * w;
        const ny = n.y * h;

        // Glow when firing
        if (n.firePhase > 0) {
          ctx.save();
          ctx.shadowColor = `rgba(239, 130, 90, ${0.6 * n.firePhase})`;
          ctx.shadowBlur = 15 * n.firePhase;
          ctx.beginPath();
          ctx.arc(nx, ny, n.radius + 3 * n.firePhase, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255, 170, 120, ${0.5 * n.firePhase})`;
          ctx.fill();
          ctx.restore();

          // Expanding ring
          const ringR = n.radius + 12 * (1 - n.firePhase);
          ctx.beginPath();
          ctx.arc(nx, ny, ringR, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(239, 120, 80, ${0.15 * n.firePhase})`;
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }

        // Resting neuron body
        ctx.beginPath();
        ctx.arc(nx, ny, n.radius, 0, Math.PI * 2);
        const restAlpha = 0.06 + n.firePhase * 0.4;
        ctx.fillStyle = `rgba(239, 100, 80, ${restAlpha})`;
        ctx.fill();
      }

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

export function HeroSection() {
  const [isVisible, setIsVisible] = useState(false);
  const [wordIndex, setWordIndex] = useState(0);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setWordIndex((prev) => (prev + 1) % words.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="relative min-h-screen flex flex-col justify-center items-start overflow-hidden bg-black">
      {/* Background gradient */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-[#0a0a0a] via-[#0f0a0a] to-[#0a0a12]" />
        <NervousSystemCanvas />
        <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/30 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-transparent to-black/60" />
      </div>

      {/* Subtle grid lines */}
      <div className="absolute inset-0 z-[2] overflow-hidden pointer-events-none opacity-20">
        {[...Array(8)].map((_, i) => (
          <div
            key={`h-${i}`}
            className="absolute h-px bg-white/10"
            style={{
              top: `${12.5 * (i + 1)}%`,
              left: 0,
              right: 0,
            }}
          />
        ))}
        {[...Array(12)].map((_, i) => (
          <div
            key={`v-${i}`}
            className="absolute w-px bg-white/10"
            style={{
              left: `${8.33 * (i + 1)}%`,
              top: 0,
              bottom: 0,
            }}
          />
        ))}
      </div>

      <div className="relative z-10 w-full max-w-[1400px] mx-auto px-6 lg:px-12 py-32 lg:py-40">
        <div className="lg:max-w-[55%]">
          <div
            className={`mb-8 transition-all duration-700 ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            }`}
          >
            <span className="inline-flex items-center gap-3 text-sm font-mono text-white/60">
              <span className="w-8 h-px bg-white/30" />
              Pediatric sepsis early-warning system
            </span>
          </div>

          <div className="mb-12">
            <h1
              className={`text-left text-[clamp(2rem,6vw,7rem)] font-display leading-[0.92] tracking-tight text-white transition-all duration-1000 ${
                isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
              }`}
            >
              <span className="block whitespace-nowrap">90 seconds to decide,</span>
              <span className="block whitespace-nowrap">
                a model that{" "}
                <span className="relative inline-block">
                  <BlurWord word={words[wordIndex]} trigger={wordIndex} />
                </span>
              </span>
            </h1>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div
        className={`absolute bottom-12 left-0 right-0 px-6 lg:px-12 transition-all duration-700 delay-500 ${
          isVisible ? "opacity-100" : "opacity-0"
        }`}
      >
        <div className="max-w-[1400px] mx-auto flex items-start gap-10 lg:gap-20">
          {[
            { value: "1,948", label: "synthetic cases trained" },
            { value: "99.7%", label: "sepsis sensitivity" },
            { value: "<2s", label: "end-to-end inference" },
          ].map((stat) => (
            <div key={stat.label} className="flex flex-col gap-2">
              <span className="text-3xl lg:text-4xl font-display text-white">{stat.value}</span>
              <span className="text-xs text-white/50 leading-tight">
                {stat.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
