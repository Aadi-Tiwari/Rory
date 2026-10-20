# Public pediatric cohort access and fit

Assessed 2026-10-20. This extends the earlier [dataset review](../retrospective-evaluation-2026-10-20/dataset-fit.md) after a broader search for original public cohorts. It corrects the earlier bounded finding that no inspected unrestricted release offered useful Rory vitals.

**The Nairobi pediatric triage release is the strongest immediately usable candidate for a narrowly described exploratory admission benchmark.** Its data are real, publicly downloadable and licensed CC BY 4.0. It does not contain a sepsis endpoint, complaint narratives, independent hospitals or a usable temporal holdout. A no-text and no-verified-capillary-refill analysis changes Rory's input contract and must be reported as an ablation. This source cannot establish safety of HOME / ED / 911 recommendations or calibrate 24-hour sepsis probabilities.

## Nairobi release: exact artifact

[Figshare record 9104918](https://api.figshare.com/v2/articles/9104918), DOI [10.6084/m9.figshare.9104918.v1](https://doi.org/10.6084/m9.figshare.9104918.v1), published 2019-07-25:

- Title: *Derivation and internal validation of a data-driven prediction model to guide frontline health workers in triaging children under-five in Nairobi, Kenya*.
- File: [PaediatricTriage_DATA.csv](https://ndownloader.figshare.com/files/16604291), file ID 16604291.
- License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), verified in the record's API response.
- Unmodified file size: 263534 bytes.
- SHA-256: `36acddd0c4358affd4adc1170f46c10a43d4bd00704a46d4bca5e7dabb3f3e5c`.
- MD5: `2300cec224d5bac90389f9394a342c9e`, independently recomputed and matching Figshare metadata.
- Local copy: `validation_private/public-cohorts/figshare-9104918-PaediatricTriage_DATA.csv`. A neighboring provenance JSON records the source and hash. `git check-ignore -v` confirmed that `validation_private/` is ignored before writing.

Pandas parsed 1135 rows and 70 columns. These are released rows, not a verified count of distinct patients. The article's analysis population differs, so an evaluation must disclose its own reproducible exclusions rather than force a match to published counts.

## Clinical meaning and time

The inspected [article, version 3](https://doi.org/10.12688/wellcomeopenres.15387.3), published 2021-04-19, concerns Mbagathi County Referral Hospital's outpatient department in Nairobi during January to June 2018. The intended ages were 2 to 60 months. Its endpoint was admission lasting at least 24 hours, decided independently by the attending clinician. Discharged children had telephone follow-up after 14 days for recovery, return visits, admission and mortality.

Emergency treatment could start before study measurements. There are no timestamps in this release that permit reconstruction of exactly which observations were available before treatment. The article describes capillary refill as a thresholded sign, at least 2 seconds, rather than documenting the numeric release codes. It reports axillary temperature in Celsius, weight in kilograms, pulse in beats/minute and respiration in breaths/minute. These facts were checked in the complete [primary article XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8097734/fullTextXML), including methods and tables.

## Input audit

| Rory input or evaluation field | Released columns and verified status |
| --- | --- |
| Heart rate | `pulse_rate`, 1099 nonmissing observations; units supported by the article. |
| Respiratory rate | `resp_rate`, 1128 nonmissing; units supported by the article. |
| Temperature | `temp`, 1126 nonmissing; Celsius, requiring explicit conversion for Rory's Fahrenheit input. |
| SpO2 | `oxygen_sat`, 1099 nonmissing; raw saturation rather than the article's later physiological transformation. |
| Capillary refill | `cap_refill_cat`, 1123 nonmissing. Observed codes are 1, 2, 3 and 5. Their exact meanings were not verified. Do not pass these codes as measured seconds. |
| Age | `age_years`, `age_mths`, `age_days`. An author-linked same-cohort script combines components as `years*12 + months + days/30`, replacing missing components with zero unless all are missing. This supports a declared component interpretation, with release-specific data errors still requiring checks. |
| Sex and weight | `child_sex`, `weight`. Weight units are documented. A direct numeric sex-code dictionary was not obtained. |
| Complaint text | No narrative complaint or clinical notes. Symptom flags must not be turned into invented patient narratives. |
| Outcome | `admitted` has codes 0 and 1, plus missing values. The paper supplies the admission endpoint; a same-cohort author script maps a labeled admission answer of `Yes` to 1. The numeric Figshare release has no verified codebook. |
| Treatment timing | `data_resuscitation` has 0/1 codes; the paper discusses data collected after emergency treatment. Exact code correspondence remains unverified, so a `0 = pretreatment` filter must not be silently assumed. |
| Follow-up | `outcome`, `recovered`, `returned`, `readmitted`; numeric encodings were not verified. Do not derive a composite severe outcome from guessed codes. |
| Grouping and holdouts | No patient ID, encounter date or site column. Patient uniqueness and repeat-visit grouping cannot be certified. |

The age interpretation comes from [the author's analysis code at a fixed commit](https://github.com/pmwaniki/ppg-analysis/blob/8679a3a31d023f5e22b7d7c23404fa0bd222d474/EDA/descriptives.py). That project used a separately released, labeled version of the same clinical cohort. Its [admission preprocessing](https://github.com/pmwaniki/ppg-analysis/blob/master/datasets/.ipynb_checkpoints/triage-checkpoint.py) supports the direction of the admission coding, but it is not a substitute for the missing Figshare dictionary.

Code-checked release observations:

- All five named vital fields are nonmissing together in 1083 rows. This is completeness of fields, not validation of the capillary-refill encoding.
- `admitted` counts: code 1 in 140 rows, code 0 in 981 rows, missing in 14 rows.
- One exact duplicate beyond the first occurrence is present. The matching pair each has 59 nonmissing columns, including the outcome and all five named vital fields. It is not an empty placeholder.
- `data_resuscitation` counts: code 0 in 739 rows, code 1 in 388 rows, missing in 8 rows.
- `cap_refill_cat` counts: code 1 in 1063 rows, code 2 in 56 rows, code 3 in 2 rows, code 5 in 2 rows, missing in 12 rows.

No patient-level rows or identifiers are included in these notes.

## Independence and codebook limits

The later [pulse-oximetry paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10280037/) uses the same hospital and recruitment period. Its development/test partition is not an independent hospital validation of the Nairobi cohort. It links Harvard Dataverse DOI [10.7910/DVN/KQ4DNK](https://doi.org/10.7910/DVN/KQ4DNK), containing `Data.csv`, `PaediatricTriage_DataDictionary.tab` and waveform files. The paper says these data require governance review because of potential identifiability.

Public Harvard metadata endpoints returned HTTP 403 in this environment. The dictionary was not retrieved, and no restricted file was accessed. Public author code was inspected as text only. The archived code record is [Zenodo 5501144](https://zenodo.org/records/5501144), MIT licensed. It does not provide a verified code dictionary for every numeric Figshare field.

An unchanged model frozen before evaluation can be tested on this separately sourced population, subject to the stated ablations. If a calibrator or threshold is fitted using part of this release, testing it on another part is an internal split of one site. It does not establish transfer across hospitals or later cohorts.

## Other primary-source findings

| Candidate | Inspected evidence | Result for this task |
| --- | --- | --- |
| DYNAMIC Tanzania / ePOCT+ | The formerly restricted Zenodo record now resolves to open [version 18187272](https://zenodo.org/records/18187272), published 2026-01-08, CC BY 4.0. The actual [Stata file](https://zenodo.org/api/records/18187272/files/DYNAMIC%20TZ%20cluster%20RCT%20study%20dataset_anonymized.dta/content) and variable labels were inspected in memory. | Has age group, sex, complaint categories, patient/site fields, treatment and follow-up outcomes. The released fields do not include Rory's vital measurements. It is not a usable independent validation set for a vitals model. |
| DYNAMIC Rwanda / ePOCT+ | Open [Zenodo 15870974](https://zenodo.org/records/15870974), published 2025-07-12, CC BY 4.0. Actual [workbook](https://zenodo.org/api/records/15870974/files/dynamic_rwanda_dataset_v2.xlsx/content) headers and dictionary were inspected in memory. | Contains identifiers, date, facility, age category, sex, complaint categories, referral, hospitalization and clinical-failure outcomes. No Rory vital fields in the released data sheet. |
| PERFORM / MOFICHE | [Primary IBI paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC8237171/) describes a multicenter febrile-child cohort and points to [DOI 10.14469/hpc/7549](https://doi.org/10.14469/hpc/7549); another relevant release is [10.14469/hpc/10644](https://doi.org/10.14469/hpc/10644). | Potentially useful independent ED sites and an invasive-bacterial-infection endpoint, which is not synonymous with sepsis. Both DOI routes led to an official Imperial migration notice; externally available patient data could not be retrieved. |
| Spot Sepsis | The [2026 final article](https://www.nature.com/articles/s41591-026-04338-1) and [earlier primary preprint](https://www.medrxiv.org/content/10.1101/2025.10.12.25337822v1.full.pdf) describe febrile children across South and Southeast Asia, with a held-out Cambodian cohort and referral-need outcome based on death or organ support. The preprint's availability section requires committee review. | Stronger clinical setting and site-transfer design, but no unrestricted original patient download was found. Final full-text availability wording was not successfully extracted; the access finding rests on the inspected primary preprint. |
| Ghana Fever in Focus | Open [Zenodo 8220138](https://zenodo.org/records/8220138), CC BY 4.0, original [RData](https://zenodo.org/api/records/8220138/files/fws_all_obs.rdata/content) and [author analysis script](https://zenodo.org/api/records/8220138/files/Fever-in-focus_pubcode_an-230807.R/content). Metadata and script were inspected; the RData schema was not parsed. | Script documents admission temperature, age, symptoms, suspected/discharge diagnoses and bacteriology. It does not establish availability of other Rory vitals. A discharge diagnosis containing sepsis is not an adjudicated incident-sepsis label. This is a possible much narrower follow-up study, not a stronger immediate full-model candidate. |

Imperial's [official repository notice](https://www.imperial.ac.uk/admin-services/ict/self-service/research-support/rcs/about/research-management-applications/hpc-repository/) says outside-network access is temporarily unavailable during migration to Helix, with completion expected in November 2026. It directs external requests through staff communication. No request was sent and no access barrier was bypassed. This is a current availability problem, not proof the underlying release is permanently restricted.

The DYNAMIC files were retrieved only to inspect schema and retained in memory. Their primary studies concern clinical management and follow-up outcomes, not an interchangeable 24-hour sepsis target. Public availability alone does not make either release fit Rory's inputs.

## Supported next action

Freeze a protocol and the Rory artifact before running the Nairobi admission benchmark. Preserve the raw file and hash, disclose the age interpretation, exclude unknown outcomes, handle exact duplicates explicitly, and avoid ambiguous codes. Report missing-text and missing-capillary-refill ablations by name. Freeze comparator and threshold rules before examining prediction results. Any confidence intervals must acknowledge the inability to verify repeat-patient grouping.

This search found an actionable original pediatric cohort, but did not find an immediately downloadable cohort that simultaneously supplies the current multimodal inputs, verified sepsis outcome/onset, and an independent external site. Sepsis calibration and clinical validation therefore remain unfinished. The narrower admission benchmark can produce useful execution evidence without changing that conclusion.
