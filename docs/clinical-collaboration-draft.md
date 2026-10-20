# Clinical collaboration request

Status: unsent draft for Aadi to review and send. No clinician, hospital, institutional affiliation, data-access permission, or approval has been secured.

## Suggested first contact

The CHOP Pediatric Sepsis Program publishes `sepsis@email.chop.edu` for inquiries. Its research activities include sepsis screening, registry adjudication, and a multicenter pediatric sepsis registry. This makes it a relevant place to request direction to a research mentor, although it does not establish that the program accepts outside projects or shares its data. [Official contact](https://www.chop.edu/centers-programs/pediatric-sepsis-program/contact), [research activities](https://www.chop.edu/centers-programs/pediatric-sepsis-program/resources-for-professionals)

## Email draft

To: sepsis@email.chop.edu

Subject: Research mentorship for retrospective pediatric triage evaluation

Hello Pediatric Sepsis Program team,

My name is Aadi Tiwari. My teammate and I built Rory, a pediatric triage research prototype that combines a presenting complaint with vital signs. It currently returns an urgency score and HOME / ED / 911 categories. It is not clinically validated. This request concerns retrospective research, with no patient-care changes.

We are looking for a pediatric emergency clinician or sepsis researcher who could help us define a defensible retrospective research question and identify an appropriate supervised data-access route.

Our existing training cases are synthetic or illustrative. We have prepared an offline evaluation pipeline that freezes the checkpoint, separates evaluation records from declared development data, checks predictor availability, and reports missed cases, false alarms, uncertainty, and subgroup results. We are also investigating a limited public-data admission benchmark. That benchmark lacks clinical narrative and cannot establish sepsis performance.

The proposed next study would evaluate the frozen score against a clinically specified sepsis outcome at an initial ED assessment, with an existing screen as the comparator and a separate hospital cohort for external evaluation. The outcome definition, onset timing, and research governance would need your institution's review. We understand that the existing urgency score is not a sepsis probability.

Could you direct us to an appropriate research contact or mentorship route? We would work within an institution-approved environment and access process. We are not requesting patient records by email.

Thank you,
Aadi Tiwari

Before sending, confirm that every statement still matches the project and add a repository link and any affiliation you want to disclose. Do not imply an affiliation or access permission that you do not have.

## Review packet

Include the [provisional protocol](retrospective-study.md), [cohort contract and execution guide](retrospective-evaluation.md), [public admission benchmark](public-triage-benchmark.md), and its aggregate results when available.

The clinical collaborator needs to resolve:

| Decision | Current proposal or unresolved point |
| --- | --- |
| Intended use | Retrospective research at the first ED assessment; school-nurse recommendations are outside this study. |
| Index | Completion of initial nursing assessment, with source and availability times for every input. Feasibility must be checked against hospital records. |
| Outcome | Incident sepsis within the next 24 hours is provisional. Specify the clinical criteria, source fields, onset rule, adjudication, and handling of sepsis already present. |
| Follow-up | Define complete negative ascertainment, transfers, discharge, death, and uncertain outcomes. A known positive need not survive the whole window. |
| Comparator | The actual local screen available at index, with its version and result recorded independently of Rory. |
| Cohort selection | Consecutive eligible patients, one linked encounter per patient, recorded exclusions, known site and calendar periods. |
| Governance | Institutional determination and data-owner authorization, permitted personnel, approved compute, retention, and aggregate-output review. |
| Precision | Event prevalence and feasible cohort size must determine a justified precision target before confirmatory analysis. |
| External cohort | Reserve an independently collected hospital cohort before fitting or threshold selection. An ICU cohort cannot establish ED or school-nurse transfer. |
| Calibration | Requires a genuine binary sepsis label and a separate development cohort to fit a probability model. Evaluate that new model on untouched patients; do not treat the current urgency score as a probability. |

The initial data feasibility check needs original complaint text, heart rate, respiratory rate, temperature and units, oxygen saturation, numeric capillary refill where available, age, linked pseudonymous patient and encounter IDs, site, predictor timestamps, outcome/onset/follow-up, and the recorded baseline screen. Missing inputs should remain missing. Generated complaints, discharge summaries used as presenting notes, and diagnosis codes without onset cannot satisfy the proposed protocol.
