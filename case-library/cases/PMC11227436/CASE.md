# Case PMC11227436: B12 deficiency mimicking a thrombotic microangiopathy

Case id `PMC11227436` · Batch 1 (task L1.3) · Status: **draft, awaiting Case Reviewer verification** · Structured data: [`gold-case-file.draft.json`](gold-case-file.draft.json)

> Spoiler warning. This file and the JSON contain the answer. They are for the Case Reviewer and for developers, never for a player or a seat.

Drafted on 25 Sep 2026 by the Case Curator (curation steps 1–5 only). The path analysis, affected values, reports and consult notes wait for the pilot review.

## Source

Sabri S, Aqodad Z, Alaoui H, Bachir H, Hamaz S, Serraj K. *Pseudomicroangiopathic Thrombotic Syndrome: Unveiling the Vitamin B12 Deficiency Connection.* Cureus 16(6): e61787. Published 6 Jun 2024. doi:[10.7759/cureus.61787](https://doi.org/10.7759/cureus.61787) · [PMC11227436](https://pmc.ncbi.nlm.nih.gov/articles/PMC11227436/) · PMID 38975473

- **Licence:** CC BY 4.0, read from the `<license>` element of the cached JATS XML (`data/articles/PMC11227436/jats.xml`) on 25 Sep 2026. `production_ok` and `public_release_ok` are true for the article. The figures carry no separate credit line, but their own flags stay false until Atul decides (SPEC §9).
- **Attribution:** "Adapted from Sabri S et al., Cureus 16(6): e61787 (2024), CC BY 4.0. Restructured into a simulation; diagnosis hidden until the debrief; simulated findings added where marked."
- **Setting:** Oujda, Morocco (University Hospital Mohammed VI). The laboratory uses French conventions: g/dL, counts per mm³, prothrombin time as a percentage.

## The case in brief

A previously well 53-year-old woman came to the emergency department with 10 days of watery diarrhoea (no blood or mucus) and significant weight loss. She was haemodynamically stable, asthenic and visibly jaundiced, with no lymphadenopathy, organomegaly or bleeding. Bloods showed Hb 5.1 g/dL, platelets 62,000/mm³, neutrophils 1,050/mm³, MCV 113 fL and reticulocytes only 92,000/mm³. Haemolysis markers were strongly positive: haptoglobin decreased, free bilirubin 31, LDH 1,466 IU/L, schistocytes 2.3%. The DAT was IgG-positive, PT 44%, and renal function normal.

The team considered a microangiopathic haemolytic anaemia, but the normal kidneys and neurology were atypical. The PLASMIC score was 4, so they did not start plasma exchange. Vitamin B12 was 50 pg/mL. A bone marrow examination showed hypercellularity with megaloblasts. Anti-parietal cell antibodies and gastroscopy with biopsies (fundic atrophy, intestinal metaplasia) confirmed pernicious anaemia (Biermer's disease). With B12 replacement alone, the diarrhoea settled by day 4 and reticulocytes rose by day 7.

## What the players start with

> A 53-year-old woman with no significant past medical history presents to the emergency department with watery diarrhoea for 10 days and significant weight loss.

Opening words: "I've had watery diarrhoea for about ten days now, and I've lost a lot of weight."

Display title: "Diarrhoea, weight loss and a very low blood count" · slug `c-k15e5`.

## Timeline in the article

The article gives no calendar dates. Day 0 is the day she was admitted to the emergency department.

| Day | Event |
| --- | --- |
| Before 0 | 10 days of watery diarrhoea; weight loss (period not stated) |
| 0 | Admission. Examination, Table 1 bloods (count, reticulocytes, PT, renal function, haemolysis screen, schistocytes, DAT, B12) |
| Not dated | PLASMIC score 4; plasma exchange not started |
| Not dated | Bone marrow examination: megaloblastic change |
| Not dated | Anti-parietal cell antibodies; gastroscopy with fundic biopsies |
| Replacement day 0 | Vitamin B12 replacement starts (route and dose not reported) |
| Replacement day 4 | Diarrhoea resolved |
| Replacement day 7 | Reticulocyte response ("reticulocyte crisis") |

Undated tests have `day: null` and can be ordered at any point in the admission.

## Facts

| Group | Count | Notes |
| --- | --- | --- |
| History | 7 | 4 in the vignette (age and sex, complaint, weight loss, no past history); 3 chart facts |
| Examination | 6 | Stable, asthenic, jaundiced, no nodes or organomegaly, no bleeding, no neurological deficit |
| Laboratory results | 15 | All from Table 1 and the text, one time point. Renal function split into urea and creatinine ("Normal") |
| Raw material | 3 | Blood film (schistocytes only), bone marrow, gastric biopsies |
| Figures | 4 | Figure 1A, 1B (marrow); Figure 2A, 2B–C (stomach) |
| Gaps | 25 | G01–G25 |

There is no hidden history: the article gives no history that surfaced only on targeted questioning. The diagnostic skill here is in reading the laboratory pattern.

## Raw material for the Pathology Service

| Id | Test | Raw findings |
| --- | --- | --- |
| R01 | Peripheral blood film (day 0) | Schistocytes 2.3% of red cells. |
| R02 | Bone marrow (H&E as captioned) | Marked hypercellularity with increased erythroblasts. Megaloblasts with fine chromatin and prominent nucleoli. |
| R03 | Upper GI endoscopy with gastric biopsies | Atrophy of the fundic mucosa. Intestinal metaplasia. |

## Ground truth (draft)

**Final diagnosis:** pernicious anaemia (autoimmune atrophic gastritis) with severe vitamin B12 deficiency, presenting as pancytopenia with haemolysis and schistocytes that mimicked a thrombotic microangiopathy. `DX.PERNICIOUS_ANAEMIA`, ICD-10 D51.0.

- **Accepted differential:** TTP; HUS, including STEC-HUS given the diarrhoea; other MAHA; warm AIHA or Evans syndrome; folate deficiency; myelodysplasia; other causes of pancytopenia; malabsorption.
- **Red herrings:** schistocytes, thrombocytopenia with haemolysis, IgG-positive DAT, very high LDH, diarrhoea, PT 44%.
- **Key discriminators:** MCV 113 fL; low reticulocytes despite haemolysis; neutropenia too; normal kidneys and neurology; PLASMIC 4; B12 50 pg/mL; megaloblastic marrow; parietal cell antibodies; fundic atrophy.
- **Must do (text only; conditions come later):** B12 and folate before transfusion; weigh TTP risk (PLASMIC, ADAMTS13 if still possible); read low reticulocytes as ineffective erythropoiesis; parenteral B12; find the cause (antibodies, gastroscopy with biopsies); confirm the reticulocyte response.
- **Must not do:** plasma exchange without weighing B12 deficiency; steroids for AIHA on the DAT alone; folic acid alone before B12.
- Rubric anchors are left for step 6 after the pilot review.

## Catalogue items the case needs but the catalogue lacks

- A numeric schistocyte count (`L11` has no catalogue link; `FND.SCHISTOCYTES` exists only as a finding).
- Unconjugated bilirubin (`L09` has no catalogue link).
- Prothrombin activity in % (`L06` is linked to `CMP.PT`, which is in seconds).
- ADAMTS13 activity (gap G11); gastrin, pepsinogen, homocysteine, methylmalonic acid (gap G14).
- A gastric biopsy histology item (R03 is linked to `PROC.ENDO.OGD`).

## Open questions for Atul

1. **Units.** The values are kept as printed (g/dL, /mm³, pg/mL, PT %), and `lab_profile` uses the article's units. Should they be converted to the catalogue's SI units before resolution? The value rules (MCH, MCHC) assume g/L.
2. **Free bilirubin "31 mmol/L".** It is almost certainly µmol/L. I recorded µmol/L with a note.
3. **Reticulocyte "normal range >120,000/mm³"** is a regenerative threshold, not a reference interval. Keep it as printed, or replace it with the catalogue's range?
4. **Anti-parietal cell antibodies.** The article says they "confirmed" the diagnosis but does not say "positive". I recorded "Positive" as an inference (`L14`).
5. **Marrow specimen.** The caption says H&E at ×100 and ×400, which suggests a trephine or clot section. I linked it to `PROC.BM.ASPIRATE`. Should it be `PROC.BM.TREPHINE`, or both?
6. **PT 44%.** The article does not explain it (malabsorption of vitamin K?). How should the INR, APTT and fibrinogen be set (G10)?
7. **Figures.** I set `has_annotations: true` on the assumption that the panel letters are drawn in. I have not seen the images. All figure flags are false until you decide.
8. **Treatment clock.** The article dates the recovery from the start of replacement, not from admission. Should replacement start on day 0 or day 1 of the case?
9. **H07 "No bleeding"** comes from the examination. May it also answer the history question?
10. **Vignette.** Should it include the jaundice, which a referral letter might mention? I left it for the examination.

## Case Reviewer checklist

- [ ] Every value in `single_results` matches Table 1 and the text
- [ ] Units and ranges decided (questions 1–3)
- [ ] The vignette and opening words reveal nothing diagnostic
- [ ] R01–R03 are faithful raw findings with no interpretation
- [ ] Redacted figure captions leak nothing; figure flags decided
- [ ] Ground truth, differential, red herrings and discriminators agreed
- [ ] Gap guidance agreed
- [ ] Signed off: freeze as `PMC11227436@v1`
