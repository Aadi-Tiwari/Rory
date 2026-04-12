"use client";

import { useEffect, useState, useRef } from "react";

function FatalityCounter() {
  const TARGET = 11192074;
  const [count, setCount] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setCount(0);
          setIsVisible(true);
        } else {
          setIsVisible(false);
        }
      },
      { threshold: 0.3 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!isVisible) return;
    const duration = 4000;
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out quart - starts fast, slows dramatically at end
      const eased = 1 - Math.pow(1 - progress, 4);
      setCount(Math.floor(eased * TARGET));
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [isVisible]);

  // Color: red at 0 -> gradually lighter -> white at TARGET
  const t = count / TARGET;
  const r = 239;
  const g = Math.floor(68 + (255 - 68) * t);
  const b = Math.floor(68 + (255 - 68) * t);

  return (
    <div ref={ref} className="relative py-16 lg:py-24 flex flex-col items-center justify-center text-center">
      {/* Background glow that intensifies */}
      <div
        className="absolute inset-0 pointer-events-none transition-opacity duration-1000"
        style={{
          background: `radial-gradient(ellipse at center, rgba(239,68,68,${0.04 + t * 0.02}) 0%, transparent 70%)`,
        }}
      />

      <span className="text-xs font-mono text-white/20 mb-6 tracking-widest uppercase">Lives lost to sepsis every year</span>

      <div
        className="relative font-display tabular-nums leading-none transition-all"
        style={{
          fontSize: "clamp(5rem, 18vw, 14rem)",
          color: `rgb(${r},${g},${b})`,
          textShadow: t < 0.8
            ? `0 0 ${40 - t * 30}px rgba(239,68,68,${0.3 - t * 0.25})`
            : "none",
        }}
      >
        {count.toLocaleString()}
      </div>

      <span className="text-sm text-muted-foreground mt-6 max-w-xs">
        Most of them showed symptoms that looked like the flu.
      </span>
    </div>
  );
}

export function ArchitectureSection() {
  const [isVisible, setIsVisible] = useState(false);
  const sectionRef = useRef<HTMLElement>(null);

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
    <section id="architecture" ref={sectionRef} className="relative py-32 lg:py-40 overflow-hidden">
      <div className="max-w-[1400px] mx-auto px-6 lg:px-12">
        <div className="mb-20">
          <span className={`inline-flex items-center gap-4 text-sm font-mono text-muted-foreground mb-8 transition-all duration-700 ${
            isVisible ? "opacity-100" : "opacity-0"
          }`}>
            <span className="w-12 h-px bg-foreground/20" />
            The Problem
          </span>

          <h2 className={`text-6xl md:text-7xl lg:text-[128px] font-display tracking-tight leading-[0.9] transition-all duration-1000 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}>
            Sepsis kills
            <br />
            <span className="text-muted-foreground">when missed.</span>
          </h2>

          <p className={`mt-8 text-xl text-muted-foreground leading-relaxed max-w-2xl transition-all duration-1000 delay-100 ${
            isVisible ? "opacity-100" : "opacity-0"
          }`}>
            Every year, pediatric sepsis is missed because early symptoms look like the flu.
            By the time it is obvious, it is often too late. Rory Staunton was 12.
          </p>
        </div>

        <FatalityCounter />

        {/* Rory's story cards */}
        <div className={`mt-12 grid grid-cols-1 lg:grid-cols-3 gap-4 transition-all duration-1000 delay-300 ${
          isVisible ? "opacity-100" : "opacity-0"
        }`}>
          {[
            {
              time: "Day 1",
              title: "Gym class scrape",
              desc: "Rory Staunton, 12, cuts his arm diving for a ball. Looks like nothing.",
              color: "text-[#22c55e]",
              border: "border-[#22c55e]/10",
            },
            {
              time: "Day 2",
              title: "Sent home from ER",
              desc: "Fever, vomiting, leg pain. ER runs labs but sends him home. Sepsis is already spreading.",
              color: "text-[#eab308]",
              border: "border-[#eab308]/10",
            },
            {
              time: "Day 3",
              title: "Gone",
              desc: "Rory dies of septic shock. His lab results - flagged abnormal - were never reviewed.",
              color: "text-[#ef4444]",
              border: "border-[#ef4444]/10",
            },
          ].map((event, i) => (
            <div
              key={event.time}
              className={`relative p-6 border ${event.border} bg-foreground/[0.02] transition-all duration-500`}
              style={{ transitionDelay: `${i * 100 + 400}ms` }}
            >
              <div className="flex items-center gap-3 mb-4">
                <span className={`text-xs font-mono ${event.color}`}>{event.time}</span>
                <div className="flex-1 h-px bg-foreground/[0.06]" />
              </div>
              <h4 className="font-display text-lg mb-2">{event.title}</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">{event.desc}</p>
            </div>
          ))}
        </div>

        {/* Bottom line */}
        <div className={`mt-12 pt-8 border-t border-foreground/10 transition-all duration-1000 delay-500 ${
          isVisible ? "opacity-100" : "opacity-0"
        }`}>
          <p className="text-lg text-muted-foreground max-w-2xl">
            RORY exists so that the next time a child walks into a school nurse&apos;s office or an ER with vague symptoms, the system catches what the eye might miss.
          </p>
        </div>
      </div>
    </section>
  );
}
