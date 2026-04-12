"use client";

import { useState } from "react";
import { AnimatePresence } from "framer-motion";
import { Navigation } from "@/components/landing/navigation";
import { HeroSection } from "@/components/landing/hero-section";
import { FeaturesSection } from "@/components/landing/features-section";
import { HowItWorksSection } from "@/components/landing/how-it-works-section";
import { ArchitectureSection } from "@/components/landing/architecture-section";
import { MetricsSection } from "@/components/landing/metrics-section";
import { TechStackSection } from "@/components/landing/tech-stack-section";
import { CaseStudiesSection } from "@/components/landing/case-studies-section";
import { SettingsSection } from "@/components/landing/settings-section";
import { CtaSection } from "@/components/landing/cta-section";
import { ForRoryClose } from "@/components/landing/for-rory-close";
import { FooterSection } from "@/components/landing/footer-section";
import { RorySplash } from "@/components/landing/rory-splash";

export default function Home() {
  const [showSplash, setShowSplash] = useState(true);

  return (
    <>
      <AnimatePresence>
        {showSplash && <RorySplash onComplete={() => setShowSplash(false)} />}
      </AnimatePresence>

      <main className="relative min-h-screen overflow-x-hidden">
        <Navigation />
        <HeroSection />
        <FeaturesSection />
        <HowItWorksSection />
        <ArchitectureSection />
        <MetricsSection />
        <TechStackSection />
        <CaseStudiesSection />
        <SettingsSection />
        <CtaSection />
        <ForRoryClose />
        <FooterSection />
      </main>
    </>
  );
}
