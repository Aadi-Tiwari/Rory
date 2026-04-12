import { motion } from "framer-motion";
import { useEffect, useState } from "react";

const LINES = [
  "In 2012, Rory Staunton scraped his arm playing basketball.",
  "He developed sepsis. He was sent home twice.",
  "He died 4 days later. He was 12 years old.",
  "We built this for him.",
];

interface Props {
  onComplete: () => void;
  photoUrl?: string;
}

export default function RorySplash({ onComplete, photoUrl = "/rory_staunton.jpg" }: Props) {
  const [lineIndex, setLineIndex] = useState(0);

  useEffect(() => {
    if (lineIndex < LINES.length) {
      const timer = setTimeout(() => setLineIndex(lineIndex + 1), 1800);
      return () => clearTimeout(timer);
    }
    const timer = setTimeout(onComplete, 2000);
    return () => clearTimeout(timer);
  }, [lineIndex, onComplete]);

  return (
    <div className="fixed inset-0 bg-black flex items-center justify-center z-50">
      <div className="max-w-2xl px-8 text-center">
        <motion.img
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.85 }}
          transition={{ duration: 2 }}
          src={photoUrl}
          alt="Rory Staunton"
          className="w-48 h-48 rounded-full mx-auto mb-8 grayscale object-cover"
          onError={(e) => {
            // Fallback to silhouette if photo not found
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />
        <div className="space-y-4 text-white text-xl font-light">
          {LINES.slice(0, lineIndex).map((line, i) => (
            <motion.p
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 0.9, y: 0 }}
              transition={{ duration: 1.2 }}
            >
              {line}
            </motion.p>
          ))}
        </div>
      </div>
    </div>
  );
}
