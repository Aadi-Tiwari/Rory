# Retrospective evaluation status

The incident-sepsis evaluation tooling is implemented and tested. No real-patient evaluation under this incident-sepsis protocol or relevant external validation has been completed. Rory remains not clinically validated.

A subsequent search found a usable open pediatric admission cohort. The separate [public admission benchmark](../public-triage-2026-10-20/results.md) tests the frozen checkpoint with missing narrative and numeric capillary refill. It does not resolve this protocol's sepsis outcome, input, or clinical-review requirements. The verification entries below describe the earlier tooling run.

## What is available

- A provisional pediatric ED incident-sepsis study specification, with clinical review and the reference standard explicitly pending.
- A normalized cohort schema requiring source and availability timestamps, linked patient IDs, outcome onset, follow-up, and documented data provenance.
- An offline scorer using the existing checkpoint, frozen tokenizer assets, source hashes, package versions, and deployed score thresholds.
- Aggregate discrimination, error rates, uncertainty, age and site summaries, and paired recorded-screen comparisons.
- A dataset review with primary-source links and exact access and modality limitations.

The study concerns an exploratory association between an existing urgency score and subsequent sepsis. It does not establish a calibrated sepsis probability or the safety of HOME / ED / 911 recommendations.

## Verification

| Check | Result and evidence |
| --- | --- |
| Focused tests | PASS. `python -m pytest tests/test_retrospective.py -q` returned `45 passed, 1 warning in 13.00s`. The warning concerns an existing `_jac_finder` pytest plugin. |
| Existing-data audit | PASS. `python -m backend_a.validation.retrospective audit --output reports/retrospective-evaluation-2026-10-20/existing-data-audit.json` completed. [Audit output](existing-data-audit.json). |
| Frozen offline inference | PASS. The final checkpoint smoke run produced finite, normalized outputs for the synthetic inputs, verified assets before and after scoring, and recorded the manifest and checkpoint hashes. [Execution output](inference-smoke-final.json). |
| Template rejection | PASS. The final command rejected the example cohort before inference and did not create a performance report. This is also recorded in the final smoke output. |
| Artifact checks | PASS. JSON examples parse; the edited protocol and local links were checked; `git diff --check` returned success. |
| Incident-sepsis patient performance | UNVERIFIED. No suitable permitted cohort with the required input and outcome provenance was acquired. A separate public admission benchmark is linked above. |
| Temporal or external transfer | UNVERIFIED. No independent eligible cohort was evaluated. |
| Sepsis calibration | NOT ESTIMATED. The deployed urgency score is not a sepsis probability. |
| Clinical protocol approval | PENDING. The research question and horizon are provisional; an approved reference standard and precision requirements are still needed. |

The earlier freeze is stored locally at `validation_private/provisional-freeze.final.json`. It records clinical review as pending and predates the public-benchmark source changes, so it is historical evidence rather than a current executable manifest. The local private directory is ignored by Git. Create a new freeze before any future incident-sepsis run.

## Review findings addressed

A separate static review identified high-severity gaps in binding consumed files to their hashes and hashing the exact bytes parsed. The corrected manifest keeps hashes under the consumed paths, checks required asset coverage and snapshot membership, and hashes parsed JSON bytes directly. Regression tests cover changed checkpoints, added tokenizer files, and a symlink retargeted to another already hashed file.

The review also identified misleading degenerate bootstrap intervals. The report now withholds zero-width intervals and intervals with too few valid resamples. Tests exercise both withheld and nondegenerate intervals.

An additional cohort review found that requiring full-window follow-up after a known positive event could exclude severe cases. Positives now require follow-up through onset; negatives require the complete window. The regression test retains an established event when observation ends before the window closes.

## Material findings and remaining work

The existing generator includes later reassessment details in the initial complaint text. At the original audit, the evaluator used argmax while deployment applied urgency-score thresholds. GitHub's later research workflow corrected that mismatch through a shared decision policy; the integrated validation runners now use that policy too. Neither issue was concealed by relabeling synthetic data as clinical evidence. This integration does not change the model weights, generator, or service behavior.

The inspected dataset releases have missing modalities, missing outcome timing, restricted access, or a different clinical setting. A clinical research partner must supply or authorize a suitable export and approve the outcome reference standard. See the [dataset review](../../research_notes/retrospective-evaluation-2026-10-20/dataset-fit.md), [study specification](../../docs/retrospective-study.md), and [execution guide](../../docs/retrospective-evaluation.md).

No commits, pushes, deployments, agreement submissions, or external communications were made.
