# Running the retrospective evaluation

Run commands from the repository root. The scorer uses the existing local checkpoint and tokenizer, stays offline, and runs on CPU. It does not retrain the model or call the application server.

The current study is provisional. No suitable real-patient cohort has been acquired or evaluated. The example specification leaves clinical review pending, and the example cohort is explicitly a template. Neither can produce a patient-performance result.

## Audit the existing data

```powershell
python -m backend_a.validation.retrospective audit --output validation_private/existing-data-audit.json
```

This reports counts, patient-ID and exact-text overlap, reassessment-text indicators, missing index timestamps, and checkpoint identity. It does not score clinical performance. The checked-in audit under `reports/retrospective-evaluation-2026-10-20/` records the files inspected during this work.

## Prepare the study and export

Start from [the study specification](retrospective-study.md) and the two schema examples:

- [Study configuration](retrospective-study.example.json).
- [Cohort export](retrospective-cohort.example.json).

Resolve the clinical outcome definition, adjudication procedure, cohort sampling, and permitted data use before changing the pending status. A status field is a declaration, not evidence of institutional approval. Maintain the actual governance and extraction records separately.

Keep authorized exports, manifests, and any patient-level artifacts under `validation_private/`, which is ignored by Git. The program writes aggregate reports only. Patient identifiers must be pseudonymous, consistently linked across all sites and development files, and unique within the evaluation. It rejects repeat patients, so the upstream extraction must select the earliest eligible encounter before examining outcomes.

Every vital is either `null` or an object with `value`, `observed_at`, and `available_at`. The complaint has those timestamps plus `origin: "recorded_at_care"`. Timestamp checks cannot detect a later fact copied into a falsely dated note; inspect source provenance. Use Fahrenheit for temperature. Preserve conversion records outside the model inputs. Never substitute normal values for missing vitals or generate missing text.

For a positive outcome, supply an onset within the future window. Negative outcomes require complete follow-up. The program rejects known or unknown prevalent sepsis, incomplete ascertainment, and timezone-free timestamps.

A baseline, when available, uses this structure:

```json
{
  "name": "Exact screen name from the frozen study",
  "value": 1,
  "observed_at": "2026-01-01T09:00:00Z",
  "available_at": "2026-01-01T09:01:00Z"
}
```

Use `null` when no eligible baseline was recorded. The report compares methods on the same patients with a recorded baseline and identifies the coverage. This is descriptive comparison, not a superiority test.

## Freeze before evaluating

The snapshot must be a complete local Bio_ClinicalBERT directory compatible with the checkpoint, including `config.json`, `vocab.txt`, and model weights. Use a resolved cached snapshot directory rather than a moving model name.

```powershell
python -m backend_a.validation.retrospective freeze --spec validation_private/study.json --snapshot C:/path/to/local/snapshot --output validation_private/frozen-study.json
```

The manifest hashes model and evaluation source, weights, tokenizer/base-model assets, normalization metadata, and declared development files. It records Python and package versions and the existing decision thresholds. The study specification is embedded; the final report records the manifest and cohort hashes. Freeze before accessing evaluation outcomes and preserve the dated manifest independently. A hash detects changes against a retained manifest; it does not prove when a file was created or prevent someone replacing the manifest.

The development files are JSON arrays containing `patient_id` for every patient used in training, tuning, recalibration, or threshold selection. Declare all such files. A matching ID check cannot detect undeclared development data or incompatible identifier namespaces.

Use `cohort_role: "exploratory"` for the first real-data study of this synthetic-trained model. A genuine external comparison requires known development sites. A temporal comparison requires known development sites, a development cutoff, and preserved cross-patient calendar time. Patient-specific shifted dates do not satisfy that requirement.

## Score an approved cohort

```powershell
python -m backend_a.validation.retrospective run --manifest validation_private/frozen-study.json --cohort validation_private/cohort.json --output validation_private/report.json
```

The command verifies assets before and after inference, rejects invalid records rather than silently dropping them, and refuses to overwrite an existing output. Correct any extraction errors through a documented revision, not outcome-guided filtering. Maintain an upstream exclusion ledger because this command receives the already selected cohort.

The report contains confusion counts, denominators, Wilson intervals for binary rates, AUROC and average precision with patient bootstrap intervals, age and site strata, aggregate missingness, and a paired baseline summary where available. Single-class strata have undefined discrimination metrics. Bootstrap counts identify draws omitted because they contain only one outcome class. Intervals are suppressed if fewer than 1000 valid draws remain; this computational minimum does not establish an adequate clinical sample size. Degenerate intervals are also withheld: perfect separation in an observed sample does not establish certainty. Sparse intervals are descriptive and can be unstable.

The primary alarm uses the deployed urgency score at `0.70`. The report also counts the deployed HOME / ED / 911 recommendations using the `0.35` and `0.70` thresholds, without claiming these dispositions are clinically correct. It does not report sepsis calibration or Brier score: this model's score is not a sepsis probability.

This evaluates the frozen model score only. It does not evaluate drift detection, explanations, outlier handling, the UI, actual referrals, or patient outcomes under deployment. Passing the import checks does not establish clinical validation.

## Verify the tooling

```powershell
python -m pytest tests/test_retrospective.py -q
```

The tests use fabricated records and analytical examples. They cover leakage rejection, patient overlap, outcome windows, missingness, cohort separation, uncertainty, paired baseline coverage, shared service-policy thresholds, frozen-file changes, and overwrite protection. These are software tests, not patient evidence.
