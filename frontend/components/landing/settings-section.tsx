"use client";

import { useState, useEffect, useRef } from "react";
import { ArrowRight, Check, Zap } from "lucide-react";

const settings = [
  {
    name: "School Nurse",
    description: "Limited vitals, maximum sensitivity",
    vitals: "Temp + HR",
    features: [
      "Temperature and heart rate only",
      "Highest sensitivity threshold",
      "HOME or ED recommendation",
      "Confidence penalty for missing vitals",
      "Mean imputation for absent fields",
    ],
    cta: "Most common setting",
    highlight: false,
  },
  {
    name: "Pediatric ED",
    description: "Full vital suite, standard protocol",
    vitals: "All 5 vitals",
    features: [
      "HR, RR, Temp, SpO2, Cap Refill",
      "Standard SIRS thresholds",
      "HOME, ED, or 911 recommendation",
      "Full DBSCAN outlier detection",
      "Cluster drift monitoring",
      "Rory's Regulations citations",
      "Complete reasoning chain",
    ],
    cta: "Full capability",
    highlight: true,
  },
  {
    name: "Emergency Dept",
    description: "All vitals plus sepsis protocol",
    vitals: "All + protocol",
    features: [
      "All vitals with lab integration",
      "Lowest sepsis threshold",
      "911 escalation priority",
      "Full audit trail",
      "Protocol citation system",
      "Pediatric SSC compliance",
      "Real-time drift alerts",
      "Outlier flagging",
    ],
    cta: "Maximum safety",
    highlight: false,
  },
];

export function SettingsSection() {
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
    <section id="settings" ref={sectionRef} className="relative py-32 lg:py-40">
      <div className="max-w-[1400px] mx-auto px-6 lg:px-12">
        <div className="grid lg:grid-cols-12 gap-8 mb-20">
          <div className="lg:col-span-7">
            <span className="inline-flex items-center gap-3 text-sm font-mono text-muted-foreground mb-8">
              <span className="w-12 h-px bg-foreground/30" />
              Settings
            </span>
            <h2 className={`text-6xl md:text-7xl lg:text-[128px] font-display tracking-tight leading-[0.9] transition-all duration-1000 ${
              isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
            }`}>
              Three settings.
              <br />
              <span className="text-stroke">One mission.</span>
            </h2>
          </div>

          <div className="lg:col-span-5 flex items-end">
            <p className={`text-xl text-muted-foreground leading-relaxed transition-all duration-1000 delay-100 ${
              isVisible ? "opacity-100" : "opacity-0"
            }`}>
              RORY adapts to wherever the nurse is. School office with a thermometer, pediatric ED with full monitoring, or emergency department with sepsis protocol.
            </p>
          </div>
        </div>

        <div className="relative">
          <div className="grid lg:grid-cols-3 gap-4 lg:gap-0">
            {settings.map((setting, index) => (
              <div
                key={setting.name}
                className={`relative bg-background border transition-all duration-700 ${
                  setting.highlight
                    ? "border-foreground lg:-mx-2 lg:z-10 lg:scale-105"
                    : "border-foreground/10 lg:first:-mr-2 lg:last:-ml-2"
                } ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"}`}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                {setting.highlight && (
                  <div className="absolute -top-4 left-8 right-8 flex justify-center">
                    <span className="inline-flex items-center gap-2 px-4 py-2 bg-foreground text-background text-xs font-mono uppercase tracking-widest">
                      <Zap className="w-3 h-3" />
                      Primary Use
                    </span>
                  </div>
                )}

                <div className="p-8 lg:p-10">
                  <div className="mb-8 pb-8 border-b border-foreground/10">
                    <span className="font-mono text-xs text-muted-foreground">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <h3 className="text-2xl lg:text-3xl font-display mt-2">{setting.name}</h3>
                    <p className="text-sm text-muted-foreground mt-2">{setting.description}</p>
                  </div>

                  <div className="mb-8">
                    <span className="text-4xl font-display">{setting.vitals}</span>
                    <p className="text-xs text-muted-foreground mt-2 font-mono">
                      available at intake
                    </p>
                  </div>

                  <ul className="space-y-3 mb-10">
                    {setting.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-3">
                        <Check className="w-4 h-4 text-[#ef4444] mt-0.5 shrink-0" />
                        <span className="text-sm text-muted-foreground">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <a
                    href="/demo"
                    aria-label={`${setting.cta}: open Rory demo`}
                    className={`w-full py-4 flex items-center justify-center gap-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-foreground ${
                      setting.highlight
                        ? "bg-foreground text-background hover:bg-foreground/90"
                        : "border border-foreground/20 text-foreground hover:bg-foreground/5"
                    }`}
                  >
                    {setting.cta}
                    <ArrowRight className="w-4 h-4" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={`mt-20 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8 pt-12 border-t border-foreground/10 transition-all duration-1000 delay-500 ${
          isVisible ? "opacity-100" : "opacity-0"
        }`}>
          <div className="flex flex-wrap gap-6 text-sm text-muted-foreground">
            <span className="flex items-center gap-2">
              <Check className="w-4 h-4 text-[#ef4444]" />
              Adaptive dimensionality
            </span>
            <span className="flex items-center gap-2">
              <Check className="w-4 h-4 text-[#ef4444]" />
              Confidence-weighted output
            </span>
            <span className="flex items-center gap-2">
              <Check className="w-4 h-4 text-[#ef4444]" />
              Mean imputation for missing vitals
            </span>
          </div>
        </div>
      </div>

      <style jsx>{`
        .text-stroke {
          -webkit-text-stroke: 1.5px currentColor;
          -webkit-text-fill-color: transparent;
        }
      `}</style>
    </section>
  );
}
