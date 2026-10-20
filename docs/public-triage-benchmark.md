# Public admission benchmark

This is a separate exploratory study of the existing checkpoint with missing inputs. It does not change the provisional incident-sepsis protocol or claim clinical approval.

## Fixed analysis

Use the original `PaediatricTriage_DATA.csv` in Figshare version 1, released under CC BY 4.0. The published study concerns children attending Mbagathi Hospital in Nairobi. Its primary outcome is clinician-decided hospital admission for at least 24 hours. Some emergency measurements followed the start of treatment. This benchmark therefore measures association at the study assessment, not performance before treatment or early sepsis detection. [Dataset](https://doi.org/10.6084/m9.figshare.9104918.v1), [study](https://doi.org/10.12688/wellcomeopenres.15387.3)

The inspected file has SHA256 `36acddd0c4358affd4adc1170f46c10a43d4bd00704a46d4bca5e7dabb3f3e5c`. The runner rejects other bytes.

Apply these rules before calculating scores:

1. Remove exact repeated CSV rows, retaining the first occurrence. Released identifiers are absent, so further patient linkage is unverified.
2. Require `admitted` to be `0` or `1`, interpreted as no or yes. The author analysis maps admission to a binary label, but a dictionary specific to this numeric release was not found.
3. Calculate months as `12*age_years + age_mths + age_days/30`. Treat blank components as zero only when some age information is present. Retain ages from 2 through 60 months inclusive. This follows the component semantics in the [author's analysis](https://github.com/pmwaniki/ppg-analysis/blob/8679a3a31d023f5e22b7d7c23404fa0bd222d474/EDA/descriptives.py), which uses a differently labeled export of the same cohort.
4. Require at least one observed numeric model vital. Map pulse rate to beats/min, respiratory rate to breaths/min, oxygen saturation to percent, and Celsius temperature to Fahrenheit using `C*9/5 + 32`. Preserve missing values.
5. Set numeric capillary refill to missing. The released categories are not seconds and their full coding was not verified. Give the text encoder an empty string for every participant. Do not reconstruct complaints from symptoms, diagnoses, outcomes, or generated prose.

The model, normalization buffers, source, tokenizer, environment, both declared development JSON files, and analysis specification are frozen before inference. There is no fitting or recalibration on this cohort. All eligible rows are evaluation data; a train/test split would serve no purpose without fitting. Full training history and patient independence cannot be independently established from the released files.

Use the shared service policy in `backend_a/decision_policy.py`: `(0.5*p_ED + p_911)/sum(probabilities)`, with the existing thresholds `0.35` and `0.70`. The original run used the older float32 weighted sum. During integration with GitHub's existing service changes, the evaluator was aligned with the normalized policy and its source was added to the freeze. Report that compatibility rerun separately from the original frozen results. No thresholds or model parameters are fitted. Report admission discrimination, sensitivity, specificity, missed admissions, false alarms against admission, predictive values, and alert rates. These labels describe agreement with admission, not appropriate treatment or referral.

Report Wilson 95% intervals for rates and participant-row percentile bootstrap intervals for AUROC and average precision, with 2,000 resamples and seed 42. Retain the existing suppression of single-class and degenerate discrimination intervals. The intervals are conditional on independent participant rows; unidentified repeat patients could make them too narrow.

At threshold `0.70`, also report age groups `[2,12)`, `[12,24)`, and `[24,60]`, and strata by the released `data_resuscitation` codes. Do not interpret those codes as pre-treatment or post-treatment without a dictionary. Report missingness overall, by age, by raw resuscitation code, and by admission. These exploratory strata do not establish fairness.

There is no verified recorded screening result in the inspected release. Do not construct a clinical baseline from unverified category codes, or compare this test directly with the source model's development performance. No sepsis calibration, disposition-safety assessment, or independent-hospital replication can be calculated from this release.

## Reproduction

Keep the CSV, freeze, and participant predictions in the ignored `validation_private` directory. The repository contains aggregate reports only. Download the original file from the dataset record, preserving its filename and bytes. A copy is already present locally at `validation_private/public-cohorts/figshare-9104918-PaediatricTriage_DATA.csv`.

```powershell
python -m backend_a.validation.public_triage freeze `
  --snapshot "C:\Users\tiwar\.cache\huggingface\hub\models--emilyalsentzer--Bio_ClinicalBERT\snapshots\d5892b39a4adaed74b92212a44081509db72f87b" `
  --source validation_private/public-cohorts/figshare-9104918-PaediatricTriage_DATA.csv `
  --output validation_private/public-triage-freeze.integration.json

python -m backend_a.validation.public_triage run `
  --manifest validation_private/public-triage-freeze.integration.json `
  --source validation_private/public-cohorts/figshare-9104918-PaediatricTriage_DATA.csv `
  --predictions validation_private/public-triage-predictions.integration.json `
  --output reports/public-triage-2026-10-20/metrics.integration.json
```

Outputs refuse overwriting. Repeated runs need new output names. The local model snapshot must contain the original tokenizer and base-model files. All inference is offline.

The source dataset and study are by Mawji and colleagues. This benchmark adapts their released data using the transformations listed above; it does not imply their endorsement of Rory. Preserve the dataset citation and [CC BY 4.0 attribution](https://creativecommons.org/licenses/by/4.0/) when sharing results.
