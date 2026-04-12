"use client";

import { useState, useEffect, useRef } from "react";

const features = [
  {
    title: "Pydantic v2 contract",
    description: "Shared schema between both backends. Type-safe, validated at boundaries."
  },
  {
    title: "Adaptive imputation",
    description: "Missing vitals? Mean imputation + confidence penalty. No crashes, just honesty."
  },
  {
    title: "Ring buffer drift",
    description: "Last 5 embeddings tracked via cosine distance to sepsis centroid."
  },
  {
    title: "Cached demo mode",
    description: "Pre-computed responses for 3 demo cases. Works without GPU or model weights."
  },
];

export function DevelopersSection() {
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
    <section id="developers" ref={sectionRef} className="relative py-24 lg:py-32 overflow-hidden">
      {/* Background code watermark */}
      <div
        className={`absolute bottom-0 right-0 w-[55%] h-[85%] pointer-events-none transition-all duration-1000 delay-300 ${
          isVisible ? "opacity-100" : "opacity-0"
        }`}
      >
        <div className="w-full h-full flex items-center justify-center opacity-[0.04]">
          <pre className="text-xs font-mono text-foreground leading-relaxed whitespace-pre overflow-hidden">
{`from inference.predict import predict
from inference.drift import DriftMonitor
from inference.dbscan_outlier import check_outlier
from models.fusion_model import FusionModel

class TriagePipeline:
    def __init__(self):
        self.model = FusionModel.load("best_model.pt")
        self.drift = DriftMonitor(buffer_size=5)
        self.dbscan = load("dbscan.pkl")

    def run(self, req: PredictRequest):
        text_emb = self.model.encode_text(
            req.complaint_text
        )
        vital_emb = self.model.encode_vitals(
            req.vitals, impute_missing=True
        )
        fused = torch.cat([text_emb, vital_emb])
        logits = self.model.fusion_head(fused)

        outlier = self.dbscan.predict(fused)
        drift = self.drift.update(fused)

        completeness = count_present(req.vitals) / 5
        confidence = softmax(logits).max()
        if completeness < 1.0:
            confidence *= (0.7 + 0.3 * completeness)

        return PredictResponse(
            recommendation=argmax(logits),
            risk=softmax(logits)[SEPSIS],
            confidence=confidence,
            completeness=completeness,
            outlier_flag=(outlier == -1),
            drift_alert=(drift > 0.7),
            cluster_drift=drift,
        )`}
          </pre>
        </div>
        <div className="absolute inset-0 bg-gradient-to-r from-background via-background/60 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-b from-background via-transparent to-transparent" />
      </div>

      <div className="relative z-10 max-w-[1400px] mx-auto px-6 lg:px-12">
        <div
          className={`mb-16 transition-all duration-700 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <span className="inline-flex items-center gap-3 text-sm font-mono text-muted-foreground mb-6">
            <span className="w-8 h-px bg-foreground/30" />
            Under the Hood
          </span>
          <h2 className="text-6xl md:text-7xl lg:text-[128px] font-display tracking-tight leading-[0.9]">
            Built to catch
            <br />
            <span className="text-muted-foreground">what humans miss.</span>
          </h2>
        </div>

        <div
          className={`max-w-[50%] transition-all duration-700 delay-100 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <p className="text-xl text-muted-foreground mb-12 leading-relaxed max-w-md">
            A predict pipeline that combines text encoding, vital sign normalization,
            outlier detection, and drift monitoring in a single forward pass.
          </p>
          <div className="grid grid-cols-2 gap-6">
            {features.map((feature, index) => (
              <div
                key={feature.title}
                className={`transition-all duration-500 ${
                  isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
                }`}
                style={{ transitionDelay: `${index * 50 + 200}ms` }}
              >
                <h3 className="font-medium mb-1">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
