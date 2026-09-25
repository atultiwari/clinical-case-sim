# Case PMC11227436: B12 deficiency mimicking a thrombotic microangiopathy

> **Spoiler warning.** This file, the gold case file, `curation/` and `catalogue_needs.json` contain the answer. They are for the Case Reviewer and for developers, never for a player or a seat.

Case id `PMC11227436` · version `PMC11227436@v1` · Batch 1 (task L1.3) · Sambhasha starter case · Status: **draft; curation steps 1-9 prepared locally, awaiting the Case Reviewer**

Structured data: [`gold-case-file.draft.json`](gold-case-file.draft.json) · [`curation/`](curation/) · [`catalogue_needs.json`](catalogue_needs.json)

Steps 1-5 were drafted earlier on 25 Sep 2026. On the same day the Case Curator converted the case to SI units, applied the decisions in [`../BATCH1-CURATOR-ANSWERS.md`](../BATCH1-CURATOR-ANSWERS.md), decided the open questions (Atul delegated them) and wrote steps 6-9. Nothing has been written to the Case Vault. The local replay (`uv run python -m scripts.case_replay cases/PMC11227436`) reports **0 open problems**.

## Source

Sabri S, Aqodad Z, Alaoui H, Bachir H, Hamaz S, Serraj K. *Pseudomicroangiopathic Thrombotic Syndrome: Unveiling the Vitamin B12 Deficiency Connection.* Cureus 16(6): e61787. Published 6 Jun 2024. doi:[10.7759/cureus.61787](https://doi.org/10.7759/cureus.61787) · [PMC11227436](https://pmc.ncbi.nlm.nih.gov/articles/PMC11227436/) · PMID 38975473

- **Licence:** CC BY 4.0, read from the `<license>` element of the cached JATS XML (`data/articles/PMC11227436/jats.xml`). `production_ok` and `public_release_ok` are true for the article and for both figures (the brief's rule for batch 1).
- **Attribution:** "Adapted from Sabri S et al., Cureus 16(6): e61787 (2024), CC BY 4.0. Restructured into a simulation; diagnosis hidden until the debrief; simulated findings added where marked."
- **Setting:** Oujda, Morocco. The laboratory printed French conventions (g/dL, counts per mm³, prothrombin time as a percentage); every value is now in the catalogue's SI unit with the printed value in the fact's `note`.

## The case in brief

A previously well 53-year-old woman came to the emergency department with 10 days of watery diarrhoea (no blood or mucus) and significant weight loss. She was haemodynamically stable, asthenic and visibly jaundiced, with no lymphadenopathy, organomegaly, bleeding or neurological deficit. Bloods: Hb 51 g/L, platelets 62 x10^9/L, neutrophils 1.05 x10^9/L, MCV 113 fL, reticulocytes only 92 x10^9/L; haptoglobin decreased, unconjugated bilirubin 31 µmol/L, LDH 1,466 U/L, schistocytes 2.3%; IgG-positive DAT; prothrombin activity 44%; renal function normal.

The team considered a microangiopathic haemolytic anaemia, but the normal kidneys and neurology were atypical. The PLASMIC score was 4, so no plasma exchange. Vitamin B12 was 37 pmol/L (50 pg/mL). The marrow was hypercellular and megaloblastic. Parietal cell antibodies and gastroscopy with biopsies (fundic atrophy, intestinal metaplasia) confirmed pernicious anaemia. With B12 alone the diarrhoea settled by day 4 and reticulocytes rose by day 7 of replacement.

## What the players start with

> A 53-year-old woman with no significant past medical history presents to the emergency department with watery diarrhoea for 10 days and significant weight loss.

Opening words: "I've had watery diarrhoea for about ten days now, and I've lost a lot of weight."

Display title: "Diarrhoea, weight loss and a very low blood count" · tags haematology, gastroenterology, internal medicine · slug `c-k15e5`.

## Timeline

No calendar dates. Day 0 is admission. Replacement starts on day 1 (decision Q8).

| Day | Event |
| --- | --- |
| Before 0 | Weeks of tiredness (affected); 10 days of watery diarrhoea; weight loss |
| 0 | Admission; examination; Table 1 bloods |
| Undated (null) | Anti-parietal cell antibodies (L14); bone marrow (R02); gastroscopy with biopsies (R03) |
| 1 | Vitamin B12 replacement starts (route and dose not reported) |
| 4 | Diarrhoea resolved (outcome) |
| 7 | Reticulocyte response (outcome) |

The playable case runs for day 0 only; the response is in the ground truth's `outcome`, not a result.

## Facts (all origin `article`)

| Group | Count | Notes |
| --- | --- | --- |
| History | 7 | H01-H04 in the vignette; H05-H07 on questioning. H03 is released by the associated-symptoms question only; the fever/sweats/weight question gets an affected answer carrying the amount |
| Examination | 6 | E01 ("haemodynamically stable") is `release: never` and releases nothing; the vital signs, pulse and postural BP rows carry it as numbers |
| Laboratory | 14 | L01-L14 in SI. L07 ("renal function normal") is `release: never`; urea, creatinine and electrolytes are affected numbers within range |
| Raw material | 3 | R01 film (schistocytes), R02 marrow section (trephine), R03 gastric biopsies |
| Figures | 2 | M01 Figure 1 (marrow, A-B); M02 Figure 2 (stomach, A-C); `has_annotations` false from the captions |
| Gaps | 25 | G01-G25, all resolved by the rows below |

Unit conversions (printed value kept in each `note`): Hb 5.1 g/dL → 51 g/L; platelets 62,000/mm³ → 62 x10^9/L; neutrophils 1,050/mm³ → 1.05 x10^9/L; reticulocytes 92,000/mm³ → 92 x10^9/L; haptoglobin range 30-200 mg/dL → 0.3-2.0 g/L; free bilirubin "31 mmol/L" → 31 µmol/L (misprint); B12 50 pg/mL → 37 pmol/L (range 200-900 → 148-664). The `lab_profile` holds the article's ranges in SI.

## Hidden facts

There is no hidden history: nothing in the article surfaced only on targeted questioning. The skill is in reading the laboratory pattern: a macrocytic pancytopenia whose reticulocyte count is far too low for the haemolysis.

## Ground truth

**Final diagnosis:** pernicious anaemia (autoimmune atrophic gastritis) with severe vitamin B12 deficiency, presenting as a pseudo-thrombotic microangiopathy. `DX.PERNICIOUS_ANAEMIA`, ICD-10 D51.0.

- **Rubric:** 5 `DX.PERNICIOUS_ANAEMIA`; 4 `DX.B12_DEFICIENCY_ANAEMIA` (cause not established); 3 megaloblastic, folate or mixed nutritional anaemia; 2 TTP, HUS, aHUS, other MAHA, warm AIHA, MDS, aplastic anaemia or unexplained pancytopenia; 1 anything else.
- **Must do (with conditions):** B12 and folate (`ordered_all`); weigh TTP before plasma exchange (film or schistocyte count, a coagulation test and renal function); reticulocyte count; B12 replacement in the plan; the cause (IF/GPC antibodies and OGD or gastric biopsy); plan repeat bloods.
- **Must not do:** plasma exchange; steroids or rituximab; folic acid without B12; platelet transfusion.
- Leak terms include the synonyms, "B12 deficiency", "pseudo-TMA", "megaloblastic anaemia", "autoimmune gastritis" and "atrophic gastritis". The leak scan is clean.

## Path analysis (`curation/paths.json`)

| Path | Kind | What the case must show |
| --- | --- | --- |
| P1 Efficient | efficient | Macrocytic pancytopenia with a low reticulocyte count; B12 37 pmol/L; parietal cell antibodies; fundic atrophy on biopsy |
| P2 TTP | trap | Normal kidneys, no fever, no neurological or cardiac involvement, high MCV (PLASMIC 4), ADAMTS13 62% |
| P3 STEC-HUS | trap | Painless, non-bloody diarrhoea; no food source or contacts; normal urine output, creatinine and urinalysis; stool culture and Shiga toxin PCR negative |
| P4 Warm AIHA or Evans | trap | Reticulocytes too low for immune haemolysis; no spherocytes; C3d negative; weak panreactive eluate |
| P5 Marrow failure or MDS | alternative | Hypercellular megaloblastic marrow; normal karyotype, FISH and flow; negative viral screen |
| P6 Malabsorption | alternative | Normal coeliac serology, calprotectin, elastase and colonoscopy; gastrin high and pepsinogen I low point to the stomach |
| P7 Coagulopathy | alternative | Normal APTT, fibrinogen and D-dimer; mixing corrects; factor VII low, factor V normal; normal liver on ultrasound |

## Rows written (local replay)

- **Ledger:** affected 179 (judgement calls 10), reviewer 0, normal 370, rule 1 (PSA "Not applicable").
- **Reports:** 12, all `only` and final (the article describes no revised report). The film and the film review, marrow aspirate and trephine, iron stain, flow, karyotype, FISH, OGD, gastric biopsy, ultrasound and colonoscopy.
- **Consult notes:** 22. Affected 9: haematology (3 variants: none, after the B12 result `L13`, after the biopsy finding), gastroenterology (2: none, after `L13`), nephrology, neurology, infectious diseases, dietetics. Rule 13 for the referrals off the paths.
- **Lay text:** H02-H07; every affected history row carries its own `lay_text`.
- **Test utility:** 76 (essential 10, supportive 27, low-yield 30, unnecessary 9).
- A few off-path rows are affected because a neutral template or normal draw would contradict this patient: syncope, impact, exercise, OTC medicines, thirst, skin colour, hands and nails, lipids (the generator's independent draws broke the non-HDL formula), ABG (bicarbonate 21), factors II and X (PT activity 44%).

## Curator's decisions

Atul delegated the open questions. Method decisions come from `BATCH1-CURATOR-ANSWERS.md`; the "Proposed" items and new questions are decided here.

| # | Question | Decision |
| --- | --- | --- |
| Q1 | Units | SI at extraction; printed value in `note`; `lab_profile` in SI (method) |
| Q2 | Free bilirubin "31 mmol/L" | µmol/L with a note (method) |
| Q3 | Reticulocyte "normal range >120,000/mm³" | Catalogue range 50-100 x10^9/L shown; printed threshold in the note (method). 92 is therefore unflagged, which is realistic: the point is that it is too low for Hb 51 |
| Q4 | Anti-parietal cell antibodies "confirmed" | "Positive" kept as an article fact (the article's wording allows no other reading), noted as an inference and listed below as a judgement call |
| Q5 | Marrow specimen | Both. R02 (H&E section) is linked to `PROC.BM.TREPHINE`; the aspirate report RP03 is written from the same findings |
| Q6 | PT 44% (G10) | Modelled as vitamin K deficiency from poor intake and diarrhoea: PT 20.8 s, INR 1.75, APTT 34.0 s, fibrinogen 3.1 g/L, D-dimer 0.42, mixing corrects, factor VII 38, factors II 58 and X 55, factor V 92. INR 1.75 keeps the PLASMIC score at 4, as the article reports |
| Q7 | Figures | Two media entries, one per figure file, flags true (brief); `has_annotations` false because the captions mention only panel letters. To check when the files are downloaded |
| Q8 | Treatment clock | Replacement starts on day 1 (method); the case plays day 0 only |
| Q9 | H07 as a history answer | Yes: H07 answers `HX.GEN.BRUISING_BLEEDING` |
| Q10 | Jaundice in the vignette | No; it stays an examination finding (E03) with a history answer (`HX.GEN.JAUNDICE`) |
| New | Catalogue gaps (schistocytes, unconjugated bilirubin, PT %, ADAMTS13, gastrin, pepsinogen, homocysteine, MMA, gastric histology) | Proposed as new items in `catalogue_needs.json`; the facts link to them |
| New | E01 "haemodynamically stable" | `release: never`; the vital signs row gives numbers consistent with it (the contradiction check forbids a fact and a ledger row on the same item) |
| New | L07 "renal function normal" | `release: never`; numbers as affected rows within range (a text "Normal" in a urea result would give its origin away) |
| New | Stool Shiga toxin | Added `LAB.MICRO.STEC_PCR` so the HUS trap can be tested properly |

### Judgement calls (affected rows with `judgement_call: true`), most important first

1. **CMP.ANTI_IF** not detected (alternative: positive). Why it matters: a positive result would make the cause obvious without the gastroscopy; the article relied on parietal cell antibodies and histology.
2. **CMP.PT / G10**: vitamin K deficiency pattern for PT 44% (alternative: mild hepatic synthetic impairment). Changes the coagulopathy path (P7).
3. **CMP.ADAMTS13_ACT** 62% (alternative: mildly reduced, 30-50%). Either way not below 10%; decides the TTP trap if a player sends it.
4. **EX.GEN.VITALS**: afebrile, pulse 106, BP 112/68 (article: "stable haemodynamics"). No fever matters for the TTP trap.
5. **CMP.ELUATE** weakly panreactive IgG (alternative: no antibody detected). Supports the authors' dysimmune reading; strengthens the AIHA trap a little.
6. **EX.ORAL.CAVITY** normal tongue with pale mucosa (alternative: smooth red tongue). Glossitis would add a clue the article does not report.
7. **HX.GEN.FEVER_SWEATS_WEIGHT**: about 7 kg over 2-3 months (G02).
8. **HX.PC.PROGRESSION**: tiredness for several weeks before the diarrhoea; 4-6 stools a day.
9. **HX.FAMILY.AUTOIMMUNE** none known; **CMP.ANTI_TPO** 18 IU/mL (alternatives: a relative with thyroid disease; raised anti-TPO).
10. Not flagged in the ledger but judgement calls all the same: L14 "Positive" (Q4); the OGD appearance (RP09: pale, thin body mucosa; it could look normal); group O RhD positive (arbitrary; nothing depends on it).

### Reviewer-set values

None. No value here must not be guessed, so there are no `reviewer` rows.

## Catalogue needs (`catalogue_needs.json`)

| Kind | New | Ids |
| --- | --- | --- |
| Tests | 10 | `LAB.HAEM.PT_PERCENT`, `LAB.CHEM.BILI_FRACTIONS`, `LAB.HAEM.SCHISTOCYTE_COUNT`, `LAB.HAEM.ADAMTS13`, `LAB.CHEM.GASTRIN`, `LAB.CHEM.PEPSINOGEN`, `LAB.CHEM.HOMOCYSTEINE`, `LAB.CHEM.MMA`, `PROC.BIOPSY.GASTRIC`, `LAB.MICRO.STEC_PCR` (prices `estimate`) |
| Components | 11 | `CMP.PT_ACTIVITY`, `CMP.BILI_UNCONJ`, `CMP.SCHISTOCYTE_PCT`, `CMP.ADAMTS13_ACT`, `CMP.GASTRIN`, `CMP.PEPSINOGEN_I`, `CMP.PEPSINOGEN_RATIO`, `CMP.HOMOCYSTEINE`, `CMP.MMA`, `CMP.GASTRIC_BIOPSY_REPORT`, `CMP.STEC_PCR` |
| Findings | 2 | `FND.GASTRIC_FUNDIC_ATROPHY`, `FND.INTESTINAL_METAPLASIA` |
| Value rules | 1 | `R.BILI_UNCONJ` (unconjugated = total - conjugated, 10%) |
| Diagnoses, history, exam, referrals, templates | 0 | Existing ids suffice |

The rows pass the catalogue checker when appended to a copy of the CSVs. PMC12007988 (also B12) may propose some of the same items; the lead curator de-duplicates.

## Case Reviewer checklist

- [ ] Every value in `single_results` matches Table 1 and the text after conversion (see the notes)
- [ ] The vignette, opening words, title and tags reveal nothing diagnostic
- [ ] R01-R03 are faithful raw findings; figure captions leak nothing; figure flags and `has_annotations` confirmed when the files are downloaded
- [ ] The ten judgement calls above
- [ ] Reports RP01-RP12, especially the OGD appearance (RP09) and the gastric biopsy (RP10)
- [ ] Consult notes CN01-CN09 are helpful but no more diagnostic than a competent colleague
- [ ] Ground truth, rubric, must-do and must-not-do conditions agreed
- [ ] New catalogue items agreed (with the lead curator's merge)
- [ ] Signed off: freeze as `PMC11227436@v1`
