# Case PMC11890614: miliary tuberculosis mistaken for sarcoidosis, then haemophagocytic lymphohistiocytosis

Case id `PMC11890614` · Status: **draft, awaiting Case Reviewer verification** · Structured data: [`gold-case-file.draft.json`](gold-case-file.draft.json) · Path analysis: not yet written (waits for the pilot review)

> Spoiler warning. This file and the JSON contain the answer. They are for the Case Reviewer and for developers, never for a player or a seat.

Drafted on 25 Sep 2026 for Case Library task L1.3 (batch 1, curation steps 1–5 only). Nothing has been written to the Case Vault.

## Source

Li W, Mann P, De La Hoz I, Constantakos A, Gordon D, Everett G, Maharam E. *A Perplexing Case Highlighting the Diagnostic Conundrum of Miliary Tuberculosis Mimicking Sarcoidosis and Progressing Into Hemophagocytic Lymphohistiocytosis.* Cureus 17(2): e78636. Published 6 Feb 2025. doi:[10.7759/cureus.78636](https://doi.org/10.7759/cureus.78636) · [PMC11890614](https://pmc.ncbi.nlm.nih.gov/articles/PMC11890614/) · PMID 40062127

- **Licence:** CC BY 4.0, read from the JATS `<license>` element of the cached XML (`data/articles/PMC11890614/jats.xml`, SHA-256 `0ebdccaf…63b565`). No figure carries its own permissions or credit line, so the article licence covers them. `production_ok` and `public_release_ok` are true for the article; every figure's flags are false until Atul decides.
- **Attribution to reuse:** "Adapted from Li W, Mann P, De La Hoz I, et al., Cureus 17(2): e78636 (2025), CC BY 4.0. Restructured into a simulation; diagnosis hidden until the debrief; simulated findings added where marked."
- **Setting:** AdventHealth, Orlando, USA.

## The case in brief

A 36-year-old man from Haiti, previously well, had four months of recurrent fever, dry cough, night sweats and weight loss. On admission he was febrile (39.0 °C) and tachycardic (115/min), with mild normocytic anaemia, raised inflammatory markers, ferritin 1364 ng/mL and AST 63 U/L. HIV was negative. The chest X-ray and CT showed innumerable bilateral miliary nodules, and abdominal CT showed moderate splenomegaly.

Miliary tuberculosis was expected, but the interferon-gamma release assay, repeated sputum AFB smears, MTB complex PCR and mycobacterial cultures, a bronchoalveolar lavage (AFB smear and culture), and two sequencing tests (Karius cell-free DNA and MicroGenDX) were all negative. A transbronchial lung biopsy showed non-necrotising granulomas with a negative AFB stain. Fungal, other bacterial and viral tests were negative. Sarcoidosis was diagnosed by exclusion and high-dose steroid started.

Fever and cough continued. Pancytopenia developed, with rising ferritin and transaminases (day 17: Hb 6.8 g/dL, WBC 0.03 ×10³/µL, platelets 40 ×10³/µL, ferritin 7821 ng/mL, AST 335, ALT 325 U/L). The H-score was 256; soluble IL-2 receptor 7593 pg/mL and CXCL9 52 784 pg/mL. The marrow showed non-caseating granulomas and occasional haemophagocytes. He was treated for HLH with steroids and etoposide. On day 18 he developed hypoxic respiratory failure and shock. On day 25 the repeat sequencing tests and a second lavage (AFB stain, PCR, later culture) found *Mycobacterium tuberculosis*. Four-drug treatment started and HLH chemotherapy was withheld, but he died about a week later. There was no autopsy.

## What the players start with

> A 36-year-old man, originally from Haiti and with no significant past medical history, presents to the emergency department with four months of recurrent fever and a dry cough.

Opening words: "I've had fevers on and off and a dry cough for about four months now, and they just won't go away."

Night sweats and weight loss are in the Chart, released by the fever, sweats and weight question (`HX.GEN.FEVER_SWEATS_WEIGHT`) or the associated-symptoms question. No fact is hidden behind a specific question the way the pilot's supplement was: the difficulty here is that the tests are falsely reassuring, not that the history hides something.

Display title: "Four months of fever and dry cough in a young man" · slug `c-c149v` · tags: infectious disease, respiratory medicine, haematology, internal medicine · difficulty hard.

## Timeline in the article

Day 0 is admission, the article's hospital day 1 (no calendar date is given). Hospital day N is day N−1 here.

| Day | Event |
| --- | --- |
| 0 | Admission. T 39.0 °C, HR 115. Hb 9.9, WBC 4.5, ANC 2.9, platelets 227, ferritin 1364, AST 63, ALT 40. HIV negative. Chest X-ray and CT: miliary nodules. CT abdomen: moderate splenomegaly |
| Not dated | IGRA, sputum AFB, MTB PCR and cultures, first lavage, fungal and other tests: all negative. Lung biopsy: non-necrotising granulomas, AFB negative. First Karius and MicroGenDX: negative |
| Not dated | High-dose steroid for presumed sarcoidosis; no improvement |
| Not dated (before day 18) | sIL-2R and CXCL9 very high; H-score 256; marrow: granulomas and haemophagocytes; HLH-2004 steroids and etoposide |
| 17 | Hb 6.8, WBC 0.03, ANC 0, platelets 40, ferritin 7821, AST 335, ALT 325 |
| 18 | Hypoxic respiratory failure, intubation, shock on vasopressors; empirical antibiotics and antifungals; CT pulmonary angiogram: no embolism, new bilateral airspace opacities |
| 25 | Repeat Karius and MicroGenDX: MTB complex detected. Second lavage: AFB stain and MTB PCR positive within hours. Rifampin, isoniazid, pyrazinamide and ethambutol started; HLH chemotherapy withheld |
| 29 | CT chest (Figure 4b, "day 30"): diffuse reticulonodular, flocculent and consolidative opacities |
| About 32 | Death after multi-organ failure; later, lavage culture grew *M. tuberculosis* |

The text dates only admission, day 18 (hospital day 19) and day 25 (hospital day 26). Undated results carry `day: null` and a note. Figure 5, a timeline image not read for this draft, probably dates them (gap G21).

## Hidden and conditional facts

None beyond the ordinary Chart. The positive tuberculosis results (L19–L23) are marked `reveals_dx` and `pivotal`, and they belong to day 25. Before day 25, every microbiology result the article reports is negative.

## Raw material for the diagnostic services

| Id | Test | Day | Raw findings |
| --- | --- | --- | --- |
| R01 | Chest X-ray | 0 | Innumerable small nodules in both lungs, miliary pattern |
| R02 | CT chest | 0 | Innumerable bilateral miliary nodules filling both lungs |
| R03 | CT abdomen | 0 | Moderate splenomegaly |
| R04 | CT pulmonary angiogram | 18 | No embolism; new bilateral airspace opacities, worse than on admission |
| R05 | CT chest | 29 | Diffuse reticulonodular, flocculent and consolidative opacities |
| R06 | Transbronchial lung biopsy (attached to `PROC.RESP.BRONCHOSCOPY`) | not dated | Non-necrotising granulomas; AFB stain negative |
| R07 | Bone marrow trephine | not dated | Multiple small foci of non-caseating granulomas |
| R08 | Bone marrow aspirate | not dated | Occasional haemophagocytic cells |

Figures M01–M07 come from Figures 1–4, with neutral captions. Figure 5 (the timeline) is left out of the media because it names the diagnosis and is not a clinical image.

## Gaps to fill

The article reports only two vital signs, no examination, no inflammatory-marker values, and none of the H-score inputs beyond ferritin and the counts. The 22 gaps (G01–G22) are in the JSON. Four are set **not to auto-generate**, because a positive result would end the case early or has to follow the true course: urine and other extrapulmonary mycobacterial samples (G14), marrow AFB and culture (G15), liver biopsy (G16), and the dates of the undated work-up (G21).

## Ground truth (draft)

**Final diagnosis:** miliary tuberculosis (`DX.MILIARY_TB`, A19.9), complicated by secondary haemophagocytic lymphohistiocytosis (`DX.HLH`, D76.1), after a false diagnosis of sarcoidosis and high-dose steroid. The leak scan uses both ids.

Rubric anchors, must-do and must-not-do are in the JSON as plain text; their conditions over catalogue ids wait for step 6.

## Catalogue items this case needs that the catalogue lacks

- Mycobacterial (AFB) culture, for sputum, lavage, marrow and blood
- MTB complex PCR as a generic test (only Xpert MTB/RIF exists; L04 is linked to it for now)
- Bronchoalveolar lavage with AFB smear, PCR and culture; transbronchial or lung biopsy (`PROC.BIOPSY.LUNG`)
- Plasma microbial cell-free DNA sequencing (Karius) and a pathogen NGS test (MicroGenDX)
- Soluble IL-2 receptor (sCD25) and CXCL9
- Fungal tests: cryptococcal antigen, histoplasma antigen, aspergillus galactomannan, beta-D-glucan, Pneumocystis PCR; brucella serology; JC virus PCR
- Serum ACE; urine AFB and mycobacterial culture
- Fundoscopy for choroidal tubercles exists as `EX.EYE.FUNDOSCOPY`; no change needed

## Open questions for Atul

1. **Undated work-up.** Most of the work-up is undated in the text. Should I read Figure 5 (the timeline image) to date it, or will you set the days? Until then these results carry `day: null`, which the engine treats as valid all admission.
2. **Platelet range** is printed "139-36". Is it 139–361? It is left out of `lab_profile` for now.
3. **Units.** Values are kept in the article's US units (g/dL, 10³/µL, ng/mL). Should they be converted to the catalogue's SI units now or at the pilot review, as for the sibling cases?
4. **Day 18 CTPA and Figure 4b "day 30".** Are these one scan or two? The draft keeps both (R04 day 18, R05 day 29).
5. **Vignette.** It includes Haiti (a tuberculosis risk clue) and holds back night sweats and weight loss for the Chart. Is that the balance you want?
6. **Final diagnosis.** Is it one diagnosis (`DX.MILIARY_TB`) with HLH as a secondary finding, or both ids as now? For ICD-10, keep D76.1 (the catalogue's code) or use D76.2 (infection-associated)?
7. **Reverse causation.** The authors cannot exclude that tuberculosis reactivated under steroid and etoposide. The ground truth follows their view that it was present from the start. Agree?
8. **Scoring the harmful step.** Should steroid without anti-tuberculosis cover be a must-not-do even though the real team did it after every test was negative?
9. **L04** (sputum "MTB complex PCR") is linked to Xpert MTB/RIF. Keep it there, or wait for a generic PCR item?

## Case Reviewer checklist

- [ ] Every value in `series` and `single_results` matches Table 1 and the text
- [ ] Day mapping is correct (day 0 = hospital day 1); undated items get days
- [ ] The vignette and opening words reveal nothing diagnostic
- [ ] R01–R08 are faithful raw findings with no interpretation
- [ ] Figure captions leak nothing; figure flags set (use, mask or exclude)
- [ ] Ground truth, rubric anchors, must-do and must-not-do agreed
- [ ] Gap guidance agreed; values set for G11, G14, G15, G16, G21
