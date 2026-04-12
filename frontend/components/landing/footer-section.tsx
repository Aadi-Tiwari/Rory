"use client";

import { ArrowUpRight } from "lucide-react";
import { useEffect, useRef } from "react";

const footerLinks = {
  System: [
    { name: "Capabilities", href: "#features" },
    { name: "How it works", href: "#how-it-works" },
    { name: "Technology", href: "#tech" },
    { name: "Compliance", href: "#compliance" },
  ],
  Architecture: [
    { name: "Backend A - ML", href: "#architecture" },
    { name: "Backend B - Foundry", href: "#architecture" },
    { name: "Shared Contract", href: "#tech" },
    { name: "Demo Cases", href: "#cases" },
  ],
  Project: [
    { name: "Los Altos Hacks X", href: "#" },
    { name: "GitHub", href: "https://github.com/Tiwari-Aadi/Rory-Test" },
    { name: "Rory's Regulations", href: "#compliance" },
  ],
};

const socialLinks = [
  { name: "GitHub", href: "https://github.com/Tiwari-Aadi/Rory-Test" },
  { name: "Devpost", href: "#" },
];

function AnimatedWaveCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    let time = 0;

    const resize = () => {
      canvas.width = canvas.offsetWidth * window.devicePixelRatio;
      canvas.height = canvas.offsetHeight * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };
    resize();
    window.addEventListener("resize", resize);

    const animate = () => {
      const width = canvas.offsetWidth;
      const height = canvas.offsetHeight;
      ctx.clearRect(0, 0, width, height);

      // ECG-style waves in red
      for (let wave = 0; wave < 3; wave++) {
        ctx.beginPath();
        ctx.strokeStyle = `rgba(239, 68, 68, ${0.08 - wave * 0.02})`;
        ctx.lineWidth = 1;

        for (let x = 0; x <= width; x += 3) {
          const phase = (x / width) * Math.PI * 6 + time + wave * 1.5;
          const cycle = phase % (Math.PI * 2);

          let y;
          if (cycle < 1.3) {
            y = Math.sin(cycle * 2.4) * 15;
          } else if (cycle < 1.6) {
            y = Math.sin((cycle - 1.3) * Math.PI / 0.3) * 40;
          } else {
            y = Math.sin(cycle * 0.8) * 8;
          }

          const baseY = height * 0.5 + wave * 20;
          if (x === 0) ctx.moveTo(x, baseY + y);
          else ctx.lineTo(x, baseY + y);
        }
        ctx.stroke();
      }

      time += 0.02;
      animationId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationId);
    };
  }, []);

  return <canvas ref={canvasRef} className="w-full h-full" />;
}

export function FooterSection() {
  return (
    <footer className="relative bg-black">
      {/* Top border line */}
      <div className="w-full h-px bg-white/10" />

      <div className="relative z-10 max-w-[1400px] mx-auto px-6 lg:px-12">
        <div className="py-16 lg:py-20">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-12 lg:gap-8">
            <div className="col-span-2">
              <a href="#" className="inline-flex items-center gap-2 mb-6">
                <span className="text-2xl font-display text-white">RORY</span>
              </a>

              <p className="text-white/50 leading-relaxed mb-4 max-w-xs text-sm">
                Pediatric sepsis early-warning system. A tablet a nurse uses in the first 90 seconds of seeing a child.
              </p>
              <p className="text-white/30 leading-relaxed mb-8 max-w-xs text-xs italic">
                Named after Rory Staunton (1999-2012), who died of septic shock after being sent home from the ER twice.
              </p>

              <div className="flex gap-6">
                {socialLinks.map((link) => (
                  <a
                    key={link.name}
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-white/40 hover:text-white transition-colors flex items-center gap-1 group"
                  >
                    {link.name}
                    <ArrowUpRight className="w-3 h-3 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                  </a>
                ))}
              </div>
            </div>

            {Object.entries(footerLinks).map(([title, links]) => (
              <div key={title}>
                <h3 className="text-sm font-medium text-white mb-6">{title}</h3>
                <ul className="space-y-4">
                  {links.map((link) => (
                    <li key={link.name}>
                      <a
                        href={link.href}
                        className="text-sm text-white/40 hover:text-white transition-colors inline-flex items-center gap-2"
                      >
                        {link.name}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        <div className="py-8 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-white/30">
            Los Altos Hacks X - April 2026
          </p>

          <div className="flex items-center gap-4 text-sm text-white/30">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#ef4444]" />
              For Rory.
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
