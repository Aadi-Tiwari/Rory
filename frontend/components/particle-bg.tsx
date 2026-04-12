"use client";

import { useEffect, useRef } from "react";

export function ParticleBg() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let w = 0, h = 0, frame = 0;

    const resize = () => {
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = w;
      canvas.height = h;
    };
    resize();
    window.addEventListener("resize", resize);

    // Generate particles once
    const COUNT = 200;
    const particles = Array.from({ length: COUNT }, () => ({
      x: Math.random() * 1.2 - 0.1,
      y: Math.random() * 1.2 - 0.1,
      r: 1.5 + Math.random() * 3,
      drift: Math.random() * Math.PI * 2,
      phase: Math.random() * Math.PI * 2,
    }));

    let t = 0;
    const render = () => {
      ctx.clearRect(0, 0, w, h);
      t += 0.008;

      for (const p of particles) {
        const px = (p.x + Math.sin(t * 0.5 + p.drift) * 0.03) * w;
        const py = (p.y + Math.cos(t * 0.3 + p.phase) * 0.02) * h;
        const pulse = 0.4 + 0.6 * Math.pow((Math.sin(t + p.phase) + 1) * 0.5, 2);
        const alpha = 0.12 + pulse * 0.18;

        // Glow
        ctx.beginPath();
        ctx.arc(px, py, p.r * pulse * 2.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.15})`;
        ctx.fill();

        // Core dot
        ctx.beginPath();
        ctx.arc(px, py, p.r * pulse, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
        ctx.fill();
      }

      frame = requestAnimationFrame(render);
    };
    render();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 z-0 pointer-events-none"
      style={{ opacity: 0.8 }}
    />
  );
}
