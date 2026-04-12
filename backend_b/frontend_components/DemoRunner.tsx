import { useEffect, useState } from "react";
import RorySplash from "./RorySplash";
import ForRoryClose from "./ForRoryClose";

type Phase = "splash" | "case1_mimic" | "case2_rory_ed" | "case3_rory_school" | "close";

interface DemoCase {
  phase: Phase;
  durationMs: number;
  cachedResponseKey: string;
  label: string;
}

const DEMO_SEQUENCE: DemoCase[] = [
  { phase: "case1_mimic", durationMs: 15000, cachedResponseKey: "CASE_1_MIMIC", label: "9yo girl - viral syndrome" },
  { phase: "case2_rory_ed", durationMs: 25000, cachedResponseKey: "CASE_2_RORY_ED", label: "12yo - Rory 2012 in ED" },
  { phase: "case3_rory_school", durationMs: 20000, cachedResponseKey: "CASE_3_RORY_SCHOOL", label: "12yo - Rory 2012 school nurse" },
];

interface Props {
  onCaseChange: (cachedResponseKey: string) => void;
}

export default function DemoRunner({ onCaseChange }: Props) {
  const [phase, setPhase] = useState<Phase>("splash");
  const [caseIndex, setCaseIndex] = useState(-1);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "r") {
        e.preventDefault();
        setPhase("splash");
        setCaseIndex(-1);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    if (phase === "splash" || phase === "close") return;
    const current = DEMO_SEQUENCE[caseIndex];
    if (!current) return;
    onCaseChange(current.cachedResponseKey);
    const timer = setTimeout(() => {
      if (caseIndex + 1 < DEMO_SEQUENCE.length) {
        setCaseIndex(caseIndex + 1);
        setPhase(DEMO_SEQUENCE[caseIndex + 1].phase);
      } else {
        setPhase("close");
      }
    }, current.durationMs);
    return () => clearTimeout(timer);
  }, [phase, caseIndex, onCaseChange]);

  if (phase === "splash") {
    return (
      <RorySplash
        onComplete={() => {
          setCaseIndex(0);
          setPhase(DEMO_SEQUENCE[0].phase);
        }}
      />
    );
  }

  if (phase === "close") {
    return <ForRoryClose />;
  }

  return null;
}
