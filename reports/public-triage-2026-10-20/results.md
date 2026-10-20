# Public pediatric admission benchmark

Rory performed poorly in this missing-input admission test. The result does not establish sepsis accuracy, clinical validation, or safe disposition recommendations.

The frozen checkpoint was evaluated on 1,116 eligible participant records from the open Nairobi pediatric triage release, including 139 coded admissions. The source outcome is clinician-decided admission for at least 24 hours. Narrative text and numeric capillary refill were unavailable: every complaint input was empty and capillary refill remained missing. Some measurements followed emergency treatment. [Source dataset](https://doi.org/10.6084/m9.figshare.9104918.v1), [source study](https://doi.org/10.12688/wellcomeopenres.15387.3)

## Measured results

Admission AUROC was **0.588** (95% bootstrap interval **0.536 to 0.640**). Average precision was 0.163; the admission fraction was 12.5%. These are admission-association measures under missing inputs, not sepsis probabilities.

| Existing urgency threshold | Admissions above threshold | Missed admissions | Nonadmitted alerts | Sensitivity, 95% CI | Specificity, 95% CI |
| --- | --- | --- | --- | --- | --- |
| 0.35 | 2/139 | 137 | 6 | 1.4% (0.4% to 5.1%) | 99.4% (98.7% to 99.7%) |
| 0.70 | 0/139 | 139 | 6 | 0.0% (0.0% to 2.7%) | 99.4% (98.7% to 99.7%) |

An admission below threshold is counted as a missed admission for this analysis. An alert in a nonadmitted child does not prove that referral would have been unnecessary. Neither threshold was chosen or changed using these outcomes.

| Age in months | Records | Admissions | Admission AUROC, 95% CI |
| --- | --- | --- | --- |
| [2,12) | 404 | 71 | 0.497 (0.421 to 0.572) |
| [12,24) | 346 | 41 | 0.552 (0.445 to 0.651) |
| [24,60] | 366 | 27 | 0.674 (0.550 to 0.794) |

These descriptive strata do not establish fairness or age-specific safety. The full report also includes raw treatment-timing-code strata, missingness, predictive values, alert rates, average-precision intervals, and score quantiles.

## Cohort and interpretation

The file contains 1,135 rows. The fixed selection excluded 14 with missing or unknown admission, 4 outside the specified age range, and 1 exact duplicate. These counts differ from the published analysis; this study reports the released file rather than forcing agreement.

- Binary admission coding is interpreted as 0 = no and 1 = yes. Author analysis supports the direction, but no dictionary specific to this numeric release was retrieved.
- Participant IDs are absent. Removing an exact duplicate does not prove all remaining rows are independent; the bootstrap and rate intervals assume independence.
- The absent text and numeric capillary refill change the intended input setting. The result cannot be used as an estimate of the complete text-and-vitals model.
- Treatment may precede measurements. The data do not establish information availability at initial triage.
- The outcome is admission, not sepsis. There is no sepsis calibration result, complete screening comparator, or independent-hospital replication.
- The existing training artifacts are synthetic or illustrative. The run used no fitting, recalibration, threshold selection, or generated patient narratives.

## Reproducibility and checks

The original frozen run completed at `2026-10-20T18:23:32.277052+00:00`. The checkpoint SHA256 is `825409ee00fde7193a3e35aca0bd9d89c0f7c73d606c30294490f29876e86e2c`; the original manifest SHA256 is `64c06ad59139fefe0759d15c671ec5eba9b0d1e7e6a3fc29676f0aa55837def2`. The source and model assets were verified before and after inference. Participant predictions stay in the ignored local directory.

`python -m pytest tests/test_retrospective.py tests/test_public_triage.py -q` completed with `60 passed, 1 warning in 7.38s`. The warning is from the existing `_jac_finder` pytest plugin. The final run reproduced every first-run probability exactly after an output-path collision guard was added. Confusion counts and AUROC were independently recomputed from the saved predictions, and subgroup totals were checked.

The separate code review raised an output-path collision case, now rejected before inputs are read. Its concern that a single-class subgroup would abort the report was refuted by execution: undefined statistics return null while counts and estimable rates remain available.

[Aggregate metrics](metrics.json), [verification record](verification.json), [fixed protocol and commands](../../docs/public-triage-benchmark.md), [dataset-access review](../../research_notes/patient-evaluation-access-2026-10-20/open-cohorts.md).

## Integration rerun

GitHub's existing service uses a normalized weighted score. Both evaluators now call that shared policy, and the freeze includes its source. The original float32 weighted sum can differ at an exact decision boundary. Regression checks cover those boundaries; neither thresholds nor model parameters were fitted.

A separate freeze at `2026-10-20T18:38:58.722615+00:00` preceded the integration rerun, which completed at `2026-10-20T18:40:52.302219+00:00`. Its manifest SHA256 is `758acbdbee18b95b1f6f5b3a7ddfca96f329f5761d422719a1f502ed54551174`. Every participant's raw model probabilities matched the original run exactly. Both threshold confusion matrices, AUROC, average precision, their intervals, and the age and raw resuscitation-code summaries remained unchanged. The original report and provenance are retained alongside the [integration metrics](metrics.integration.json).

The combined suite completed with `104 passed, 1 warning in 10.91s` using `.\validation_private\test-env\Scripts\python.exe -m pytest -q tests backend_a/tests`. An isolated environment supplied Starlette 0.37.2 for the installed FastAPI 0.111.0; the laptop's global Starlette 1.3.1 is incompatible and was left unchanged. Post-run checks verified the frozen assets and file hashes, independently recomputed service-policy metrics, and checked subgroup totals. See the [integration verification record](integration-verification.json).

## Remaining clinical work

An appropriate sepsis-labeled cohort, a clinically reviewed outcome and index definition, and an independent evaluation cohort are still needed. Fitting a sepsis probability model would require separate development data before untouched evaluation. The [unsent collaboration request](../../docs/clinical-collaboration-draft.md) identifies an official research contact and the decisions needed from a clinical collaborator. No contact, agreement, or approval has been submitted or obtained.

Rory remains not clinically validated.
