"use client";

import { useEffect, useState, useRef } from "react";
import { Shield, BookOpen, FileSearch, Activity } from "lucide-react";

const complianceFeatures = [
  {
    icon: Shield,
    title: "Rory's Regulations",
    description: "Full compliance with NY Public Health Law 405.4.",
  },
  {
    icon: BookOpen,
    title: "Citation system",
    description: "Every decision cites specific regulation sections and pages.",
  },
  {
    icon: FileSearch,
    title: "Audit trails",
    description: "Every prediction logged with reasoning chain and confidence.",
  },
  {
    icon: Activity,
    title: "Adaptive thresholds",
    description: "Sensitivity adjusts to clinical setting - lower threshold in schools.",
  },
];

const certifications = ["Rory's Law 405.4", "Pediatric SSC", "SIRS Criteria", "qSOFA"];

export function ComplianceSection() {
  const [isVisible, setIsVisible] = useState(false);
  const [activeFeature, setActiveFeature] = useState(0);
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
      setActiveFeature((prev) => (prev + 1) % complianceFeatures.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section id="compliance" ref={sectionRef} className="relative py-32 lg:py-40 overflow-hidden">
      <div className="max-w-[1400px] mx-auto px-6 lg:px-12">
        <div className="mb-20">
          <span className={`inline-flex items-center gap-4 text-sm font-mono text-muted-foreground mb-8 transition-all duration-700 ${
            isVisible ? "opacity-100" : "opacity-0"
          }`}>
            <span className="w-12 h-px bg-foreground/20" />
            Compliance
          </span>

          <h2 className={`text-6xl md:text-7xl lg:text-[128px] font-display tracking-tight leading-[0.9] mb-12 transition-all duration-1000 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}>
            Compliant,
            <br />
            <span className="text-muted-foreground">not just accurate.</span>
          </h2>

          <div className={`transition-all duration-1000 delay-100 ${
            isVisible ? "opacity-100" : "opacity-0"
          }`}>
            <p className="text-xl text-muted-foreground leading-relaxed max-w-2xl">
              Every recommendation maps to Rory&apos;s Regulations and Pediatric Surviving Sepsis Campaign guidelines. Auditable, explainable, defensible.
            </p>
          </div>
        </div>

        <div className="grid lg:grid-cols-12 gap-6">
          <div className={`lg:col-span-7 relative p-8 lg:p-12 border border-foreground/10 min-h-[400px] overflow-hidden transition-all duration-700 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}>
            {/* Regulations text overlay */}
            <div className="absolute inset-0 pointer-events-none items-center justify-end hidden lg:flex opacity-10 p-8">
              <pre className="text-xs font-mono text-foreground/60 leading-relaxed whitespace-pre-wrap max-w-md">
{`NY PUBLIC HEALTH LAW 405.4
Rory's Regulations

405.4.1 - Pediatric Sepsis Screening
  All emergency departments shall
  implement evidence-based protocols
  for the early identification of
  severe sepsis in pediatric patients.

405.4.2 - Mandated Response Time
  Clinical staff must initiate sepsis
  screening within 15 minutes of
  triage for any pediatric patient
  presenting with suspected infection.

405.4.3 - Documentation Requirements
  All screening results, clinical
  decisions, and interventions must
  be documented in the patient record
  with timestamps.`}
              </pre>
            </div>

            <div className="relative z-10">
              <span className="font-mono text-sm text-muted-foreground">Regulations compliance</span>
              <div className="mt-8">
                <span className="text-7xl lg:text-8xl font-display">8</span>
                <span className="block text-muted-foreground mt-2">Rory's Regulations checklist items tracked</span>
              </div>
            </div>

            <div className="absolute bottom-8 left-8 right-8 flex flex-wrap gap-2">
              {certifications.map((cert, index) => (
                <span
                  key={cert}
                  className={`px-3 py-1 border border-foreground/10 text-xs font-mono text-muted-foreground transition-all duration-500 ${
                    isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
                  }`}
                  style={{ transitionDelay: `${index * 100 + 300}ms` }}
                >
                  {cert}
                </span>
              ))}
            </div>
          </div>

          <div className="lg:col-span-5 flex flex-col gap-4">
            {complianceFeatures.map((feature, index) => (
              <div
                key={feature.title}
                className={`p-6 border transition-all duration-500 cursor-default ${
                  activeFeature === index
                    ? "border-foreground/30 bg-foreground/[0.04]"
                    : "border-foreground/10"
                } ${isVisible ? "opacity-100 translate-x-0" : "opacity-0 translate-x-8"}`}
                style={{ transitionDelay: `${index * 80}ms` }}
                onClick={() => setActiveFeature(index)}
                onMouseEnter={() => setActiveFeature(index)}
              >
                <div className="flex items-start gap-4">
                  <div className={`shrink-0 w-10 h-10 flex items-center justify-center border transition-colors ${
                    activeFeature === index
                      ? "border-foreground bg-foreground text-background"
                      : "border-foreground/20"
                  }`}>
                    <feature.icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-medium mb-1">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
