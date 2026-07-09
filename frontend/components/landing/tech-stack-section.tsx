"use client";

import { useEffect, useState, useRef } from "react";
import { Brain, Cpu, Server, Database, Activity, BarChart3, Layout, FileText, Shield, Layers, GitBranch, Zap } from "lucide-react";

const techIcons: Record<string, React.ReactNode> = {
  "Bio_ClinicalBERT": <Brain className="w-6 h-6" />,
  "PyTorch": <Cpu className="w-6 h-6" />,
  "FastAPI": <Zap className="w-6 h-6" />,
  "Palantir Foundry": <Database className="w-6 h-6" />,
  "DBSCAN": <Activity className="w-6 h-6" />,
  "scikit-learn": <BarChart3 className="w-6 h-6" />,
  "React": <Layout className="w-6 h-6" />,
  "Pydantic v2": <FileText className="w-6 h-6" />,
  "AIP Logic": <Shield className="w-6 h-6" />,
  "Ontology API": <Layers className="w-6 h-6" />,
  "NumPy": <GitBranch className="w-6 h-6" />,
  "Transformers": <Server className="w-6 h-6" />,
};

const technologies = [
  { name: "Bio_ClinicalBERT", category: "NLP" },
  { name: "PyTorch", category: "ML" },
  { name: "FastAPI", category: "API" },
  { name: "Palantir Foundry", category: "Platform" },
  { name: "DBSCAN", category: "Clustering" },
  { name: "scikit-learn", category: "ML" },
  { name: "React", category: "Frontend" },
  { name: "Pydantic v2", category: "Contract" },
  { name: "AIP Logic", category: "AI" },
  { name: "Ontology API", category: "Data" },
  { name: "NumPy", category: "Compute" },
  { name: "Transformers", category: "HF" },
];

export function TechStackSection() {
  const [isVisible, setIsVisible] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);
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
    <section id="tech" ref={sectionRef} className="relative overflow-hidden">
      <div className="relative z-10 pt-32 lg:pt-40 text-center">
        <span className={`inline-flex items-center gap-4 text-sm font-mono text-muted-foreground mb-8 transition-all duration-700 justify-center ${
          isVisible ? "opacity-100" : "opacity-0"
        }`}>
          <span className="w-12 h-px bg-foreground/20" />
          Technology
          <span className="w-12 h-px bg-foreground/20" />
        </span>

        <h2 className={`text-6xl md:text-7xl lg:text-[128px] font-display tracking-tight leading-[0.9] transition-all duration-1000 ${
          isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
        }`}>
          Powered by
          <br />
          <span className="text-muted-foreground">Palantir.</span>
        </h2>

        <p className={`mt-8 text-xl text-muted-foreground leading-relaxed max-w-lg mx-auto transition-all duration-1000 delay-100 ${
          isVisible ? "opacity-100" : "opacity-0"
        }`}>
          Built on Palantir Foundry and AIP. Ontology, Document Intelligence, and AI Logic
          working together to turn raw predictions into auditable clinical decisions.
        </p>
      </div>

      <div className="relative z-10 mt-16 lg:mt-24 max-w-[1400px] mx-auto px-6 lg:px-12">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-16">
          {technologies.map((tech, index) => (
            <div
              key={tech.name}
              className={`group relative overflow-hidden p-6 lg:p-8 border transition-all duration-500 cursor-default ${
                hoveredIndex === index
                  ? "border-foreground bg-foreground/[0.04] scale-[1.02]"
                  : "border-foreground/10 hover:border-foreground/30"
              } ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
              style={{
                transitionDelay: `${index * 30 + 300}ms`,
              }}
              onMouseEnter={(e) => {
                setHoveredIndex(index);
                const rect = e.currentTarget.getBoundingClientRect();
                setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
              }}
              onMouseMove={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
              }}
              onMouseLeave={() => {
                setHoveredIndex(null);
                setMousePos(null);
              }}
            >
              {hoveredIndex === index && mousePos && (
                <span
                  aria-hidden="true"
                  className="pointer-events-none absolute inset-0 z-0"
                  style={{
                    background: `radial-gradient(200px circle at ${mousePos.x}px ${mousePos.y}px, rgba(255,255,255,0.1) 0%, transparent 70%)`,
                  }}
                />
              )}
              <span className={`absolute top-3 right-3 text-[10px] font-mono px-2 py-0.5 transition-colors ${
                hoveredIndex === index
                  ? "bg-foreground text-background"
                  : "bg-foreground/10 text-muted-foreground"
              }`}>
                {tech.category}
              </span>

              <div className={`w-10 h-10 mb-6 flex items-center justify-center transition-colors ${
                hoveredIndex === index ? "text-white" : "text-foreground/60"
              }`}>
                {techIcons[tech.name]}
              </div>

              <span className="font-medium block">{tech.name}</span>

              <div className="absolute bottom-0 left-0 right-0 h-px bg-foreground/20 overflow-hidden">
                <div className={`h-full bg-foreground transition-all duration-500 ${
                  hoveredIndex === index ? "w-full" : "w-0"
                }`} />
              </div>
            </div>
          ))}
        </div>

        <div className={`flex flex-wrap items-center justify-between gap-8 pt-12 border-t border-foreground/10 transition-all duration-1000 delay-500 pb-32 lg:pb-40 ${
          isVisible ? "opacity-100" : "opacity-0"
        }`}>
          <div className="flex flex-wrap gap-12">
            {[
              { value: "12", label: "Core technologies" },
              { value: "Pydantic", label: "Shared contract" },
              { value: "REST", label: "API protocol" },
            ].map((stat) => (
              <div key={stat.label} className="flex items-baseline gap-3">
                <span className="text-3xl font-display">{stat.value}</span>
                <span className="text-sm text-muted-foreground">{stat.label}</span>
              </div>
            ))}
          </div>

          <a href="https://github.com/Tiwari-Aadi/Rory" target="_blank" rel="noopener noreferrer" className="group inline-flex items-center gap-2 text-sm font-mono text-muted-foreground hover:text-foreground transition-colors">
            View source on GitHub
            <span className="group-hover:translate-x-1 transition-transform">&rarr;</span>
          </a>
        </div>
      </div>
    </section>
  );
}
