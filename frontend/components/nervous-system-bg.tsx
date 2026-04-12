"use client";

import { useEffect, useRef } from "react";

export function NervousSystemBg({ opacity = 1 }: { opacity?: number }) {
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

    interface Neuron { x: number; y: number; radius: number; firePhase: number; fireCooldown: number; fireRate: number; connections: number[]; }
    interface Signal { from: number; to: number; progress: number; speed: number; }

    let seed = 42;
    const rng = () => { seed = (seed * 16807 + 0) % 2147483647; return (seed - 1) / 2147483646; };

    const NEURON_COUNT = 80;
    const neurons: Neuron[] = [];
    for (let i = 0; i < NEURON_COUNT; i++) {
      neurons.push({ x: rng() * 1.1 - 0.05, y: rng() * 1.1 - 0.05, radius: 1.5 + rng() * 2.5, firePhase: 0, fireCooldown: rng() * 2, fireRate: 1 + rng() * 3, connections: [] });
    }

    const MAX_DIST = 0.18, MAX_CONNECTIONS = 4;
    for (let i = 0; i < neurons.length; i++) {
      const dists: { idx: number; dist: number }[] = [];
      for (let j = 0; j < neurons.length; j++) {
        if (i === j) continue;
        const dx = neurons[i].x - neurons[j].x, dy = neurons[i].y - neurons[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < MAX_DIST) dists.push({ idx: j, dist });
      }
      dists.sort((a, b) => a.dist - b.dist);
      neurons[i].connections = dists.slice(0, MAX_CONNECTIONS).map(d => d.idx);
    }

    const signals: Signal[] = [];
    const fireNeuron = (idx: number) => {
      const n = neurons[idx];
      if (n.firePhase > 0) return;
      n.firePhase = 1.0; n.fireCooldown = n.fireRate;
      for (const target of n.connections) signals.push({ from: idx, to: target, progress: 0, speed: 0.8 + rng() * 1.2 });
    };

    let time = 0;
    const dt = 0.016;

    const render = () => {
      ctx.clearRect(0, 0, w, h);
      time += dt;

      for (let i = 0; i < neurons.length; i++) {
        neurons[i].fireCooldown -= dt;
        if (neurons[i].fireCooldown <= 0) fireNeuron(i);
        if (neurons[i].firePhase > 0) neurons[i].firePhase = Math.max(0, neurons[i].firePhase - dt * 3.5);
      }

      for (let i = signals.length - 1; i >= 0; i--) {
        signals[i].progress += dt * signals[i].speed;
        if (signals[i].progress >= 1) { fireNeuron(signals[i].to); signals.splice(i, 1); }
      }

      // Connections
      ctx.lineWidth = 0.5;
      for (let i = 0; i < neurons.length; i++) {
        const n = neurons[i], nx = n.x * w, ny = n.y * h;
        for (const j of n.connections) {
          if (j <= i) continue;
          const m = neurons[j], mx = m.x * w, my = m.y * h;
          const midX = (nx + mx) / 2 + (n.y - m.y) * w * 0.08;
          const midY = (ny + my) / 2 + (m.x - n.x) * h * 0.08;
          ctx.beginPath(); ctx.moveTo(nx, ny); ctx.quadraticCurveTo(midX, midY, mx, my);
          ctx.strokeStyle = "rgba(239, 68, 68, 0.04)"; ctx.stroke();
        }
      }

      // Signals
      for (const s of signals) {
        const from = neurons[s.from], to = neurons[s.to];
        const fx = from.x * w, fy = from.y * h, tx = to.x * w, ty = to.y * h;
        const midX = (fx + tx) / 2 + (from.y - to.y) * w * 0.08;
        const midY = (fy + ty) / 2 + (to.x - from.x) * h * 0.08;
        const t = s.progress;
        const px = (1-t)*(1-t)*fx + 2*(1-t)*t*midX + t*t*tx;
        const py = (1-t)*(1-t)*fy + 2*(1-t)*t*midY + t*t*ty;
        const intensity = Math.sin(t * Math.PI);
        ctx.save();
        ctx.shadowColor = `rgba(239, 120, 80, ${0.6 * intensity})`; ctx.shadowBlur = 12;
        ctx.beginPath(); ctx.arc(px, py, 2 + intensity * 1.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 160, 100, ${0.7 * intensity})`; ctx.fill();
        ctx.restore();
        for (let ti = 1; ti <= 3; ti++) {
          const tt = Math.max(0, t - 0.12 * ti * 0.3);
          const tpx = (1-tt)*(1-tt)*fx + 2*(1-tt)*tt*midX + tt*tt*tx;
          const tpy = (1-tt)*(1-tt)*fy + 2*(1-tt)*tt*midY + tt*tt*ty;
          ctx.beginPath(); ctx.arc(tpx, tpy, 1.2 - ti * 0.2, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(239, 100, 70, ${0.15 / ti})`; ctx.fill();
        }
        ctx.beginPath(); ctx.moveTo(fx, fy); ctx.quadraticCurveTo(midX, midY, tx, ty);
        ctx.strokeStyle = `rgba(239, 120, 80, ${0.06 * intensity})`; ctx.lineWidth = 1.5; ctx.stroke();
      }

      // Neurons
      for (const n of neurons) {
        const nx = n.x * w, ny = n.y * h;
        if (n.firePhase > 0) {
          ctx.save();
          ctx.shadowColor = `rgba(239, 130, 90, ${0.6 * n.firePhase})`; ctx.shadowBlur = 15 * n.firePhase;
          ctx.beginPath(); ctx.arc(nx, ny, n.radius + 3 * n.firePhase, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255, 170, 120, ${0.5 * n.firePhase})`; ctx.fill(); ctx.restore();
          const ringR = n.radius + 12 * (1 - n.firePhase);
          ctx.beginPath(); ctx.arc(nx, ny, ringR, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(239, 120, 80, ${0.15 * n.firePhase})`; ctx.lineWidth = 0.8; ctx.stroke();
        }
        ctx.beginPath(); ctx.arc(nx, ny, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(239, 100, 80, ${0.06 + n.firePhase * 0.4})`; ctx.fill();
      }

      frameRef.current = requestAnimationFrame(render);
    };
    render();

    return () => { window.removeEventListener("resize", resize); cancelAnimationFrame(frameRef.current); };
  }, []);

  return <canvas ref={canvasRef} className="fixed inset-0 z-0 pointer-events-none" style={{ width: "100%", height: "100%", opacity }} />;
}
