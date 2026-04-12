"use client";

import { useEffect, useRef } from "react";

export function GridBg() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let w = 0, h = 0;
    const resize = () => {
      w = window.innerWidth; h = window.innerHeight;
      canvas.width = w; canvas.height = h;
    };
    resize();
    window.addEventListener("resize", resize);

    let t = 0;
    const render = () => {
      ctx.clearRect(0, 0, w, h);
      t += 0.005;

      const gridSize = 40;

      // Draw grid dots
      for (let x = 0; x < w; x += gridSize) {
        for (let y = 0; y < h; y += gridSize) {
          const wave = Math.sin(x * 0.008 + y * 0.006 + t) * 0.5 + 0.5;
          const pulse = Math.sin(t * 2 + x * 0.01 + y * 0.01) * 0.3 + 0.7;
          const size = 0.8 + wave * 0.8;
          const alpha = 0.03 + wave * 0.04 * pulse;

          ctx.beginPath();
          ctx.arc(x, y, size, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
          ctx.fill();
        }
      }

      // Subtle horizontal scan line
      const scanY = (t * 60) % h;
      ctx.strokeStyle = "rgba(255, 255, 255, 0.008)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, scanY);
      ctx.lineTo(w, scanY);
      ctx.stroke();

      frameRef.current = requestAnimationFrame(render);
    };
    render();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(frameRef.current);
    };
  }, []);

  return <canvas ref={canvasRef} className="fixed inset-0 z-0 pointer-events-none" />;
}
