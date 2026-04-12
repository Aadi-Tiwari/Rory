"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

const LINES = [
  "In 2012, Rory Staunton scraped his arm playing basketball.",
  "He developed sepsis. He was sent home twice.",
  "He died 4 days later. He was 12 years old.",
  "We built this so it never happens again.",
];

interface Props {
  onComplete: () => void;
}

export function RorySplash({ onComplete }: Props) {
  const [lineIndex, setLineIndex] = useState(0);

  useEffect(() => {
    if (lineIndex < LINES.length) {
      const timer = setTimeout(() => setLineIndex(lineIndex + 1), 2000);
      return () => clearTimeout(timer);
    }
    const timer = setTimeout(onComplete, 2200);
    return () => clearTimeout(timer);
  }, [lineIndex, onComplete]);

  return (
    <motion.div
      className="fixed inset-0 bg-black flex items-center justify-center z-[100]"
      exit={{ opacity: 0 }}
      transition={{ duration: 1 }}
    >
      <div className="max-w-2xl px-8 text-center">
        {/* Large R monogram instead of photo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 0.6, scale: 1 }}
          transition={{ duration: 2 }}
          className="w-32 h-32 rounded-full border border-white/10 flex items-center justify-center mx-auto mb-12"
        >
          <span className="text-6xl font-display text-white/40">R</span>
        </motion.div>

        <div className="space-y-5 text-white">
          {LINES.slice(0, lineIndex).map((line, i) => (
            <motion.p
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: i === LINES.length - 1 ? 1 : 0.7, y: 0 }}
              transition={{ duration: 1.5 }}
              className={`text-xl lg:text-2xl font-display leading-relaxed ${i === LINES.length - 1 ? "text-white" : "text-white/70"}`}
            >
              {line}
            </motion.p>
          ))}
        </div>

        {/* Skip hint */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.15 }}
          transition={{ delay: 3, duration: 1 }}
          className="text-xs font-mono text-white mt-16 cursor-pointer"
          onClick={onComplete}
        >
          click to skip
        </motion.p>
      </div>
    </motion.div>
  );
}
