# Outcome choice and patient-data access

Research date: 2026-10-20. Scope: existing clinical labels, access requirements, and the first defensible patient benchmark for Rory. Public documentation and metadata were inspected. No access request, agreement, membership application, or external message was submitted.

## Recommendation

Prefer a dataset's established, documented endpoint over inventing an incident-sepsis endpoint that its fields cannot support. An exploratory benchmark against an existing clinical label does not inherently require a new physician to approve that label. Permission to use the data, institutional requirements, and correct scientific interpretation are separate questions.

The current protocol's universal requirement for a pediatric collaborator's approval is a conservative choice for its proposed new endpoint, not a universal rule for every secondary-data benchmark. Do not mark that requirement approved without approval. A different benchmark needs an explicitly revised specification identifying its released endpoint and applicable governance basis.

The newly identified open Nairobi release supports a narrower immediate experiment: a frozen-model, missing-text and missing-capillary-refill admission benchmark. Proceed under that explicit scope after the field mapping is checked. Keep the existing incident-sepsis protocol separate. The Figshare record supplies its clinical CSV under CC BY 4.0 without a separate access application on the inspected release page. [Nairobi release, version 1](https://doi.org/10.6084/m9.figshare.9104918.v1)

The restricted multisite Smart Triage release remains a possible later acquisition target. It may support a broader independent-site illness-severity study, subject to its actual field coverage and permission. Neither endpoint should be relabeled sepsis onset.

## Immediate Nairobi experiment

The primary study enrolled children aged 2-60 months presenting with acute illness at Mbagathi Hospital during weekday daytime hours. Its outcome section specifies clinician-determined admission lasting at least 24 hours. Emergency patients started study data collection only after emergency treatment had begun. Admission is a surrogate for illness severity, and the article discusses limits involving children discharged home. [Primary Nairobi study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8097734/)

Recommended experiment:

- Use the published `admitted` outcome after verifying its encoding against the release and article. Do not require a sepsis-onset timestamp or fabricate one.
- Map pulse, respiratory rate, temperature, and oxygen saturation using verified units. Treat categorical capillary refill as missing unless a valid numeric mapping is actually documented. Freeze the text input as empty for every patient. Do not translate structured symptoms or diagnoses into a fabricated complaint.
- Label the index as the study measurement occasion. Describe the result as an admission-association stress test using recorded study-time measurements. The source design does not support calling all measurements pretreatment or initial triage measurements.
- Keep the model, preprocessing, and original thresholds frozen; perform no fitting in this first experiment. Report discrimination against admission and descriptive urgency outputs. A high urgency output without admission is not necessarily an inappropriate clinical decision.
- Verify `data_resuscitation` encoding before using it. Report its relationship to inclusion and separate results by the recorded flag if supported. The flag alone does not establish precise intervention or measurement timing. If coding remains uncertain, report that uncertainty rather than assuming a value means pretreatment.
- Check release age bounds, duplicates, missing outcomes, missing vitals, and any difference between released rows and the published analysis population. Preserve an explicit exclusion ledger. Do not force the result to match a published count or reuse the study's fitted performance as a Rory baseline.
- This file is one external clinical source relative to Rory's synthetic development. It is not a second-hospital validation, sepsis evaluation, probability calibration, validation of the full multimodal input, or evidence of safe HOME / ED / 911 disposition.

The supplied input coverage and candidate resuscitation field were identified by the parallel dataset audit; this bounded review independently checked the release metadata and source study, not patient-level values. Actual counts and subgroup coding belong in the execution report after local checks.

## What existing labels can establish

| Available reference label | Defensible analysis | Claim it cannot establish |
|---|---|---|
| Released sepsis diagnosis without onset | Association or discrimination against that documented diagnosis in the released population | Sepsis developing after triage within a specified future window |
| Clinician-assigned triage category | Agreement with recorded clinical triage | Correct HOME / ED / 911 disposition or improved outcomes |
| Published admission, mortality, readmission, or referral composite | Prediction of the exact published composite from eligible arrival-time measurements | Sepsis specifically, or safe home discharge |
| Verified incident-sepsis phenotype with onset, baseline status, and follow-up | A prespecified future-event study | Clinical benefit from acting on the model |

These are proposed study interpretations, not statements that a particular release contains every required field. Preserve the original outcome coding and exclusions. Do not turn diagnoses, admission, or triage categories into interchangeable labels.

### Phoenix is a disease definition, not the triage screen

Phoenix identifies pediatric sepsis using suspected or confirmed infection plus a Phoenix Sepsis Score of at least two, covering respiratory, cardiovascular, coagulation, and neurological dysfunction. The consensus explicitly distinguishes this from early screening before organ dysfunction. Its development evaluated organ-dysfunction information from the first 24 hours; this does not itself give an incident-onset label after an initial assessment. The paper also specifies neonatal applicability restrictions. A generic age-in-months filter is insufficient to resolve those restrictions. [Primary consensus paper](https://jamanetwork.com/journals/jama/fullarticle/2814297)

Consequently, Rory's five vitals cannot establish a Phoenix reference outcome by themselves. If a cohort already supplies an appropriately documented Phoenix label, use that exact endpoint. If it supplies only a maximum first-day score, call the outcome first-day Phoenix-defined sepsis, not incident sepsis after index. Deriving onset from raw records requires a separately specified infection definition, component timing, observation windows, and baseline assessment. Do not manufacture those facts from a final diagnosis.

### Published Smart Triage outcome

The Kenyan validation used a composite involving clinician-determined admission longer than 24 hours, early mortality, readmission, or referral, with follow-up. This is not a sepsis diagnosis. The paper reports arrival-time heart rate, temperature, and oxygen saturation among its predictors. It excluded eligible children needing immediate emergency treatment, which limits evaluation of the most urgent cases. [Primary validation study](https://journals.plos.org/digitalhealth/article?id=10.1371/journal.pdig.0000293)

The combined age-group release describes a related admission/mortality/readmission outcome across Kenyan and Ugandan hospitals. Obtain its dictionary rather than assuming all components and horizons match the earlier Kenyan paper. [Borealis dataset](https://borealisdata.ca/dataset.xhtml?persistentId=doi:10.5683/SP3/4OI0BI)

## Governance is not equivalent to clinical endorsement

OHRP distinguishes secondary research using information that investigators cannot identify from research involving identifiable private information. Its guidance recommends institutional policies assigning the determination to an appropriate authority, rather than independent investigator self-determination. This supports separating the governance determination from physician endorsement of a model; it does not establish an exemption for this project. Dataset terms can impose additional requirements. [OHRP guidance, last reviewed 2022-12-30](https://www.hhs.gov/ohrp/coded-private-information-or-biospecimens-used-research.html)

For an unrestricted, appropriately licensed release with an established outcome, the scientific work can be a documented reanalysis without pretending that the original investigators approved Rory. For a controlled release, satisfy its actual access process. An ethics approval or consent waiver for the original collection does not automatically grant secondary users access.

## Exact access routes inspected

### PhysioNet PIC

The current PIC page requires a PhysioNet account, credentialed-user status, approved CITI Data or Specimens Only Research training, and acceptance of the dataset's data-use agreement. The public FAQ describes identity/research review and possible reference confirmation; an academic email or institutional ORCID can help processing but is not described there as an absolute affiliation requirement. The live credentialing form redirects to login, so its full applicant fields were not inspected. [PIC release](https://physionet.org/content/picdb/1.1.0/), [PhysioNet FAQ](https://physionet.org/about/faqs/)

The inspected public PIC license and FAQ did not state a numeric minimum applicant age. This is not proof that every applicant is eligible. Do not infer either a ban on students/minors or guaranteed approval. Each researcher needs their own authorization, and the license prohibits sharing restricted access with others. [PIC license](https://physionet.org/content/picdb/view-license/1.1.0/)

PIC's original narrative clinical documents are withheld; its symptom table was extracted from progress notes and discharge summaries. It is a single-center critical-care cohort with patient-specific date shifting. Thus access would not solve the missing initial complaint or independent-hospital requirements. A source-verified structured-input experiment could be possible, but not the unchanged multimodal ED claim. [PIC release](https://physionet.org/content/picdb/1.1.0/)

### PECARN Registry

PECARN explicitly requires a research data-use agreement and relevant institutional IRB approval or demonstration of exemption under institutional policy. Its general policy describes the agreement as involving the recipient institution, investigator, and coordinating center. The Registry's online agreement asks for contact information and agreement before download. No request was made. No numeric applicant-age minimum was found on the inspected page; independent eligibility without a recipient institution was not established. [PECARN access policy and Registry agreement](https://pecarn.org/datasets/)

The preceding local dictionary audit found initial structured vitals and recorded diagnoses/triage/disposition, but no released complaint text or sepsis-onset time. This run reused that field audit as local evidence rather than re-downloading patient records. A legitimate label would be the recorded diagnosis, triage category, or specified disposition, not fabricated sepsis onset. See [prior field audit](../retrospective-evaluation-2026-10-20/dataset-fit.md).

### Smart Triage through Borealis and Sepsis CoLab

The current public metadata API returned release version 2.1, updated 2026-05-12. Both clinical CSVs and the accompanying code files are restricted. Access terms direct applicants to CoLab membership; some files can remain subject to additional case-by-case approval. The metadata license excludes commercial use. Public metadata and an open article do not make the restricted files freely downloadable. [Dataset and access terms](https://borealisdata.ca/dataset.xhtml?persistentId=doi:10.5683/SP3/4OI0BI)

The live membership form requires identity/contact details, an institution, profession, research interests, motivation, a Borealis/Dataverse account username, agreement to its MOU, and confirmation of accuracy. Profession choices include graduate student, undergraduate student, medical student, and Other. No age minimum was visible. An institution field does not prove that a university appointment is mandatory or that a school affiliation will be accepted. [Membership application](https://rc.bcchr.ca/redcap/surveys/?s=EDCYL7AC79)

The attached MOU includes students among potential collaborators, requires compliance with institutional and national policies, and expressly leaves data rights to separate agreements. Membership alone is therefore not permission to analyze a particular restricted dataset. The form and MOU were read without entering information or agreeing. [MOU attachment on the application](https://rc.bcchr.ca/redcap/surveys/?s=EDCYL7AC79)

### Smart Triage through KEMRI-Wellcome

The Kenyan paper names case-by-case access through the KEMRI-Wellcome Data Governance Committee and a data-sharing agreement. Its current stated contact is `dgc@kemri-wellcome.org`. [Study access statement](https://journals.plos.org/digitalhealth/article?id=10.1371/journal.pdig.0000293)

The official posted 2018 guidelines describe an external application containing requestor and institution details, investigators, requested data, objectives, analysis, timeframe, ethical-approval status, risks, benefits, outputs, and a signed agreement. Prior ethical approval can affect prioritization; a request without it may require a new protocol. The committee considers scientific integrity and relevance to the source community. No numeric applicant-age restriction was found. These are posted guidelines, not confirmation of the exact process the committee would apply today. [Official data-sharing guidelines, sections 3.17-3.18 and Appendix Bii](https://kemri-wellcome.org/zp-content/uploads/2021/02/Data-Sharing-guidelines-KIDMSand-Study-Specific-Data_04Jan2018.pdf)

## Concrete protocol choice after obtaining permitted records

1. Inspect the actual dictionary and aggregate missingness before choosing among the labels above. Preserve the provider's label definition, population, and exclusions. The open Nairobi admission experiment can proceed first; a multisite composite is a separate later study if those records become available.
2. Freeze the existing Rory weights and score. If original predecision text exists, evaluate the multimodal model. If it does not, a separately declared empty-text ablation is possible, with the missing channel fixed identically for every patient. That experiment measures transport of the score under missing text and cannot validate the intended text-and-vitals workflow. Do not generate symptom narratives from diagnoses.
3. First measure the raw score's discrimination against the selected endpoint. Keep the deployed urgency thresholds descriptive; do not interpret them as calibrated endpoint probabilities.
4. If calibration is requested, develop a simple prespecified probability mapping from the frozen score on a separate calibration cohort. This is model updating for a new endpoint. Freeze that mapping before applying it to an untouched hospital or later cohort. Report calibration and Brier score only for those new probabilities against that exact outcome. Calling the updated output a sepsis probability would be wrong when the outcome is admission or urgency.
5. Keep every linked patient in only one role. Reserve a hospital for the final test when genuine site identifiers and sufficient data exist. A random holdout is internal evaluation; an ICU cohort does not establish school or ED disposition safety.

The strongest objection to the empty-text option is that the synthetic model learned text cues, including future reassessment information. A poor result may be unsurprising, and a good result still would not validate the complete intended workflow. The evidence that would reverse the preference for an established composite is a permitted cohort with genuine initial complaints and a validated incident-sepsis phenotype including onset and follow-up.

## What the next clinical collaboration must resolve

For a study of Rory's intended initial pediatric assessment, ask the data custodian to confirm an authorized cohort containing original predecision complaint text; measurement and availability timestamps for vitals and text; linked patient and encounter IDs; age and units; site or period; and the exact existing outcome definition. Clarify whether measurements followed emergency treatment and whether later amendments can be distinguished.

If the intended outcome is incident sepsis, a pediatric clinical investigator should resolve the reference phenotype, infection evidence, baseline sepsis status, event time, neonatal scope, and negative follow-up. For a Phoenix-based phenotype, request the necessary organ-dysfunction and infection evidence rather than expecting Rory's inputs to establish it. Use existing clinical adjudication where available; do not claim a newly approved endpoint merely because its name appears in a file.

The institution or provider should identify the actual access and ethics determination needed for that export. Any human application must truthfully describe the applicant's affiliation, access roles, purpose, and security arrangements. Separate the dataset permission, clinical interpretation review, and any endorsement of Rory. No outreach, form submission, or agreement acceptance has been performed.

## Inspection ledger and remaining limits

| Source | Material inspected | Limit |
|---|---|---|
| Nairobi Figshare 9104918 v1, 2019-07-25 | Official metadata API, license, filename and download availability | Patient-level fields and exclusions delegated to the dataset audit |
| Nairobi primary study, PMC8097734 | Direct HTML methods, eligibility, outcome, emergency-treatment timing, data availability | Study-time measurements do not all precede treatment |
| JAMA Phoenix consensus, 2024 | Full primary article, diagnostic table, applicability and screening caveats | No raw patient cohort obtained |
| Smart Triage Kenyan validation, 2024 | Methods, predictors, endpoint, eligibility, data-access statement | Published endpoint is not sepsis onset |
| Borealis Smart Triage age-group release | Public metadata API, terms, version, restricted-file flags | Patient-file dictionaries and contents remain inaccessible |
| CoLab application and attached MOU | Live fields, profession choices, agreement terms | Membership and dataset access not approved |
| PIC v1.1.0, license, FAQ | Direct official HTML retrieval after web-tool timeout | Credentialing application behind login not inspected |
| PECARN dataset page | General policy and Registry-specific agreement/form | Patient data not accessed; earlier dictionary audit reused |
| KEMRI-Wellcome guidelines | Official PDF, external-request process and application | Posted 2018 policy; no direct confirmation from committee |
| OHRP secondary-use guidance | Official guidance including determination authority | No project-specific ethics determination |

No source inspected establishes that Rory is clinically validated. The open Nairobi release removes the acquisition blocker for its narrowly named admission ablation. The intended initial-assessment, incident-sepsis evaluation still needs suitable inputs, outcomes, and permissions.
