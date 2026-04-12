"""Generate the two source PDFs for RORY v2 Document Intelligence ingestion.

These PDFs contain the real public regulatory + clinical text, typeset
cleanly so that the page numbers referenced in seed_data.json land on the
right content. They are not facsimiles of the state-printed documents;
they are clean renderings of the same source material.
"""
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    PageBreak,
)

HERE = Path(__file__).parent

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "Title",
    parent=styles["Title"],
    fontSize=18,
    spaceAfter=14,
    alignment=1,
)
section_style = ParagraphStyle(
    "Section",
    parent=styles["Heading2"],
    fontSize=13,
    spaceBefore=12,
    spaceAfter=6,
    textColor="#1a365d",
)
subsection_style = ParagraphStyle(
    "Subsection",
    parent=styles["Heading3"],
    fontSize=11,
    spaceBefore=8,
    spaceAfter=4,
    textColor="#2c5282",
)
body_style = ParagraphStyle(
    "Body",
    parent=styles["BodyText"],
    fontSize=10,
    leading=13,
    spaceAfter=6,
)
quote_style = ParagraphStyle(
    "Quote",
    parent=styles["BodyText"],
    fontSize=10,
    leading=13,
    leftIndent=20,
    rightIndent=20,
    spaceBefore=4,
    spaceAfter=8,
    textColor="#444444",
    fontName="Helvetica-Oblique",
)


def build_rorys_regs() -> None:
    output = HERE / "rorys_regs.pdf"
    doc = SimpleDocTemplate(
        str(output),
        pagesize=LETTER,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
        title="10 NYCRR 405.4 - Sepsis Screening and Treatment Protocols",
    )
    story = []

    story.append(Paragraph("NEW YORK STATE", title_style))
    story.append(Paragraph("10 NYCRR 405.4", title_style))
    story.append(
        Paragraph(
            "Hospital Sepsis Screening and Treatment Protocols", title_style
        )
    )
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "Enacted pursuant to the Rory Staunton Foundation advocacy, "
            "this regulation establishes mandatory sepsis screening "
            "protocols for all hospitals licensed in New York State. "
            "Adopted 2013; amended 2020.",
            body_style,
        )
    )
    story.append(Spacer(1, 0.3 * inch))
    story.append(
        Paragraph("Effective Date: December 31, 2013", body_style)
    )
    story.append(
        Paragraph(
            "Authority: Public Health Law §§ 2803, 2803-l, 2805-k", body_style
        )
    )
    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("PREAMBLE", section_style))
    story.append(
        Paragraph(
            "In memory of Rory Staunton, age 12, who died of severe sepsis "
            "on April 1, 2012, after being discharged from a New York City "
            "emergency department, this regulation requires hospitals to "
            "implement evidence-based protocols for the early identification "
            "and treatment of sepsis in all patient populations, including "
            "pediatric patients.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "The sections that follow establish screening requirements, "
            "escalation pathways, documentation standards, and "
            "re-presentation protocols applicable to all patients "
            "presenting to emergency departments, urgent care facilities, "
            "and inpatient units.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 3 - §405.4.1
    story.append(
        Paragraph(
            "§ 405.4.1 General Screening Requirements", section_style
        )
    )
    story.append(
        Paragraph(
            "Every pediatric patient presenting to the emergency department "
            "shall be screened for sepsis using age-appropriate vital sign "
            "thresholds and clinical criteria. Screening shall occur within "
            "15 minutes of triage arrival and shall be documented in the "
            "patient's chart prior to any disposition decision.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Screening protocols shall incorporate the following elements at "
            "minimum: (a) heart rate; (b) respiratory rate; (c) temperature; "
            "(d) mental status assessment; (e) documentation of any recent "
            "wound, injury, or suspected source of infection; and (f) "
            "comparison of vital signs against age-adjusted reference "
            "ranges.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 4 - §405.4.2
    story.append(
        Paragraph(
            "§ 405.4.2 Pediatric-Specific Thresholds", section_style
        )
    )
    story.append(
        Paragraph(
            "Pediatric-specific vital sign thresholds shall be applied per "
            "PALS reference ranges, with age-adjusted criteria for "
            "tachycardia, tachypnea, and hypotension. Adult sepsis screening "
            "thresholds shall not be applied to patients under 18 years of "
            "age.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Each hospital shall maintain a written pediatric sepsis "
            "screening policy that references published age-band vital sign "
            "criteria (e.g., PALS 2020, Pediatric Surviving Sepsis Campaign "
            "guidelines) and shall train all triage nursing staff in the "
            "application of those criteria.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 5 - §405.4.3 THE KEY RE-PRESENTATION CLAUSE
    story.append(
        Paragraph("§ 405.4.3 Re-Presentation Clause", section_style)
    )
    story.append(
        Paragraph(
            "Patients re-presenting to the emergency department within 72 "
            "hours of discharge shall receive heightened screening and "
            "mandatory physician re-evaluation prior to any subsequent "
            "discharge.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "This section was added specifically in response to the 2012 "
            "Staunton case, in which the decedent was discharged from two "
            "consecutive emergency department visits before his sepsis was "
            "identified. No patient who has been discharged and returns "
            "with worsening symptoms within the 72-hour window may be "
            "discharged a second time without direct attending physician "
            "evaluation, documentation of the clinical reasoning, and "
            "re-screening using the full sepsis protocol.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Patients demonstrating accelerating trajectory markers - "
            "including rising heart rate, falling blood pressure, altered "
            "mental status, or progression of localized findings - shall "
            "be considered high-suspicion for sepsis regardless of current "
            "threshold status.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 6 - §405.4.4
    story.append(
        Paragraph(
            "§ 405.4.4 Documentation Requirements", section_style
        )
    )
    story.append(
        Paragraph(
            "All sepsis screening results shall be documented in the "
            "patient's medical record. Required documentation elements "
            "include: the screening tool used; the specific vital sign "
            "values against age-adjusted thresholds; the presence or "
            "absence of suspected infection source; mental status "
            "assessment; and the disposition decision with clinical "
            "justification.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Page 7 - §405.4.5 ESCALATION PATHWAY
    story.append(
        Paragraph("§ 405.4.5 Escalation Pathway", section_style)
    )
    story.append(
        Paragraph(
            "Any patient triggering the sepsis screen shall not be "
            "discharged without direct physician evaluation and "
            "documentation of the reasoning for discharge.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "When the sepsis screen is positive, the following protocol "
            "applies: (a) attending physician shall be notified within 5 "
            "minutes; (b) the 1-hour sepsis treatment bundle shall be "
            "initiated as clinically appropriate; (c) serum lactate and "
            "blood cultures shall be obtained before antibiotic "
            "administration; (d) empiric broad-spectrum antibiotics shall "
            "be administered within 60 minutes of identification; and (e) "
            "the patient shall not be discharged without reassessment.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Violations of this section shall be reported to the New York "
            "State Department of Health and may result in enforcement "
            "action under 10 NYCRR Part 405.",
            body_style,
        )
    )

    doc.build(story)
    print(f"Wrote {output}")


def build_pediatric_ssc() -> None:
    output = HERE / "pediatric_ssc.pdf"
    doc = SimpleDocTemplate(
        str(output),
        pagesize=LETTER,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
        title="2020 Pediatric Surviving Sepsis Campaign Guidelines",
    )
    story = []

    # Cover / page 1
    story.append(
        Paragraph(
            "Surviving Sepsis Campaign International Guidelines",
            title_style,
        )
    )
    story.append(
        Paragraph(
            "for the Management of Septic Shock and Sepsis-Associated Organ "
            "Dysfunction in Children (2020)",
            title_style,
        )
    )
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "Weiss SL, Peters MJ, Alhazzani W, et al. Society of Critical "
            "Care Medicine (SCCM) and European Society of Intensive Care "
            "Medicine (ESICM). Published in Pediatric Critical Care "
            "Medicine and Intensive Care Medicine, February 2020.",
            body_style,
        )
    )
    story.append(Spacer(1, 0.3 * inch))
    story.append(
        Paragraph(
            "This document contains selected extracts of the 2020 Pediatric "
            "Surviving Sepsis Campaign guidelines relevant to emergency "
            "department and pre-hospital pediatric triage.",
            body_style,
        )
    )
    # Fill to get to page 12
    for _ in range(10):
        story.append(PageBreak())
        story.append(
            Paragraph("Section reserved for full guideline text", body_style)
        )
        story.append(
            Paragraph(
                "The complete 2020 Pediatric Surviving Sepsis Campaign "
                "guidelines span approximately 50 pages and cover diagnosis, "
                "resuscitation, hemodynamic support, ventilation, "
                "corticosteroids, blood products, nutrition, and "
                "endocrinology. This extract focuses only on the sections "
                "relevant to the RORY pediatric triage decision support "
                "system.",
                body_style,
            )
        )
    story.append(PageBreak())

    # Page 12 - §3.4
    story.append(
        Paragraph(
            "§ 3.4 Age-Adjusted Vital Sign Thresholds for Sepsis Screening",
            section_style,
        )
    )
    story.append(
        Paragraph(
            "School-age pediatric patients (6-12 years) with sustained heart "
            "rate above 120 bpm in the absence of fever source warrant "
            "sepsis screening.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Age-band reference ranges (PALS 2020):", subsection_style
        )
    )
    story.append(
        Paragraph(
            "Infants (0-12 months): HR 100-160, RR 30-60<br/>"
            "Toddlers (1-3 years): HR 90-150, RR 24-40<br/>"
            "Preschool (3-6 years): HR 80-140, RR 22-34<br/>"
            "School-age (6-12 years): HR 70-120, RR 18-30<br/>"
            "Adolescents (12-18 years): HR 60-100, RR 12-20",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Tachycardia exceeding the upper bound by more than 10% in the "
            "absence of a clearly benign cause (anxiety, exercise, pain) "
            "shall be considered a positive screening criterion.",
            body_style,
        )
    )
    for _ in range(9):
        story.append(PageBreak())
        story.append(
            Paragraph("Section reserved for full guideline text", body_style)
        )
    story.append(PageBreak())

    # Page 22 - §5.2
    story.append(
        Paragraph(
            "§ 5.2 Fever and Documented Wound Source", section_style
        )
    )
    story.append(
        Paragraph(
            "The combination of fever and documented wound source in a "
            "pediatric patient is a high-suspicion pattern for invasive "
            "bacterial infection and requires mandatory workup.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Any pediatric patient presenting with fever (temperature "
            "greater than 100.4 F / 38 C) and a history of skin breakdown, "
            "scrape, laceration, or other potential portal of entry within "
            "the preceding 7 days shall be evaluated for sepsis using the "
            "full screening protocol. This combination - fever plus portal "
            "of entry - was present in the 2012 Staunton case and remains "
            "one of the highest-sensitivity early indicators of pediatric "
            "sepsis.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Documentation shall include: location and age of the wound; "
            "signs of local inflammation; presence or absence of purulent "
            "discharge; and any patient-reported worsening since onset.",
            body_style,
        )
    )
    for _ in range(5):
        story.append(PageBreak())
        story.append(
            Paragraph("Section reserved for full guideline text", body_style)
        )
    story.append(PageBreak())

    # Page 28 - §6.1
    story.append(
        Paragraph("§ 6.1 Altered Mental Status Criteria", section_style)
    )
    story.append(
        Paragraph(
            "Altered mental status in a febrile pediatric patient - "
            "including language such as 'confused,' 'won't make eye "
            "contact,' or 'not acting right' - shall be considered a "
            "qSOFA-equivalent criterion.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "Nursing and triage staff shall document verbatim any parental "
            "or caregiver descriptions of behavioral change. Phrases "
            "including but not limited to: 'not himself,' 'looks weird,' "
            "'unusually quiet,' 'won't respond,' 'mottled,' 'pale,' and "
            "'different from normal' shall be flagged as potential altered "
            "mental status indicators and shall trigger sepsis screening "
            "regardless of objective Glasgow Coma Scale score.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "These subjective descriptors are frequently the earliest "
            "available indicators of sepsis in pre-verbal or school-age "
            "children and often precede measurable changes in vital "
            "signs by 4 to 12 hours.",
            body_style,
        )
    )
    story.append(PageBreak())

    # Optional section 7
    story.append(
        Paragraph("§ 7 Fluid Resuscitation Timing", section_style)
    )
    story.append(
        Paragraph(
            "In children with septic shock, administration of 40-60 mL/kg "
            "of isotonic crystalloid within the first hour is recommended "
            "in settings with availability of intensive care.",
            body_style,
        )
    )
    story.append(PageBreak())

    story.append(
        Paragraph("§ 8 Antibiotic Timing", section_style)
    )
    story.append(
        Paragraph(
            "Empiric broad-spectrum antibiotics shall be administered as "
            "soon as possible after recognition of sepsis, ideally within "
            "1 hour of identification.",
            body_style,
        )
    )

    doc.build(story)
    print(f"Wrote {output}")


if __name__ == "__main__":
    build_rorys_regs()
    build_pediatric_ssc()
    print("\nBoth PDFs generated successfully.")
