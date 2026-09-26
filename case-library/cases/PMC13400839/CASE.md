# Case PMC13400839: folate deficiency after sleeve gastrectomy, mimicking a high-risk myelodysplastic neoplasm

Case id `PMC13400839` · Case version `PMC13400839@v1` · Status: **draft, awaiting Case Reviewer verification** · Structured data: [`gold-case-file.draft.json`](gold-case-file.draft.json), [`curation/`](curation/), [`catalogue_needs.json`](catalogue_needs.json) · Case Library task L1.3, curation steps 1–9

> Spoiler warning. This file and the JSON contain the answer. They are for the Case Reviewer and for developers, never for a player or a seat.

Educational and research use only. Nothing here is clinical advice.

## Source

Potter S, Williams M, Hanley TM. *Severe Folate Deficiency Mimicking Myelodysplastic Syndrome/Acute Myeloid Leukemia: A Case Report.* Case Reports in Hematology 2026: 8212282 (published 24 Jul 2026). doi:[10.1155/crh/8212282](https://doi.org/10.1155/crh/8212282) · [PMC13400839](https://pmc.ncbi.nlm.nih.gov/articles/PMC13400839/)

- **Licence:** CC BY 4.0, read from the JATS `<license>` element (`data/articles/PMC13400839/efetch.jats.xml`) and recorded in `cases/BATCH1.md` on 25 Sep 2026. `production_ok` and `public_release_ok` are true. No figure carries its own credit line, so the article licence covers the three figures; each media entry carries the flags as true (brief).
- **Attribution to reuse:** "Adapted from Potter S, Williams M, Hanley TM, Case Rep Hematol 2026: 8212282, CC BY 4.0. Restructured into atomic facts; diagnosis redacted from player-facing text; simulated findings added where marked."
- **Setting:** University of Utah and ARUP Laboratories, USA. The article has no tables; every value is in the text, in conventional US units. They are converted to SI in the gold file, with the printed value in each fact's `note`.

## The case in brief

A 56-year-old woman with hypothyroidism after a remote total thyroidectomy, a sleeve gastrectomy and malnutrition was transferred with severe pancytopenia, referred as possible aplastic anaemia. She had had one unit of red cells and was on cefepime, metronidazole and fluconazole for presumed colitis and mucositis. Examination was unremarkable. Hb 7.7 g/dL, Hct 22.5%, MCV 92.2 fL, platelets <6 ×10⁹/L, WBC 0.33 ×10⁹/L, neutrophils 0.06.

The film showed minimal anisopoikilocytosis, eosinophils 50% of leucocytes with atypical segmentation and rare hypogranular neutrophils; blood flow cytometry showed 1.5% myeloid blasts. The day-0 marrow was 20% cellular and erythroid-predominant, with 12% blasts (18% by flow, about 15% CD34-positive on the core), trilineage dysplasia, megaloblastic erythroid change and occasional haemophagocytosis; no ring sideroblasts. The pathologists read it as highly suspicious for MDS-IB2 (WHO 5th edition) or MDS/AML (ICC 2022).

Next day: serum folate 2.6 ng/mL (printed "pg/mL"), B12 >1500 pg/mL, iron 103 µg/dL, TIBC 159, transferrin saturation 65%, ferritin 1531 ng/mL, copper normal. Karyotype, SNP array, eosinophilia FISH, AML FISH, BCR::ABL1 FISH and a rapid AML panel were normal; the myeloid NGS panel found DNMT3A at 1.2% VAF and a KMT2A variant of uncertain significance at 49.6%. Pneumocystis pneumonia on day 3 needed intubation. With folate, the counts normalised over 18 days and a repeat marrow was 60% cellular with 1% blasts.

**Final diagnosis (ground truth):** `DX.FOLATE_DEFICIENCY_ANAEMIA`. Severe folate deficiency after sleeve gastrectomy with malnutrition, with megaloblastic trilineage dysplasia and a transient rise in blasts mimicking MDS-IB2 or MDS/AML (ICD-10 D52.8).

## What the players start with

> A 56-year-old woman is transferred from another hospital with severe pancytopenia; the referring team was concerned about aplastic anaemia. She received one unit of red cells before transfer and is on intravenous antimicrobials for presumed colitis and mucositis.

Opening words: "I've been so tired and weak for weeks, and I get out of breath just walking around the house. The other hospital said my blood counts were very low and sent me here."

Display title: "Transferred with very low blood counts" · tags: pancytopenia, neutropenia, transfer · slug `c-w4n9t`

## Timeline in the article

Day 0 is the transfer. The article gives no calendar dates (`clock.day_0` is null).

| Day | Event |
| --- | --- |
| Before 0 | Referring hospital: one unit of packed red cells; cefepime, metronidazole and fluconazole for presumed colitis and mucositis |
| 0 | Transfer. Examination unremarkable. Blood count, film, blood flow cytometry. Bone marrow aspirate, iron stain, trephine with IHC, marrow flow |
| 1 | Folate, B12, iron studies, ferritin, copper reported (placed on day 0; see decision 3) |
| Later (undated) | Karyotype, SNP array, FISH panels, rapid AML panel, myeloid NGS reported |
| 3 | Pneumocystis pneumonia diagnosed; intubated for hypoxic respiratory failure (secondary finding only) |
| 0 to 18 | Folate replacement; counts normalise |
| 18 | Repeat marrow: 60% cellular, myeloid-predominant, 1% blasts, mild dysmegakaryopoiesis (R13, `release: never`) |

## Facts

| Id | Fact | Released by |
| --- | --- | --- |
| H01 | 56-year-old woman | vignette |
| H02 | Hypothyroidism after total thyroidectomy; referring team records malnutrition | `HX.PMH.MEDICAL`, `HX.PMH.CHRONIC_CONDITIONS` |
| H03 | **Total thyroidectomy and a sleeve gastrectomy** (pivotal) | `HX.PMH.SURGICAL`, `HX.PMH.MEDICAL` (no longer hidden; see the corrections below) |
| H04 | Transfer letter: severe pancytopenia, concern for aplastic anaemia | vignette, `HX.RECORDS.REFERRAL_LETTER` |
| H05 | One unit of red cells; cefepime, metronidazole, fluconazole for presumed colitis and mucositis | `HX.PC.TREATMENT_SO_FAR`, `HX.MEDS.RECENT_ANTIBIOTICS` |
| H06 | Examination recorded as unremarkable | `EX.GEN.APPEARANCE` |
| L01–L06 | Hb 77 g/L, Hct 0.225, MCV 92.2 fL, platelets <6, WBC 0.33, neutrophils 0.06 ×10⁹/L | chart |
| L07 | **Serum folate 5.9 nmol/L** (2.6 ng/mL; limit ≥13.4 nmol/L) (pivotal) | chart |
| L08–L13 | B12 >1107 pmol/L; iron 18.4 µmol/L; TIBC 28.5 µmol/L; TSAT 65%; ferritin 1531 µg/L; copper 13.5 µmol/L | chart |
| L14 | BCR::ABL1 not detected | chart |
| D.MCHC | MCHC 342 g/L, derived from Hb and Hct | chart |

## Hidden and conditional facts

| Item | Released when |
| --- | --- |
| H03 sleeve gastrectomy | No longer hidden (corrections, 2026-09-26): the past medical or surgical history. Also reachable through `HX.PMH.ADMISSIONS` ("my stomach operation"), the port-site scars on `EX.ABD.INSPECTION`, early satiety on `HX.GI.NAUSEA_APPETITE`, and imaging or endoscopy |
| Diet (`HX.SOCIAL.DIET`, affected) | Only the diet question: small soft meals, almost no fruit or green vegetables |
| Stopped multivitamin (`HX.MEDS.SUPPLEMENTS`, `_DETAILS`, affected) | Only the supplements questions |
| Monthly B12 injections (`HX.MEDS.CURRENT`, affected) | The medicines question; explains B12 >1500 pg/mL |

## Raw material for the Pathology Service

| Id | Test | Figure | Report |
| --- | --- | --- | --- |
| R01 | Blood film | none | RP01 (`LAB.HAEM.FILM`), RP02 (`LAB.HAEM.FILM_REVIEW`) |
| R02 | Blood flow cytometry | none | RP03 |
| R03 | Marrow aspirate | Figure 1A–D (M01–M04; 1C has arrows) | RP04 |
| R04 | Marrow iron stain | none | RP05 |
| R05 | Trephine with CD34, CD61, E-cadherin IHC | Figure 2A–D (M05–M08) | RP06 |
| R06 | Marrow flow cytometry | Figure 3 (M09) | RP07 |
| R07–R12 | Karyotype, AML FISH, eosinophilia FISH, SNP array, rapid AML panel, myeloid NGS | none | RP08, RP10–RP14 |
| R13 | Follow-up marrow, day 18 | none | outcome only, `release: never` |

Captions are redacted to specimen and stain. Figure files are downloaded later (`PMC13400839/F1.jpg` to `F3.jpg`).

## Path analysis (summary)

| Path | Kind | What the case must show |
| --- | --- | --- |
| P1 Nutritional work-up | efficient | Folate 2.6 ng/mL with B12 replete; the sleeve only on the surgical history; low-folate diet and stopped multivitamin on specific questions; megaloblastic change; normal cytogenetics |
| P2 High-risk MDS or AML | trap | Blasts without aberrant phenotype; normal karyotype, SNP array and FISH; only DNMT3A 1.2% and a KMT2A VUS. Hypomethylating or induction therapy is a must-not-do |
| P3 Aplastic anaemia | trap | Hypocellular but dysplastic, left-shifted marrow with blasts, not aplasia; no PNH clone, hepatitis or drug. ATG with ciclosporin is a must-not-do |
| P4 Myeloid neoplasm with eosinophilia | alternative | Relative eosinophilia only (absolute 0.17); eosinophilia FISH negative |
| P5 Infection in neutropenia | alternative | Cultures negative; CRP 46; lymphocytes 0.09; faint ground-glass on CT chest only |
| P6 Malabsorption after bariatric surgery | alternative | B12 replete on injections; copper normal; zinc and vitamin D low; albumin 28; TSH normal; sleeve anatomy on imaging and OGD |
| P7 HLH | alternative | No organomegaly, triglycerides normal, fibrinogen not low, no acute EBV or CMV |
| P8 Autoimmune cytopenia | alternative | Rheumatological tests unrevealing (article); DAT negative |

Every item on a path resolves from an article fact, an `affected` row or an authored report. The full lists are in `curation/paths.json`.

## Ground truth and scoring (summary)

- **Rubric:** 5 = `DX.FOLATE_DEFICIENCY_ANAEMIA` with H03, RP17, RP19, CN03, CN04, CN05, CN07, CN08 or CN11 cited as evidence; 4 = `DX.FOLATE_DEFICIENCY_ANAEMIA`; 3 = `DX.MEGALOBLASTIC_ANAEMIA`, `DX.MIXED_NUTRITIONAL_ANAEMIA` or `DX.B12_DEFICIENCY_ANAEMIA`; 2 = `DX.MDS_EXCESS_BLASTS`, `DX.MDS`, `DX.AML` or `DX.APLASTIC_ANAEMIA`; 1 otherwise.
- **Must-do (7):** folate and B12 ordered; surgical, diet or supplement history asked; `RX.VITAMIN.FOLATE` with B12 ordered; cytogenetics or NGS ordered; empirical antibiotics plus platelet transfusion planned; `ACT.REPEAT_BONE_MARROW` or `ACT.REPEAT_BLOODS`; dietetics referral or dietary advice.
- **Must-not-do (4):** `RX.CHEMO.*`; an MDS or AML diagnosis without folate and B12 ordered; `RX.IMMUNO.ATG_CICLOSPORIN`; folate without B12 ordered.

## Curator's decisions

Atul delegated the open questions to the curator (brief, 25 Sep 2026). Each decision below stays open for his case review (L1.4).

1. **Folate units.** The article prints "2.6 pg/mL (normal ≥5.9 pg/mL)". A serum folate in pg/mL would be a thousand times too low; ng/mL is meant. Converted to 5.9 nmol/L (limit 13.4 nmol/L), with the printed text in the note.
2. **Platelet units.** "< 6 k/L" is read as <6 ×10⁹/L (k/µL), a misprint.
3. **Day of the haematinics.** Folate, B12, iron studies and copper were reported one day after the marrow. They are placed on day 0 as bloods sent at transfer, with the catalogue turnaround applying in play (as PMC12007988 Q3). The case therefore runs on day 0 only.
4. **Trephine cellularity.** The text calls the core "normocellular", but the opening sentence and the Figure 2 caption both give 20%. The report uses 20% (hypocellular for age).
5. **BCR::ABL1.** Tested by FISH in the article; recorded as an article fact on the catalogue's BCR-ABL1 test (`CMP.BCR_ABL`), since no FISH item exists.
6. **The KMT2A variant** is printed as "Tier 2 variant of unknown clinical significance", which mixes two tiers. The NGS report keeps both words and notes that a VAF near 50% may be constitutional.
7. **Hidden history.** The article lists the sleeve gastrectomy in the past history. To make the nutritional history matter, the transfer letter and the medical history mention hypothyroidism and malnutrition but not the sleeve, which is released by the surgical history (and fairly by admissions, scars, early satiety and imaging).
8. **B12 injections and a stopped multivitamin (judgement calls).** The article gives no medicines or supplements. B12 >1500 pg/mL with severe folate depletion is best explained by routine post-bariatric B12 injections, with the recommended multivitamin stopped (the article cites inadequate supplementation as a cause). Levothyroxine 100 µg is assumed after total thyroidectomy.
9. **Symptoms (judgement calls).** The article gives no symptom history. Six weeks of tiredness, two to three weeks of exertional breathlessness, loose stools and a sore mouth in the week before transfer (matching the presumed colitis and mucositis), weight loss of about 8 kg.
10. **Examination (judgement calls).** "Unremarkable" is respected: no purpura despite platelets <6, no organomegaly or nodes; mild pallor only; a smooth, slightly red tongue; port-site and thyroidectomy scars recorded because an examiner would note them. Vitals: 37.4 °C, pulse 102, BP 112/68, RR 18, SpO₂ 96% on air.
11. **Pneumocystis pneumonia** (day 3) is a secondary finding, not scored. On day 0 the chest film is clear and CT chest shows faint bilateral upper-lobe ground-glass (judgement call); lymphocytes 0.09, CD4 38 ×10⁶/L, IGRA indeterminate. The infectious diseases note flags the lymphopenia and Pneumocystis risk without predicting the pneumonia.
12. **Blood count details.** RBC 2.44 ×10¹²/L from Hct/MCV; differential sums to WBC 0.33 (eosinophils 0.17, lymphocytes 0.09, monocytes 0.01, basophils 0.00); reticulocytes 12 ×10⁹/L (0.49%); RDW 15.6% (judgement call: megaloblastic change and a transfused population, but minimal anisopoikilocytosis on the film).
13. **Other values** follow malnutrition and ineffective erythropoiesis: LDH 742 U/L and haptoglobin 0.18 g/L (judgement calls), bilirubin 24 µmol/L, albumin 28 g/L, zinc and vitamin D low, PTH raised, INR 1.3 with factor VII 46, homocysteine 41.6 µmol/L, MMA 0.21 µmol/L, red cell folate 262 nmol/L, TSH 2.6 (judgement call).
14. **PNH flow:** granulocyte and monocyte clones "not assessable" at these counts (judgement calls).
15. **Blood group:** O RhD positive (the commonest groups); antibody screen negative.
16. **No reviewer placeholders.** Nothing in this case needed a value Claude must not guess.
17. **Film report variants.** The article gives one film description, so `LAB.HAEM.FILM` has one final report; the film review adds the standard comment suggesting B12, folate, copper and a marrow, naming tests only.
18. **The marrow report keeps the article's reading** ("highly suspicious for a myelodysplastic neoplasm with increased blasts") because that is the case's trap; the haematology consult notes, from variant 2 on, point to reversible causes.

## Catalogue needs (`catalogue_needs.json`)

| Kind | New items |
| --- | --- |
| Tests (7) | `LAB.CHEM.RBC_FOLATE`, `LAB.CHEM.HOMOCYSTEINE`, `LAB.CHEM.MMA`, `LAB.CYTOGEN.FISH_AML`, `LAB.CYTOGEN.FISH_EOSINOPHILIA`, `LAB.CYTOGEN.SNP_ARRAY`, `LAB.MOL.AML_TARGETED_PANEL` (prices estimated) |
| Components (7) | `CMP.RBC_FOLATE`, `CMP.HOMOCYSTEINE`, `CMP.MMA`, and the four report components of the new interpretive tests |
| Actions (4) | `RX.CHEMO.HYPOMETHYLATING`, `RX.CHEMO.AML_INDUCTION`, `RX.IMMUNO.ATG_CICLOSPORIN`, `ACT.REPEAT_BONE_MARROW` |
| Findings (3) | `FND.INCREASED_BLASTS`, `FND.HAEMOPHAGOCYTOSIS`, `FND.EOSINOPHILIA` (their `shown_by` is under `_csv_extras`) |

Existing items reused instead of the shortlist's suggestions: `HX.PMH.SURGICAL` (not `HX.PSH.BARIATRIC`), `HX.SOCIAL.DIET`, `RX.VITAMIN.FOLATE`, `DX.FOLATE_DEFICIENCY_ANAEMIA`, `DX.MDS_EXCESS_BLASTS`, `DX.AML`, `REF.DIETETICS`. Marrow IHC is part of the trephine report rather than a separate test.

## Counts

- Facts: article 20 (6 history and examination, 14 laboratory), derived 1 (MCHC).
- Ledger (replay, 25 Sep 2026): affected 208 (206 written, plus MCH and the anion gap calculated from affected inputs), normal 336, rule 1 (PSA), reviewer 0. Judgement calls 30.
- Reports 20 (all final; none provisional). Consult notes 22: 11 authored (haematology 3 variants, dietetics 2, one each for infectious diseases, gastroenterology, general surgery, oncology, rheumatology, endocrinology) and 11 generic `rule` notes.
- Test utility: 76 tests on the paths.
- Replay: `uv run python -m scripts.case_replay cases/PMC13400839` prints `0 open problem(s)`.

## Case Reviewer checklist

- [ ] Every article value against the text, including the unit conversions (decisions 1 and 2) and the day placement (decision 3).
- [ ] Trephine cellularity (decision 4) and the KMT2A wording (decision 6).
- [ ] The hidden-history design: the sleeve released only by the surgical history and its fair clues (decision 7).
- [ ] The judgement calls, most important first: diet (`HX.SOCIAL.DIET`), supplements and B12 injections (`HX.MEDS.*`), vitals, pallor and oral findings, CT chest ground-glass, LDH, RDW, haptoglobin, TSH.
- [ ] The consult notes: haematology V2 (after the marrow) and V3 (after the folate) carry the teaching; check that none is more diagnostic than a competent colleague.
- [ ] The rubric and conditions, especially must-do 5 (platelets plus antibiotics) and must-not-do 4 (folate without B12).
- [ ] The new catalogue items and their estimated prices.
- [ ] Figures: download F1 to F3 and confirm `has_annotations` (only Figure 1C mentions arrows).

## Figure check (2026-09-26)

The images were downloaded from PMC and looked at one by one.

- M09 (Figure 3, flow cytometry): `has_annotations` set to true (gate names and axes). It shows "Blasts 1: 25.77%", which supports the myeloid-neoplasm trap, not the diagnosis.

## Corrections after the second review (2026-09-26)

Batch 1 was approved in bulk; a second expert review found the problems below. Each change is for Atul to check before the patch is applied. Ids are unchanged; no ledger row or day is dropped.

1. **The sleeve gastrectomy is no longer hidden (finding 1, MEDIUM).** Decision 7 hid H03 behind the surgical history, yet the case releases the operation through many other routes: the consult notes on any request (dietetics CN04, gastroenterology CN07, general surgery CN08, endocrinology CN11), CT abdomen RP17, OGD RP19, the staple line and clips on imaging, and the patient's own words for admissions, diet and supplements ("my stomach operation"). That is realistic: a patient names the operation and imaging shows it, and consultants who see her would learn of it. Gating the consults on H03 would have been artificial and would still leave the patient's words and imaging, so the coherent fix is to stop treating the surgery as hidden. The teaching point moves from finding the operation to connecting it with the marrow; must-do 2 (surgical, diet or supplement history) still scores the history taking.
   - `gold-case-file.draft.json`, fact H03: `item` "Previous operations (hidden until the surgical history is taken)" -> "Previous operations"; `release_condition` (`requires_topics` and its note) removed; `released_by` [`HX.PMH.SURGICAL`] -> [`HX.PMH.SURGICAL`, `HX.PMH.MEDICAL`], because the article lists the sleeve in the past history and a patient asked for her medical history would mention it. Release still `chart`; `pivotal` kept.
   - Adding the admissions, diet and supplement questions to `released_by` was tried and rejected: those items already have `affected` ledger rows for all days, and the consistency check reports a fact released by the same item and day as a contradiction. Their answers keep naming the operation.
   - `curation/ground_truth.json`, rubric score 5: `evidence_has` [H03] -> `any` of `evidence_has` H03, RP17 (CT abdomen), RP19 (OGD), CN03 (haematology after the folate), CN04 and CN05 (dietetics), CN07 (gastroenterology), CN08 (general surgery), CN11 (endocrinology): every stable id through which the operation is actually learned, in the `any` form PMC11890614 already uses. The anchor text is unchanged.
   - `curation/paths.json`, P1 rationale: "the sleeve gastrectomy only on the surgical history" -> "on the past medical or surgical history (and in the patient's words on admissions, diet and supplements, and on abdominal imaging or endoscopy)".
   - Not resolved: the admissions, diet and supplement answers and the imaging rows that mention the sleeve (plain abdomen, CT urinary tract, whole-body CT, PET-CT) are ledger rows, which have no stable id to cite. A player who learned of the operation only there can still cite H03 after the medical or surgical history, which a competent work-up takes.
2. **Prothrombin activity follows the INR (finding 2, HIGH, batch-wide).** The normal generator gave `CMP.PT_ACTIVITY` 97% on day 0 while the affected INR is 1.3 (all days) with factor VII 46%. New `affected` row in `curation/affected.json`: `CMP.PT_ACTIVITY`, day 0 (the only day with a value), 97% (normal) -> 66% (70-120, flag L), gap G11, by the Case Library's common curve: activity % = round(100 x 0.59 / (INR - 1 + 0.59)), capped at 100 (0.59 calibrated to an article pair of 44% at INR 1.75). Not a judgement call; confidence 0.7.

Replay after the corrections: `0 open problem(s)`; ledger affected 212, normal 394, rule 2.
