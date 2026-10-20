# Research validation workflow

Rory is a pediatric research prototype. This workflow prepares an evaluation; it does not establish clinical validity, authorize patient use, or provide a medical-device clearance. There is currently no clinical partner, approved pediatric study dataset, or prospective study for this repository.

A separate [public admission benchmark](../reports/public-triage-2026-10-20/results.md) now records an exploratory test with missing narrative text and numeric capillary refill. It uses an openly licensed cohort and an admission endpoint, so it does not resolve the intended clinical study's data or outcome requirements. Its [protocol](public-triage-benchmark.md) and the [incident-sepsis protocol](retrospective-study.md) specify these distinct analyses.

## What has to be established

The first proposed research question is whether information available at initial pediatric assessment can identify children who need urgent clinical review. A pediatric clinician must define the setting, eligible ages, prediction time, reference outcome, outcome window, exclusions, and intended user before a real-data experiment is frozen.

The current HOME/ED/911 labels were assigned from synthetic diagnoses. They are engineering labels, not adjudicated dispositions. In particular, a child already in an emergency department does not have the same decision context as a family deciding where to seek care. Do not map a hospital urgency field to these labels simply to make a dataset fit. A clinician-approved endpoint may require a separately versioned model and output contract.

For the proposed arrival-time study, inputs must be timestamped before or at the index assessment. Later reassessment, treatment, discharge information, diagnosis text, and outcome descriptions cannot enter the predictor. Keep later measurements for a separately defined longitudinal question. A text regex can flag obvious leakage but cannot establish feature availability.

## Existing evidence and its limits

The cohort audit found no shared patient IDs, but found repeated complaint templates and complaints containing later reassessment information. See [the generated audit](research-audit.json). Source strings inside these files are unverified labels, not proof of licensed real patient records or verified publications. The cohort remains synthetic/illustrative research material.

A trained checkpoint was recovered from an older local checkout. Its SHA-256 is `825409ee00fde7193a3e35aca0bd9d89c0f7c73d606c30294490f29876e86e2c`. The file is not distributed in Git. Its training environment, exact split membership, and original encoder/tokenizer provenance were not recorded. A matching hash identifies the recovered file but does not repair those gaps or establish redistribution rights.

Use this checkpoint only to investigate the existing pipeline. Do not present its evaluation as independent clinical evidence. The current evaluator uses the service's weighted-risk policy and includes every row, including the hand-authored Rory case. It is not an exact reproduction of the former argmax evaluator, which separated that case. Do not tune thresholds or training examples to make a spotlight case pass.

The model takes vital signs and complaint text. Age is not currently a separate structured model feature. The API's `confidence` is a heuristic involving weighted risk, input completeness, and an outlier penalty; it is not a calibrated probability of correctness or sepsis. Drift is based on request ordering, not a verified clinical timeline. The frozen-model workflow below does not validate those auxiliary components or the generated reasoning.

[Technical verification evidence](research-verification.json) records the exercised cases, repeatability check, test counts, actual runtime versions, and unexercised work. The existing local ML environment differs from the older requirements file. These runs verify that recorded environment; a clean install from the requirements file was not exercised in this pass.

## Run the workflow locally

Run commands from `backend_a/`. Keep inputs and outputs with any patient-level content in approved private storage. `.research/` is ignored by Git at every level. A report can contain small subgroup counts even when raw records are omitted; review it before sharing.

The audit and metrics commands use Python's standard library. Inference additionally uses the repository's model dependencies and a trusted checkpoint. Record the environment used for each run. The inference output records Python, package versions, CPU execution, seed, thread count, dataset and checkpoint hashes, and the exact tokenizer/construction revision. Loading a checkpoint replaces the encoder weights, so that revision does not establish their original training provenance.

```sh
python -m research.audit --train data/hero_cohort.json --test data/held_out.json --output ../.research/cohort-audit.json
python -m research.infer --dataset data/held_out.json --checkpoint /private/path/best_model.pt --data-kind synthetic --allow-legacy-synthetic --output ../.research/predictions.json
python -m research.evaluate --predictions ../.research/predictions.json --dataset data/held_out.json --output ../.research/evaluation.json
```

`--allow-legacy-synthetic` permits a clearly labeled investigation of the contaminated historical inputs. Without it, detected later information blocks inference. This override never permits real-data temporal leakage. Do not strip text and call the old model validated; any corrected training and evaluation design needs new frozen artifacts and an untouched evaluation set.

The evaluator checks the dataset hash, case coverage, reference labels, and subgroup values against the input dataset. It rejects malformed probabilities, unknown labels, duplicate IDs, and empty data. It reports the confusion matrix, class support, missed cases, false alarms, sensitivity, specificity, precision, undertriage, overtriage, multiclass Brier score, class-specific reliability bins, and exploratory age, sex, and missingness groups. Undefined denominators remain null. Constant-label accuracy baselines are included.

Wilson intervals apply to unweighted independent cases. They are not suitable for clustered repeated visits or a complex survey without a design-aware analysis. The small exploratory groups and calibration bins are not evidence of subgroup safety. The model's weighted risk is an ordinal score, not a sepsis probability.

For a future approved dataset, each JSON row needs a pseudonymous `patient_id`, integer `age_months` below 216, `sex` if available, `complaint_text`, and a `vitals` object. Vital units are beats/min, breaths/min, Fahrenheit, percent SpO2, and seconds of capillary refill. Missing vitals are JSON null. Real research rows need an independently adjudicated `label` only after the endpoint and its mapping to the output contract have been approved. Do not put direct identifiers into these files. The current interface supports one row per patient; repeated visits require patient-grouped splitting and a revised clustered analysis.

The runner does not create a reference standard, verify licensing, establish deidentification, or make a dataset independent of training. Maintain those records separately in the study's approved storage.

## Freeze a defensible experiment

1. Write and review the protocol with a pediatric clinician and a research mentor. Specify intended setting and user, index time, inclusion/exclusion criteria, outcome and horizon, reference adjudication, missing-data policy, and how harms from missed cases and false alarms will be assessed. Agree on acceptance criteria and a sample-size calculation before viewing test outcomes.
2. Obtain the dataset's permission and an institutional determination about ethics review, privacy, and consent. Record versions, permitted purposes, access conditions, retention, and redistribution restrictions. Do not upload patient records to this repository or a hosted model.
3. Split by patient before fitting anything. Prefer later-time and separate-site evaluation when available. Keep training, model-selection validation, and final evaluation distinct. Fit normalization, imputation, calibration, thresholds, clustering, and feature selection on their designated development partitions only. Keep the final evaluation sealed until the analysis is fixed.
4. Freeze the source revision, dependency environment, tokenizer revision, feature/unit schema, preprocessing statistics, model checkpoint, thresholds, and split manifest. Hash the files. Record exclusions and failures without silently dropping difficult cases. The updated trainer records its synthetic split and artifact identities; that alone does not make its random split clinically appropriate.
5. Evaluate the frozen system against the agreed reference standard. Report denominators and uncertainty with missed cases and false alarms, calibration, data coverage, failure rates, prespecified subgroups, and clinically relevant baselines. Include site/time effects and clustered uncertainty where applicable. An analyst should review the methods and outputs independently.
6. Seek external validation in another setting. Then design an appropriately approved prospective silent study before considering any workflow where predictions could affect care. Clinical impact, usability, human oversight, and jurisdiction-specific regulatory requirements need separate review.

## Candidate data routes

| Source | Useful next step | Why it does not validate Rory by itself |
| --- | --- | --- |
| [CDC NHAMCS public-use files and documentation](https://www.cdc.gov/nchs/nhamcs/documentation/index.html) | Review the pediatric subset, year-specific variables, missing codes, data-use conditions, and survey design with a mentor. | Recorded ED urgency and coded visit reasons are a different endpoint and representation from HOME/ED/911 and free-text complaints. Population estimates need survey weights and design variables; the current unweighted evaluator is not a NHAMCS analysis. |
| [PhysioNet Paediatric Intensive Care database](https://physionet.org/content/picdb/1.1.0/) | A qualified research partner can assess eligibility and obtain the required credentials, training, and data-use agreement. | It contains pediatric intensive-care data from a particular hospital setting. It cannot validate a pre-ED or general arrival triage claim without a separately justified study. |
| A partner institution's pediatric ED cohort | Define the intended use and reference labels, then request an approved extract with reliable feature and outcome timestamps. | Requires a partner, governance approval, appropriate sample size, and independent evaluation. None is currently in place. |

No adult dataset is being substituted for a pediatric validation study. No restricted dataset has been accessed and no access forms have been submitted.

## Artifacts and licensing

The source code remains under MIT. Dataset permissions, model-weight licenses, research ethics approval, clinical validation, and regulatory authorization are separate matters. Adding a license file does not make the system clinically validated.

The IMDRF [Software as a Medical Device clinical evaluation framework](https://www.imdrf.org/documents/software-medical-device-samd-clinical-evaluation) distinguishes valid clinical association, analytical validation, and clinical validation. This project is preparing technical evidence and a study workflow. Its future regulatory route depends on its intended use and jurisdiction.

Auxiliary DBSCAN and centroid artifacts must be regenerated using the same normalized model input path and a recorded training split. `generate_artifacts.py --help` lists explicit paths. It rejects legacy statistics without cohort/checkpoint hashes and split membership. Do not relabel the old auxiliary artifacts as corrected without regeneration and testing.
