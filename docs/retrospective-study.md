# Retrospective study specification

Status: provisional research protocol. No real-patient evaluation has been completed under this protocol. The outcome reference standard and clinical review remain unresolved, so the protocol is not ready for a real-data run.

## Question and limits

Among children at an initial emergency department assessment, does the frozen Rory score distinguish patients who develop incident sepsis during the following 24 hours?

This is an exploratory test of an existing ordinal triage score against a new outcome. It does not establish that the score is a sepsis probability, that HOME / ED / 911 decisions are appropriate, or that using Rory improves care. It does not evaluate school-nurse use or the first 90 seconds of an encounter.

Evaluation should reflect the intended population, setting, predictor availability, and outcome timing. An independent dataset alone does not establish relevant transfer. [External-validation methods](https://www.bmj.com/content/384/bmj-2023-074820)

## Cohort and index

The provisional population is children with `0 <= age_months < 216` presenting to an emergency department. Include consecutive eligible encounters from sites and date ranges fixed before outcome analysis. Upstream extraction must select one earliest eligible encounter per linked patient before examining outcomes. The harness rejects repeated patient IDs but does not verify cross-site linkage or earliest-encounter selection.

The index is the recorded completion time of the initial ED nursing assessment. It must be defined independently of later events and model scores. An encounter without a reliable index timestamp is ineligible. Include only information observed and available by that index.

Exclude sepsis already present at or before index, unresolved outcomes, and inadequate temporal provenance. Keep an upstream exclusion ledger and compare eligible and excluded patients. The harness rejects an invalid cohort wholesale; it does not select patients or generate that ledger. Do not balance outcome classes or select easy controls.

## Reference outcome

The endpoint is first sepsis onset strictly after index and no later than 24 hours after index. The harness fixes this horizon and the `pediatric_ed` setting. Positive records need an onset timestamp and follow-up through that event. Negative records need complete ascertainment through the entire window. Discharge, transfer, loss to follow-up, or death before completion does not automatically establish a negative outcome. A known positive event remains eligible when observation ends after onset but before the window closes.

A pediatric clinical collaborator must approve an operational reference standard, onset ascertainment, competing-event handling, and an adjudication process before real evaluation. Adjudicators must not see Rory scores. The specification must identify the diagnostic criteria, source fields, label provenance, and approach to disagreement. These are unresolved dependencies, not labels to infer from a diagnosis-code dictionary.

Do not translate discharge diagnoses into HOME / ED / 911 labels. A retrospective diagnosis without onset timing can support a separately specified association study, but cannot satisfy this incident-sepsis endpoint.

## Predictor extraction

Use the original initial-assessment complaint and the latest eligible observation for each model vital: heart rate, respiratory rate, temperature in Fahrenheit, oxygen saturation in percent, and capillary refill in seconds. Retain original units and conversion provenance.

Every observation and complaint needs both an observation time and an availability time. Both must be at or before index. A retrospectively entered or amended note is unavailable at index even if its text describes earlier events. Do not use discharge summaries, future diagnoses, follow-up vitals, or later treatment decisions as predictors.

Keep missing vitals missing and use the checkpoint's imputation and normalization. The harness requires an initial complaint and at least one observed vital, and reports missingness per feature overall. Missingness by age, site, and outcome remains an upstream study-reporting requirement. Never generate replacement notes, substitute normal values, or recompute normalization from evaluation data.

## Frozen model and decision policy

The model produces probabilities for synthetic HOME / ED / 911 training classes. Its deployed score is:

```text
score = (0.5*p_ED + p_911) / sum(probabilities)
HOME: score < 0.35
ED:   0.35 <= score < 0.70
911:  score >= 0.70
```

The scorer uses `backend_a/decision_policy.py`, the same policy as the service, including normalization of the model probabilities. The implemented binary alarm is `score >= 0.70`. The report counts all three recommendation classes using both thresholds, but does not calculate secondary binary metrics at `0.35`. Do not adjust thresholds using evaluation outcomes.

The freeze manifest embeds the specification and hashes model/evaluation source, checkpoint, normalization metadata, local tokenizer/base-model snapshot, and declared development files. It records Python and package versions. The scorer checks these before and after inference, preserves evaluation mode and normalization buffers, and records cohort and manifest hashes. Independently retain the dated manifest and extraction records; hashes do not prove provenance or prevent manifest replacement.

No fitting, recalibration, or threshold tuning belongs in this evaluation. Any such change creates a new model and requires a separate development cohort and untouched evaluation cohort.

## Analysis and comparison

The report includes patient/event counts, confusion counts, sensitivity, specificity, positive and negative predictive values, missed-case rate, false-positive rate, false-discovery rate, and alert rate at `0.70`. Rates include denominators and 95% Wilson score intervals without multiplicity adjustment. Undefined quantities remain undefined. Participant flow and score-distribution reporting still require additional study work.

AUROC and average precision use 95% patient percentile bootstrap intervals, seed `42`, and `2000` resamples by default. One row per patient makes each sampled row a patient. Reports identify requested and valid draws; single-class draws are omitted. Intervals with fewer than `1000` valid draws or zero width are suppressed. This does not establish adequate clinical precision. Single-class cohorts have undefined discrimination. Metrics are also reported by site and fixed age bins `[0,12)`, `[12,60)`, `[60,144)`, `[144,216)` months. Small strata cannot establish fairness or acceptable performance. Precision requirements remain unresolved.

The baseline is the institution's existing screen, recorded and available at index. The report describes both methods on the same patients and reports baseline coverage; it performs no superiority or paired-difference inference. An absent screen is unavailable. Do not reconstruct it from later information or substitute an unrelated adult score.

A false-positive sepsis alarm is not necessarily an unnecessary referral: Rory's training also assigns high urgency to other conditions. Likewise, a negative sepsis outcome cannot prove that a HOME recommendation was safe.

Do not calculate sepsis calibration, sepsis Brier score, or probability-based decision curves from the ordinal score. The API's `confidence` value is also not an uncertainty estimate or calibrated correctness probability.

## Temporal and external evaluation

The harness rejects IDs found in declared development files. Temporal mode requires a later index at a declared development site and preserved calendar-time metadata. External mode rejects declared development sites. These checks depend on complete declarations and consistent identifiers; they cannot discover undeclared development patients or verify calendar-time preservation.

Report each cohort separately. Compare case mix, referral patterns, age, event prevalence, missingness, and measurement practice before pooling. An ICU convenience cohort cannot establish performance for initial ED assessment. If adaptation uses external outcomes, those patients become development data and cannot remain the final external test.

TRIPOD+AI guides transparent reporting of prediction-model studies, including evaluation and subgroup reporting. It is a reporting guideline, not a certificate of study quality or clinical validation. [TRIPOD+AI](https://www.bmj.com/content/385/bmj-2023-078378)

## Findings from the original checkout

The audit below predates integration with the newer GitHub research workflow. That workflow corrected the argmax mismatch through a shared service policy and pinned the tokenizer/construction revision. The underlying synthetic-data limitations remain.

| Finding | Evidence |
|---|---|
| Training targets are assigned from diagnoses; sepsis and appendicitis both map to `911`. | `backend_a/models/train.py:62` and `:100` |
| Existing evaluation uses argmax, while deployment uses score thresholds. | `backend_a/models/evaluate.py:155`; `backend_a/inference/predict.py:57` and `:66` |
| Synthetic initial complaints contain future, label-dependent reassessment information. | `backend_a/data/generate_cohort.py:688`, `:712`, and `:729` |
| Structured age, sex, and weight do not enter the model forward call. Age can appear in complaint text and is used by reasoning. | `backend_a/inference/predict.py:97`; `backend_a/models/vitals_mlp.py:20` |
| Tokenizer and base-model loading do not pin a revision. | `backend_a/models/text_encoder.py:81` |
| API confidence multiplies risk by completeness and an outlier penalty. | `backend_a/inference/predict.py:112` |

A metadata-only audit of the current JSON files found 974 development records and 51 held-out records, no overlapping patient IDs, and 3 overlapping exact complaint texts. These are synthetic or illustrative records with shared generation methods. They can test software plumbing, not clinical performance.

## Execution and outstanding dependencies

See [execution instructions](retrospective-evaluation.md) for `audit`, `freeze`, and `run`. The standalone harness loads the existing model without changing the model or generator. It evaluates only the single-index score and thresholds, not drift, DBSCAN, reasoning, UI behavior, or disposition safety.

The code checks supplied timestamps, units, outcome windows, and review/provenance fields. It cannot independently verify the underlying records, index meaning, sampling, permissions, linkage, clinical approval, or adjudication. Changing a status field is not approval. Resolve these through source audit and clinical review before real evaluation, together with cohort dates and precision requirements. Keep patient records out of published reports.

Until those dependencies are resolved and a suitable cohort has been evaluated, Rory remains not clinically validated.
