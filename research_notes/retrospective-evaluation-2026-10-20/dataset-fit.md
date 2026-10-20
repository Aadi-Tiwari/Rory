# Dataset fit for Rory retrospective evaluation

Assessed 2026-10-20. The required inputs supplied for this review are initial HR, RR, temperature, SpO2, capillary refill, age, sex, weight, and complaint text. The intended clinical outcome and prediction horizon still need clinical specification.

**Recommendation: pursue a governed pediatric ED export with a clinical research partner for the unchanged multimodal Rory model.** No inspected release supports a defensible real-patient run of the complete current input contract today. Publicly accessible real pediatric records do exist, but the inspected unrestricted cohort lacks the required inputs. This is a bounded search finding, not a claim that no suitable dataset exists anywhere.

## Best available candidates

| Candidate | Fit and access | Evaluation that could be supported |
| --- | --- | --- |
| PECARN Registry public-use release | Real US pediatric ED visits; patient-level access requires an agreement and institutional approval or exemption. | A separately specified structured-data study after access and schema checks. Current public-use fields do not support complete Rory inputs. |
| PhysioNet PIC | Real pediatric critical-care admissions at a Chinese hospital, credentialing/training/agreement required. | A narrower ICU research question after cohort and outcome adjudication. This does not validate school-nurse referral or HOME/ED/911 safety. |
| Smart Triage Kenya/Uganda | Similar arrival-time setting and prospectively measured clinical variables; case-by-case access and governance approval. | A separately approved triage-severity comparison; sites offer geographic transfer testing, but the studied outcome is not sepsis onset. |
| Open pediatric CRRT/sepsis cohort | Public CC0 workbook successfully retrieved and headers inspected. | Biomarker/prognosis research. Required Rory vitals and complaint text are absent. |
| Pediatric Sepsis Data Challenge | Participant dataset is synthetic; original test records were withheld and the challenge has ended. | Development exercises only with participant data. It cannot supply the requested independent real-record evaluation. |

Sources and exact versions are in [dataset-sources.md](dataset-sources.md).

## PECARN: closest released setting, incomplete inputs

The inspected [public-use dictionary](https://pecarn.org/wp-content/uploads/2026/02/PECARN-Registry-v1-PUD-Dataset-Specifications.xlsx) contains `HeartRate`, `RespiratoryRate`, `TempC`, `WeightKg`, age in days/years, sex, `PersonID`, `EDYear`, `EDMonth`, and `VitalTimeMin`. It does not list SpO2, capillary refill, complaint text, narrative notes, or a hospital/site identifier. Temperature conversion is straightforward; a documented age-conversion rule would still be needed.

Diagnosis codes are billing or clinician-assigned codes, sometimes combining ED and inpatient sources. They have no onset timestamp. Medications have no administration times in this release. ESI category, disposition and hospital vital status are available, but none is an interchangeable sepsis label. Relative vital times support measurement windows, not a verified entry-time cutoff. Calendar fields permit a later-cohort design; the missing site key prevents a site-held-out analysis using this release alone.

My inference: filling the missing modalities with normal values, invented complaint text, or assumed labels would invalidate an unchanged-model claim. A complete-case analysis also cannot recover variables omitted from the entire release. Access requirements remain a separate barrier. [PECARN access policy](https://pecarn.org/datasets/)

## PIC: useful clinical timing, substantial mismatch

The [release description](https://physionet.org/content/picdb/1.1.0/) states that original narrative documents are not released. `EMR_SYMPTOMS` contains extracted symptoms instead. The database is selected through critical-care admission, and surgery measurements are a distinct stream. SpO2 was added to the surgery table in the current release; that does not establish availability at initial triage. Exact item mappings, weight coverage and capillary-refill availability remain unverified without the released dictionary.

Dates are shifted by a patient-specific offset. Within-patient intervals remain useful; comparing shifted calendar dates across different patients cannot establish a true historical training/test boundary. Independent hospitals are not included.

For any eventual extraction:

- Apply the prediction cutoff to measurement time and clinical availability time. PIC distinguishes `CHARTTIME` from `STORETIME`, the latter recording entry or validation. [Chart documentation](https://github.com/Healthink/PIC/blob/master/pic-doc/src/components/Pages/chartevents.vue)
- Restrict extracted symptoms using `RECORDTIME` and source-document provenance. The source pool includes discharge summaries. Never reconstruct a complaint from later recorded symptoms. [Symptom documentation](https://github.com/Healthink/PIC/blob/master/pic-doc/src/components/Pages/emr_symptoms.vue)
- Treat end-of-stay ICD diagnoses as potential outcome evidence, never triage predictors. They lack sepsis-onset timing. [Diagnosis documentation](https://github.com/Healthink/PIC/blob/master/pic-doc/src/components/Pages/diagnoses_icd.vue)
- The admission `DIAGNOSIS` field is a preliminary Chinese diagnosis rather than a presenting complaint. Using it as complaint text would change the task and risk revealing clinical conclusions. [Admission documentation](https://github.com/Healthink/PIC/blob/master/pic-doc/src/components/Pages/admissions.vue)

## The unrestricted-data check

The [open CRRT cohort](https://doi.org/10.6084/m9.figshare.30812312.v1) is a concrete counterexample to a blanket "all real pediatric data are restricted" claim. Its original workbook was retrieved in memory and its headers inspected. It includes age, sex, prognosis, organ-dysfunction categories, PRISM III, pSOFA and biomarkers. It lacks the requested HR, RR, temperature, SpO2, capillary refill, weight and complaint text. No patient rows were retained or used for inference.

A second [open septic-shock cohort](https://doi.org/10.5281/zenodo.15081539) has accessible release metadata, but its XLS field schema was not verified. The [study](https://advances.umw.edu.pl/ahead-of-print/204830.pdf) concerns mortality among children already admitted with septic shock. Even if inputs were sufficient, that selected population could not estimate false alarms among general pediatric presentations.

For [Smart Triage](https://journals.plos.org/digitalhealth/article?id=10.1371/journal.pdig.0000293), the reviewed Kenyan evaluation used a composite of admission, early mortality, readmission or referral. It excluded children needing immediate emergency treatment. Both the paper's access statement and the [Borealis file metadata](https://borealisdata.ca/dataset.xhtml?persistentId=doi:10.5683/SP3/4OI0BI) impose access restrictions. A public article, public dictionary or open-license metadata entry does not establish that its patient files are unrestricted.

## Concrete acquisition target

For the first unchanged-model retrospective study, obtain an authorized export with patient and encounter identifiers, a site or cohort identifier, initial measurement and recording times, genuinely pre-prediction complaint text, the required units, and separately adjudicated outcome/onset/follow-up fields. Define the clinical target and horizon before inspecting outcomes. Preserve repeat-patient grouping across every split. Select and freeze comparator rules using only measurements available in the same window.

The strongest next acquisition route is a pediatric ED research collaborator who can confirm these fields and the outcome definition. PECARN is a possible structured-data fallback if the study is explicitly reframed; PIC is an ICU fallback if the intended population is explicitly changed. Neither is an automatic substitute for the current multimodal referral task. No clinical validation result has been produced by this dataset review.
