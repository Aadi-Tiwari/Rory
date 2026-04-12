"use client";

import { useEffect, useState, useRef } from "react";
import { ArrowLeft, ArrowRight } from "lucide-react";

const cases = [
  {
    quote: "9-year-old girl. Fever 101, runny nose, mom says 'just a cold.' RORY confirms: viral mimic. Send home with confidence.",
    author: "Case 1",
    role: "Viral Mimic",
    company: "School Nurse Setting",
    metric: { value: "HOME", label: "Risk: 0.00" },
  },
  {
    quote: "12-year-old boy. Scraped arm 2 days ago, now fever 104, leg pain, looks pale. This is Rory Staunton. RORY catches it instantly.",
    author: "Case 2",
    role: "Rory Staunton 2012",
    company: "Emergency Department",
    metric: { value: "911", label: "Risk: 1.00" },
  },
  {
    quote: "Same 12-year-old, but the school nurse only has temperature and heart rate. RORY still flags it red - lowered threshold compensates for missing vitals.",
    author: "Case 3",
    role: "Rory - Limited Vitals",
    company: "School Nurse Setting",
    metric: { value: "911", label: "Risk: 1.00" },
  },
];

export function CaseStudiesSection() {
  const [activeIndex, setActiveIndex] = useState(0);
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

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % cases.length);
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  const goTo = (index: number) => {
    setActiveIndex(index);
  };

  const goPrev = () => {
    setActiveIndex((prev) => (prev - 1 + cases.length) % cases.length);
  };

  const goNext = () => {
    setActiveIndex((prev) => (prev + 1) % cases.length);
  };

  const activeCase = cases[activeIndex];

  return (
    <section id="cases" ref={sectionRef} className="relative py-32 lg:py-40 bg-foreground text-background overflow-hidden">
      <div className="absolute inset-0 font-mono text-[10px] text-background/[0.02] leading-tight overflow-hidden whitespace-pre select-none" suppressHydrationWarning>
        {Array.from({ length: 60 }, (_, i) =>
          Array.from({ length: 100 }, (__, j) => {
            const seed = (i * 100 + j) * 2654435761;
            return ((seed >>> 16) & 0xff) > 180 ? "+" : " ";
          }).join("")
        ).join("\n")}
      </div>

      <div className="relative z-10 max-w-[1400px] mx-auto px-6 lg:px-12">
        <div className="flex items-center justify-between mb-20">
          <div>
            <span className="inline-flex items-center gap-3 text-sm font-mono text-background/40 mb-4">
              <span className="w-12 h-px bg-background/20" />
              Validated Cases
            </span>
            <h2 className={`text-4xl lg:text-5xl font-display transition-all duration-1000 ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
            }`}>
              Three cases,
              <span className="text-background/40"> three outcomes.</span>
            </h2>
          </div>

          <div className="hidden lg:flex items-center gap-2">
            <button
              onClick={goPrev}
              className="p-4 border border-background/20 hover:bg-background/10 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <button
              onClick={goNext}
              className="p-4 border border-background/20 hover:bg-background/10 transition-colors"
            >
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="grid lg:grid-cols-12 gap-12 lg:gap-20">
          <div className="lg:col-span-7 relative">
            <span className="absolute -left-4 -top-8 text-[200px] font-display text-background/5 leading-none select-none">
              &ldquo;
            </span>

            <div className="relative">
              <blockquote
                key={activeIndex}
                className="text-3xl lg:text-4xl xl:text-5xl font-display leading-[1.2] tracking-tight animate-fadeSlideIn"
              >
                {activeCase.quote}
              </blockquote>

              <div className="mt-12 flex items-center gap-6">
                <div className={`w-14 h-14 rounded-full flex items-center justify-center text-xl font-display ${
                  activeCase.metric.value === "911"
                    ? "bg-red-500/20 text-red-300"
                    : "bg-green-500/20 text-green-300"
                }`}>
                  {activeCase.author.split(" ")[1]}
                </div>
                <div>
                  <p className="text-lg font-medium">{activeCase.role}</p>
                  <p className="text-background/60">
                    {activeCase.company}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 flex flex-col justify-center gap-6">
            <div
              key={`metric-${activeIndex}`}
              className="p-10 border border-background/20 bg-background/5 animate-fadeSlideIn"
            >
              <span className={`text-7xl lg:text-8xl font-display block mb-4 ${
                activeCase.metric.value === "911"
                  ? "text-red-400"
                  : activeCase.metric.value === "ED"
                    ? "text-yellow-400"
                    : "text-green-400"
              }`}>
                {activeCase.metric.value}
              </span>
              <span className="text-lg text-background/60">
                {activeCase.metric.label}
              </span>
            </div>

            <div className="flex gap-2">
              {cases.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => goTo(idx)}
                  className="flex-1 h-1 bg-background/20 overflow-hidden"
                >
                  <div
                    className={`h-full bg-background transition-all duration-300 ${
                      idx === activeIndex ? "w-full" : idx < activeIndex ? "w-full opacity-50" : "w-0"
                    }`}
                    style={idx === activeIndex ? { animation: "progress 8s linear forwards" } : {}}
                  />
                </button>
              ))}
            </div>

            <div className="mt-4 pt-6 border-t border-background/10">
              <span className="text-xs font-mono text-background/30 uppercase tracking-widest block mb-4">
                Demo scenarios
              </span>
              <div className="flex flex-wrap gap-3">
                {cases.map((c, idx) => (
                  <button
                    key={c.role}
                    onClick={() => goTo(idx)}
                    className={`px-4 py-2 text-sm border transition-all ${
                      idx === activeIndex
                        ? "border-background/40 text-background"
                        : "border-background/10 text-background/40 hover:border-background/30"
                    }`}
                  >
                    {c.role}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes fadeSlideIn {
          from {
            opacity: 0;
            transform: translateX(20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        .animate-fadeSlideIn {
          animation: fadeSlideIn 0.5s ease-out forwards;
        }
        @keyframes progress {
          from { width: 0%; }
          to { width: 100%; }
        }
      `}</style>
    </section>
  );
}
