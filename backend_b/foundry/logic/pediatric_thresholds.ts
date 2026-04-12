// RORY v2 Backend B - AIP Logic function
// pediatric_vital_thresholds_for_age: returns age-adjusted PALS vital ranges
// Called by ontology_writer when composing TriageDecision.reasoning

import { Function } from "@foundry/functions-api";

export interface VitalRanges {
  hr_range: [number, number];
  rr_range: [number, number];
  temp_range: [number, number];
  source_citation: string;
}

@Function()
export function pediatric_vital_thresholds_for_age(age_months: number): VitalRanges {
  // PALS 2020 reference ranges by age band
  if (age_months < 12) {
    return {
      hr_range: [100, 160],
      rr_range: [30, 60],
      temp_range: [97.0, 100.4],
      source_citation: "PALS 2020 §3.1 Infant Vital Signs",
    };
  } else if (age_months < 36) {
    return {
      hr_range: [90, 150],
      rr_range: [24, 40],
      temp_range: [97.0, 100.4],
      source_citation: "PALS 2020 §3.2 Toddler Vital Signs",
    };
  } else if (age_months < 72) {
    return {
      hr_range: [80, 140],
      rr_range: [22, 34],
      temp_range: [97.0, 100.4],
      source_citation: "PALS 2020 §3.3 Preschool Vital Signs",
    };
  } else if (age_months < 144) {
    return {
      hr_range: [70, 120],
      rr_range: [18, 30],
      temp_range: [97.0, 100.4],
      source_citation: "PALS 2020 §3.4 School-age Vital Signs",
    };
  } else {
    return {
      hr_range: [60, 100],
      rr_range: [12, 20],
      temp_range: [97.0, 100.4],
      source_citation: "PALS 2020 §3.5 Adolescent Vital Signs",
    };
  }
}
