"use client";

import { Navigation } from "@/components/landing/navigation";
import { FooterSection } from "@/components/landing/footer-section";
import { DemoContent } from "@/components/landing/demo-content";
import { GridBg } from "@/components/grid-bg";

export default function DemoPage() {
  return (
    <main className="relative min-h-screen overflow-x-hidden">
      <GridBg />
      <div className="relative z-10">
        <Navigation />
        <DemoContent />
        <FooterSection />
      </div>
    </main>
  );
}
