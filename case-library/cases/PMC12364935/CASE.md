# PMC12364935: the curator's case file

Task L1.3 · Case Library · batch 1, case 5 · 25 Sep 2026 · Claude (Case Curator)

> **Spoiler warning.** This file and every JSON file in this folder name the diagnosis. They are for the Case Reviewer (Dr Atul Tiwari) and for developers, never for a player or a seat. Educational and research use only; nothing here is clinical advice.

## Source

- Sheng L-P, Lin B-Z, Han L-N, Wang G-Q, Hou F-Q. *Case Report: Visceral leishmaniasis misdiagnosed as systemic lupus erythematosus in a 36-year-old migrant worker.* Front Med 12: 1614790 (published 6 Aug 2025). doi:10.3389/fmed.2025.1614790; PMID 40842548.
- Department of Infectious Diseases, Peking University International Hospital, Beijing.
- Licence CC BY 4.0 (JATS `<license>`, recorded in `../BATCH1.md`): `production_ok` true, `public_release_ok` true. Three figures, all with annotations (measurement lines, arrows, Ct labels) and no separate credit line. JATS SHA-256 `fee44983…8239df` (full hash in the gold file).
- Case version `PMC12364935@v1`, slug `c-4bz2k`, display title "Nine months of fever despite treatment", tags fever, pancytopenia, splenomegaly.

## The case in brief

A 36-year-old migrant worker who lives and works in Zhongshan, Guangdong (where the disease is rare), has nine months of fever, fatigue, joint swelling and weight loss. A local hospital finds pancytopenia, ANA 1:320, anti-M2 antibodies, IgG 53 g/L and hepatosplenomegaly; its marrow shows erythroid hyperplasia and no parasites. A rheumatology department adds anti-dsDNA, anti-PM-Scl, a positive DAT and low C3 and C4, measures the spleen at 25 cm, repeats the marrow (nothing diagnostic) and diagnoses SLE. High-dose steroids, cyclosporine, hydroxychloroquine, tofacitinib and telitacicept fail. Ten days after she stops prednisone 20 mg and cyclosporine herself, high spiking fevers return and she comes to the authors' infectious diseases department. A targeted history finds that her home town is in Shanxi Province, an endemic area she travels to regularly. The bone marrow aspirate shows Leishmania amastigotes, confirmed by China CDC and by PCR (Ct 32.5). Liposomal amphotericin B (1.3 mg/kg daily, extended to 30 days) ends the fever within 48 hours; the counts recover and the spleen shrinks from 25.9 to 16.6 cm by four months.

**Final diagnosis:** visceral leishmaniasis (kala-azar, `DX.KALA_AZAR`, B55.0) from her endemic home province, misdiagnosed as SLE.

## Timeline (case days)

| Day | Event | Source |
| --- | --- | --- |
| about -270 | Onset of fever, fatigue, joint swelling, weight loss | Text (nine months) |
| -200 | Local hospital, Zhongshan: Hb 91, WBC 2.0, platelets 73; ANA 1:320, AMA-M2; IgG 53 g/L; marrow without parasites; CT hepatosplenomegaly | Text; day placed by the curator |
| -120 | Rheumatology admission, day 1 (Table 1 column 1) | Table 1; day placed by the curator |
| -75 | Rheumatology admission, day 45 (Table 1 column 2) | Table 1; day placed by the curator |
| -10 | She stops prednisone (20 mg) and cyclosporine herself | Text |
| 0 | Admission to the authors' department (Table 1 "This hospital, Day 1"); marrow aspirate and PCR placed here | Table 1, text |
| 1-30 | Liposomal amphotericin B; fever gone within 48 h | Outcome only (O03) |
| 30 | Table 1 "Day 30" | Outcome only (O01) |
| discharge + 21 | Counts normal | Outcome only (O02) |
| about +120 | CT: spleen 16.6 cm | Outcome only (O05) |

The engine's clock runs for day 0 only: every post-treatment value is an outcome fact (`release: never`, no catalogue link), as in PMC11227049.

## Facts

- **History (15, day 0):** H01 age and sex; H02 presenting complaint; H03 fever to 40 °C, fatigue, weight loss; H04 course, including the relapse after stopping her drugs; H05 joint swelling; H06 untreated asthma; H07 no animal contact; H08 no febrile contacts; H09 migrant worker in Zhongshan with her husband; H10 husband well, no family history of recurrent infection; **H11 home town in Shanxi, regular travel (pivotal, hidden)**; H12 and H13 the two earlier hospitals' records; H14 the SLE treatment; H15 the drugs she stopped.
- **Laboratory (35 series, 82 points, days -200 to 0):** full blood count, CRP, ESR, ferritin, LDH, AST, ALT, albumin, creatinine, D-dimer, ANA, RF, anti-Sm, anti-dsDNA, lupus anticoagulant, DAT, AMA-M2, C3, C4, IgG, hepatitis B and C, CMV, EBV, HIV, anti-PM-Scl, serum and urine immunofixation, and the Leishmania PCR. All converted to SI; printed values and units in each series' `note`. Three MCHC values are derived.
- **Outcomes (5, release never):** day 30 and post-discharge results, the treatment response, the post-treatment marrow and PCR, the four-month CT.
- **Raw material (6):** R01 the diagnostic marrow aspirate, R02 the PCR plot, R03 the admission CT; R04 to R06 the follow-up CT, marrow and PCR (release never).
- **Media (7 entries from 3 figures):** `PMC12364935/F1.jpg` (CT before and after), `F2.jpg` (marrow at 400x and 1000x, and after treatment), `F3.jpg` (PCR plots). Captions are redacted; all flags true; `has_annotations` true. The files are downloaded later.

## Hidden facts

| Fact | Released by | Condition |
| --- | --- | --- |
| H11 home town in Shanxi; regular travel between Shanxi and Zhongshan (pivotal; rubric anchor 5 needs it as evidence) | `HX.SOCIAL.TRAVEL`, `HX.SOCIAL.RESIDENCE` (new) | A residence, native-place or travel question. The vignette gives only her place of work |
| Marrow amastigotes (R01 → RP01, `FND.LD_BODIES`) | `PROC.BM.ASPIRATE` | Ordering a repeat marrow despite two earlier "negative" marrows (H12, H13) |
| Leishmania PCR positive (S35) | `LAB.MOL.LEISHMANIA_PCR` (new) | Ordering it |

## Path analysis (9 paths; `curation/paths.json`)

| Path | Kind | What the case shows |
| --- | --- | --- |
| P1 Residence history and marrow parasitology | efficient | H11 on a targeted question; amastigotes on the aspirate; rK39 positive; PCR positive; HIV negative; splenic aspirate risky at platelets 29 |
| P2 Refractory SLE | trap | anti-dsDNA now negative, anti-Sm negative, no rash, serositis or nephritis, low reticulocytes, mild haemolysis only; escalation is a must-not-do |
| P3 HLH | trap | ferritin 1,007 and EBV DNA tempt it; triglycerides 2.4, fibrinogen 2.2 and sCD25 1,850 stay below HLH-2004 thresholds |
| P4 Lymphoma or MPN | alternative | no lymphadenopathy; polyclonal proteins; reactive marrow; BCR-ABL1 and JAK2 negative; PET diffuse only |
| P5 Other chronic febrile infections | alternative | cultures, TB tests, brucella, malaria, typhoid, HIV negative; EBV DNA is reactivation only |
| P6 Chronic liver disease | alternative | normal ALP and enzymes despite anti-M2; normal portal flow; no varices; no cirrhosis |
| P7 Drug effects and steroid withdrawal | alternative | low 8 am cortisol (a real issue to cover), but no explanation for the spleen |
| P8 Asthma | alternative | mild, untreated; clear chest |
| P9 Haematinic deficiency | alternative | anaemia of inflammation; normal B12 and folate; marrow iron increased |

Consultants: infectious diseases (3 variants: none, after H11, after the marrow finding), haematology (2), rheumatology (2), gastroenterology, endocrinology, respiratory, oncology, general surgery (declines splenectomy) and dietetics; the other 10 specialties get the catalogue's generic note (`rule`).

## Ground truth in short

- **Must do:** residence and travel history; parasitological confirmation (marrow amastigotes or PCR); HIV test; liposomal amphotericin B; keep immunosuppression stopped; notify public health; follow-up for relapse.
- **Must not do:** restart or escalate immunosuppression; commit to SLE without parasitology; splenectomy; splenic aspiration at these counts.
- **Rubric:** 5 VL with H11 cited; 4 VL; 3 secondary HLH or hypersplenism; 2 SLE, another infection, lymphoma, MPN or liver disease; 1 anything else.

## Curator's decisions

Atul delegated the open questions to the curator. Each is recorded here; the value decisions stay open for his case review (L1.4).

1. **Day 0** is the authors' admission ("This hospital, Day 1"). The article gives no dates for the earlier hospitals. I placed the local hospital on day -200, rheumatology day 1 on -120 and day 45 on -75 (gap G09): nine months of illness, several months of sequential drugs, and a taper to 20 mg before she stopped. The exact days do not affect play because the clock runs on day 0 only.
2. **Post-treatment results are outcome facts** (release never, no catalogue link), as PMC11227049 did, so `case_days` stays at day 0 and no result from after treatment can answer a request during the work-up.
3. **Units (the batch rule):** Table 1 misprints several units. Hb is printed "g/dl" but is g/L (range 115-150); C3, C4 and IgG are printed "mg/dl" but are g/L; the differential is headed "%" but is absolute (x10^9/L); haematocrit converted from % to L/L; D-dimer converted from 3,936 ng/mL to 3.94 mg/L (assay type, FEU or DDU, not stated). Every printed value and unit is in the series note.
4. **Values printed as "Negative" for quantitative tests** at the other hospital (LDH, D-dimer, C4) are not transcribed as values; the text's "low C3 and C4" appears in the rheumatology record (H13).
5. **"Cytomegalovirus" and "Epstein-Barr virus" in Table 1** name no assay. I read them as plasma DNA by PCR (the routine Chinese fever panel), which fits EBV turning from negative to positive under immunosuppression. This needed two new tests, `LAB.MOL.EBV_DNA` and `LAB.MOL.CMV_DNA`; EBV and CMV serology are resolved as past infection. Reviewer: if you read them as serology instead, S29 and S30 move to `CMP.CMV_IGM` and `CMP.EBV_VCA_IGM`.
6. **DAT specificity:** the article gives only "positive". I recorded it against the IgG reagent (S22) and set C3d weakly positive (judgement call), fitting low C3.
7. **Blood group:** not reported; group O RhD positive from Han Chinese frequencies (`affected`, confidence 0.35 for ABO).
8. **Laboratory profile:** the article's printed ranges (converted) plus their relatives (MONO, BASO, RBC, MCV, MCH, MCHC, ALP, GGT, total protein) from the Chinese standard intervals the article's ranges match (WS/T 404 and 405), so synthetic rows look like the article's laboratory.
9. **HLH markers** (G07): triglycerides 2.4 mmol/L, fibrinogen 2.2 g/L and sCD25 1,850 U/mL, all plausible in active disease but below the HLH-2004 thresholds, so the article's picture (no HLH reported) holds. Judgement calls.
10. **rK39** (not done in the article, G04): positive, confidence 0.7, judgement call. Sensitivity may be lower after immunosuppression; reasonable clinicians could set it negative to make the marrow indispensable.
11. **Examination** (G01-G03): fever 39.4 °C, pulse 116, BP 102/62; spleen about 15 cm below the costal margin, crossing the umbilicus, and liver 4 cm, to fit a 25.9 cm spleen on CT; mild ankle oedema (albumin 20 g/L); a few bruises (platelets 29); no rash, synovitis or significant lymphadenopathy; weight 45 kg, BMI 18.0.
12. **Patient-dependent normals:** menstrual history (scanty and irregular), obstetric history (one normal delivery), pulse, ECG rate (114), postural BP (a small drop, light-headed), height and weight, peak flow (84% predicted, untreated asthma) and capillary glucose are written as `affected` rows. The pelvic examination template fits her and is left to the generator.
13. **Steroid withdrawal:** 8 am cortisol 160 nmol/L (low), judgement call. It is a real problem to cover (hydrocortisone is not penalised) but not the diagnosis.
14. **Autoantibodies at this admission:** ANA 1:160, anti-dsDNA and anti-Sm negative (article); anti-Ro52 weakly positive (judgement call), anti-PM-Scl weakly positive, AMA-M2 positive (persisting), the rest negative. The lupus trap stays fair: the serology is suggestive but the discriminators argue against it.
15. **Urine:** no proteinuria or haematuria, arguing against lupus nephritis (not reported in the article; the local hospital reported normal renal function).
16. **Reports:** the day-0 marrow aspirate is one final report (`only`) with the amastigotes, because the article describes one diagnostic marrow at this hospital; the two earlier marrows appear only in the records (H12, H13). The trephine calls no organisms (less sensitive, and the rheumatology biopsy was non-diagnostic). A liver biopsy or splenic aspirate, if a player risks one, would show the organisms.
17. **Consult notes never name the disease.** The infectious diseases note names the tests (rK39, Leishmania PCR) only once H11 is in the Chart, and the leak scan stays clean.
18. **No `reviewer` rows.** Nothing in this case needed a value the curator must not guess.
19. **Specialty** is set to "infectious diseases" (the pilot's is "haematology"); change it if Nidana groups batch 1 under haematology.
20. **Splenic aspiration is a must-not-do** at platelets 29 x10^9/L and PT 14.6 s (the Indian programme's contraindications), with test utility "risky", while it stays available and diagnostic.

## Catalogue needs (`catalogue_needs.json`)

Checked with `scripts.catalogue_checks` on a scratch copy of the CSVs: no errors. New tests are priced as estimates.

| Kind | New items |
| --- | --- |
| History (1) | `HX.SOCIAL.RESIDENCE` birthplace, native place and places lived (template pending review) |
| Tests (8) | `LAB.SERO.RK39`, `LAB.MOL.LEISHMANIA_PCR`, `LAB.SERO.BRUCELLA`, `LAB.IMM.SIL2R`, `LAB.MOL.EBV_DNA`, `LAB.MOL.CMV_DNA`, `LAB.IMM.ANTIPHOSPHOLIPID`, `PROC.SPLEEN.ASPIRATE` |
| Components (10) | `CMP.RK39`, `CMP.LEISHMANIA_PCR`, `CMP.BRUCELLA_SAT`, `CMP.SIL2R`, `CMP.EBV_DNA`, `CMP.CMV_DNA`, `CMP.ACL_IGG`, `CMP.ACL_IGM`, `CMP.B2GP1_IGG`, `CMP.SPLENIC_ASPIRATE_REPORT` |
| Actions (3) | `RX.ANTIPARASITIC.LIPOSOMAL_AMPHOTERICIN`, `RX.ANTIPARASITIC.MILTEFOSINE`, `RX.ANTIPARASITIC.ANTIMONIAL` |
| Findings (1) | `FND.LD_BODIES` (shown by `PROC.BM.ASPIRATE`, `PROC.SPLEEN.ASPIRATE`, `PROC.BIOPSY.LIVER`; `shown_by` goes in `findings.csv` when merged) |
| Normal templates (1) | `HX.SOCIAL.RESIDENCE` |

Existing ids used: `DX.KALA_AZAR`, `RX.ANTIFUNGAL.AMPHOTERICIN` (also accepted for the must-do), `RX.IMMUNO.STOP`, `ACT.NOTIFY_PUBLIC_HEALTH`. The lead curator may merge `HX.SOCIAL.RESIDENCE` with `HX.SOCIAL.TRAVEL` (whose synonyms include "native place visit") if a separate item is not wanted.

## Replay

`uv run python -m scripts.case_replay cases/PMC12364935`: **0 open problems** (25 Sep 2026). Rows: article facts 102, derived 3; ledger affected 197 (190 written, 7 calculated from formulas; 25 judgement calls), normal 314, rule 1, reviewer 0; 23 reports (none provisional); 23 consult notes (13 affected, 10 rule); 10 lay texts; 85 test utility rows.

## Case Reviewer checklist

- [ ] Verify every series point in the gold file against Table 1 and the text, especially the unit corrections (decision 3) and the columns for CRP, ferritin, LDH, D-dimer and C4, where Table 1 has blank or "Negative" cells.
- [ ] Accept or change the day placement of the earlier hospitals (decision 1).
- [ ] Decide the EBV and CMV assay reading (decision 5).
- [ ] Review the 25 judgement calls, most important first: rK39 positive; spleen and liver on palpation; vital signs; HLH markers; DAT C3d; anti-Ro52; 8 am cortisol; the rest.
- [ ] Check that H11 is released only by a residence or travel question, and that the vignette gives only her place of work.
- [ ] Read RP01 (the diagnostic marrow), CN02 and CN03 (infectious diseases) for fairness: helpful, never more diagnostic than the Chart allows.
- [ ] Confirm the must-do and must-not-do lists, especially splenic aspiration as a must-not-do and HIV testing as a must-do.
- [ ] Approve or merge the new catalogue items (above), including the `HX.SOCIAL.RESIDENCE` template.
- [ ] After the figures are downloaded, confirm `has_annotations` and that no figure shows the diagnosis in text (Figure 3 may carry a "Leishmania" label).

## Corrections after the second review (2026-09-26)

1. **Prothrombin activity (Quick %, `CMP.PT_ACTIVITY`, day 0)** was left to the normal generator, which gave 89% beside the affected INR 1.22 (PT 14.6 s). It is now an `affected` row (`curation/affected.json`): 73% (70-120), no flag, from the Case Library's common curve, activity % = round(100 x 0.59 / (INR - 1 + 0.59)), capped at 100 (0.59 calibrated to an article pair in another batch case, 44% at INR 1.75). Day 0 is the only day with a value, before and after. Not a judgement call.
2. **Other coagulation values checked against INR 1.22:** PT 14.6 s, APTT 37.8 s, fibrinogen 2.2 g/L, thrombin time 16.7 s, factors II 72, V 68, VII 58 and X 70 IU/dL, a correcting mixing study and normal protein C, protein S and antithrombin are consistent; no change. One value outside the INR question is left for the reviewer: the generator's FDP 2.8 mg/L (normal) is lower than the article's D-dimer 3.94 mg/L FEU, although D-dimer is one of the fibrin degradation products; an `affected` FDP (raised, for example about 9 mg/L) would fit better.

Replay after the change: 0 open problems; ledger affected 201, normal 368, rule 2.
