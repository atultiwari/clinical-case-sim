# Pilot analysis: PMC12949993

Case id `PMC12949993` · Target: `PMC12949993@v1.r1` · Status: **draft analysis for the Case Reviewer. Nothing here is in the Case Vault yet.**

> Spoiler warning. This file contains the answer. Never copy its content into player-facing code, UI text or fixtures that a player can see.

This file is the "detailed analysis beforehand" for the pilot: how players are likely to work the case up, and what each catalogue item on those paths should return. It serves both Nidana and Sambhasha. Claude turns it into Case Vault rows in task L0.9, and Atul reviews them in the pilot review (L0.10).

---

## 1. Source and starting point

Chew JE, Klose N. *Lead Toxicity Masquerading as Autoimmune Haemolytic Anaemia: A Diagnostic Pitfall in Unexplained Anaemia.* Cureus 18(1): e102622. Published 30 Jan 2026. doi:[10.7759/cureus.102622](https://doi.org/10.7759/cureus.102622) · [PMC12949993](https://pmc.ncbi.nlm.nih.gov/articles/PMC12949993/) · CC BY 4.0.

The Case Library starts from the work done with Sambhasha's design (then called VDT) rather than repeating it. Both files are in this folder:

- Dossier: `PILOT_CASE.md`
- Draft case file (schema 0.2): `gold-case-file.draft.json`, with 10 history facts (H01–H10), 19 series (S01–S19, 125 values), 26 single results (L01–L26), 3 raw-material items (R01–R03), 4 figures (M01–M04), the ground truth and 20 gaps (G01–G20).

What this analysis adds: catalogue links and release rules, the patient's words, report variants with their status, consult notes, a full path analysis, catalogue-wide resolution, and the rubric, must-do and must-not-do as conditions.

**Checked against the article on 25 Sep 2026:**

- The first film report described "marked red cell agglutination without other abnormalities". Basophilic stippling was found when the film was re-examined after the marrow.
- Every figure carries arrows: Figure 1 (agglutination), Figure 2A (coarse basophilic stippling), Figure 2B (an arrowhead on a ring sideroblast) and Figure 3 (stippling).
- The article does not report: vital signs or examination; the supplement's form, origin or duration; the ring sideroblast percentage or marrow cellularity; the succimer dose; follow-up blood lead values. These are all synthetic or reviewer-set below.
- Article keywords name the diagnosis (anaemia, basophilic stippling, blood smear, chelation therapy, dietary supplements, haemolytic, lead poisoning, pappenheimer bodies), so they must never reach a player before the debrief.

---

## 2. Case card

| Field | Draft |
| --- | --- |
| Neutral title | Abdominal pain and tiredness in a 49-year-old woman |
| Tags | Haematology · Anaemia · Abdominal pain |
| Slug | Opaque, generated at freeze (never the PMCID) |
| Vignette (from the dossier) | A 49-year-old woman with inclusion body myositis, on long-term intravenous immunoglobulin, presents with a three-week history of worsening abdominal pain and progressive lethargy. |
| Patient's opening words | "My tummy has been hurting for about three weeks and it's getting worse. And I'm exhausted all the time." |

The opening words carry only H05 and H06; they add nothing the article does not say.

---

## 3. Hidden history: catalogue mapping

| Catalogue item | Releases | Patient's words (draft) |
| --- | --- | --- |
| `HX.MEDS.CURRENT` "Current medicines" | H03, H04 | "I have immunoglobulin drips for my muscle condition, and I started mycophenolate tablets a little while ago." |
| `HX.EXPOSURE.TOXINS` "Exposure to toxins or chemicals" | H09 | "Not that I know of." |
| `HX.MEDS.SUPPLEMENTS` "Herbal, traditional or over-the-counter remedies" | H10 | "Actually, yes. A friend gave me a herbal supplement recently. There's no label on it." |
| `HX.MEDS.SUPPLEMENT_DETAILS` "Details of any remedy or supplement" | H10 plus a ledger row (§6) | H10's words, then the synthetic details |
| `HX.GI.BLEEDING` | H08 | "No, no blood." |
| `HX.GEN.RECENT_INFECTION` | H07 | "No, I haven't been unwell with anything." |
| `HX.RECORDS.PREVIOUS` "Previous results" | Baseline values at day −100 (S01–S03, S05, S06, S13) | Shown as a results table |

Synonyms that must also reach `HX.MEDS.SUPPLEMENTS`: supplements, vitamins, herbal, Ayurvedic, traditional or Chinese medicine, home remedies, tonics, over-the-counter, alternative medicine, imported medicines.

A generic toxin question never releases H10. A current-medicines question never releases H10: patients often do not count a friend's herbal product as a medicine, which is the case's teaching point.

---

## 4. Report variants and figures

| Id | Test | Variant and status | Content (draft) | Origins |
| --- | --- | --- | --- | --- |
| RP01 | `LAB.HAEM.FILM` | `original`, **provisional** (Nidana Standard and Expert) | Status line: "Provisional report: screening film, not yet reviewed by a haematopathologist. A review can be requested." Report: "Marked red cell agglutination. No other abnormality seen." | article |
| RP02 | `LAB.HAEM.FILM` (Nidana Guided) and `LAB.HAEM.FILM_REVIEW` | `expert`, **final** | Status line: "Final report, reviewed by a haematopathologist." Agglutination; coarse basophilic stippling in a proportion of red cells; Pappenheimer bodies; polychromasia; no spherocytes or red cell fragments. Comment: "Suggest a blood lead level and haemoglobin studies." | article (R01), `affected` (G16) and the comment (judgement call) |
| RP03 | `PROC.BM.ASPIRATE` | `only`, final | Dyserythropoietic features; coarse basophilic stippling in erythroid precursors; atypical plasma cells present; cellularity and blast count from G15 | article (R02), reviewer (G15) |
| RP04 | `LAB.BM.IRON_STAIN` | `only`, final | Ring sideroblasts present (percentage set by Atul); iron stores present | article (R03), reviewer (G15) |
| RP05 | `PROC.BM.TREPHINE` | `only`, final | See §6, marrow | `affected` (G15) |

Finding tags (Case Library SPEC §6.8): RP01 `FND.RBC_AGGLUTINATION`; RP02 `FND.RBC_AGGLUTINATION`, `FND.COARSE_BASOPHILIC_STIPPLING`, `FND.PAPPENHEIMER_BODIES`, `FND.POLYCHROMASIA`; RP03 `FND.DYSERYTHROPOIESIS`, `FND.COARSE_BASOPHILIC_STIPPLING`, `FND.ATYPICAL_PLASMA_CELLS`; RP04 `FND.RING_SIDEROBLASTS`.

The provisional label is there so that no player takes RP01 for the final word (Nidana N-014), while still leaving the decision to request a review to the player. The debrief explains that in the real case the first report was treated as final and the stippling was found only on review.

The expert comment may name a test ("blood lead"), never the diagnosis. The leak scan allows test names and blocks diagnosis names.

**Figures:** M01–M04 carry arrows. During development they appear as published (S-006): beside the report in Nidana's Guided mode, in every debrief, and in the Pathology seat. Before the store release, Atul records a decision for each figure: use, mask or exclude. Sambhasha's image mode receives the figures with neutral captions.

---

## 5. Path analysis (draft)

| Path | Kind | Why a player goes there | What the case must show |
| --- | --- | --- | --- |
| P1 Efficient | efficient | Haemolysis screen and film; film review shows stippling; targeted remedy question; blood lead | Stippling on review; H10 only on a specific question; blood lead 77.8 µg/dL |
| P2 Warm AIHA | trap | IgG 1+ DAT, agglutination on the film, haemolysis markers | A weak IgG-only DAT in a group A patient on IVIG is likely passive; no spherocytes; steroids are a must-not-do |
| P3 IVIG-associated haemolysis | trap | Group A patient on IVIG with a positive DAT | A plausible contributor, not the diagnosis; the eluate result is a judgement call |
| P4 Sideroblastic anaemia or MDS | trap | Ring sideroblasts and dyserythropoiesis in the marrow | No clonal markers; copper normal; little alcohol; no culprit drugs |
| P5 Plasma cell disorder | alternative | Atypical plasma cells, raised free light chains, anaemia | No paraprotein; normal ratio; polyclonal on flow; no bone lesions |
| P6 Acute porphyria | alternative | Abdominal pain with anaemia | Porphobilinogen not in the acute range; ALA and coproporphyrin raised |
| P7 Gastrointestinal cause | alternative | Abdominal pain | Examination, lipase, imaging and endoscopy normal or non-specific |
| P8 Haemoglobinopathy or red cell enzyme disorder | alternative | Basophilic stippling with haemolysis; inherited pyrimidine 5′-nucleotidase deficiency is the classic differential | HPLC normal; MCV normal; iron replete. Pyrimidine 5′-nucleotidase activity is low because lead inhibits the enzyme, which can mislead a player towards the inherited disorder |
| P9 Myositis and neuromuscular | alternative | Known IBM; raised CK and transaminases | IBM pattern; no neuropathy; CK, aldolase and troponin T fit myositis |
| P10 Drug-related anaemia | alternative | Mycophenolate recently started | Reticulocytosis argues against marrow suppression; no drugs that cause sideroblastic anaemia |
| P11 Infection while immunosuppressed | alternative | Anaemia on immunosuppression | No active parvovirus or CMV; afebrile; CRP normal |
| P12 Other heavy metals | alternative | The supplement is disclosed | Mercury and arsenic values set by Atul (the product contained both) |

---

## 6. Draft `affected` and reviewer-set items

Guidance, not final values: Claude sets exact numbers in L0.9 and they reach Atul in the review pack. "J" marks a judgement call. Gap ids (G01–G20, from the dossier) are given where they apply.

### History

| Item | Paths | Draft answer | Priority | J |
| --- | --- | --- | --- | --- |
| `HX.PC.PAIN_DETAILS` | P1, P7 | Diffuse, crampy, comes and goes, worse this past week; not related to meals; does not spread | medium | J |
| `HX.GI.BOWEL_HABIT` | P6, P7 | A little constipated in recent weeks; no diarrhoea, no blood | medium | J: classic for lead colic but unreported; the alternative is "no change" |
| `HX.GI.NAUSEA_APPETITE` | P7 | Poor appetite, occasional nausea, no vomiting, no weight loss noticed | low | J |
| `HX.GU.URINE_COLOUR` | P2, P3 | Has not noticed dark or red urine | medium | |
| `HX.GEN.JAUNDICE` | P2 | Has not noticed yellow eyes or skin | medium | |
| `HX.CVS.BREATHLESSNESS` | P1 | Breathless on stairs over the past couple of weeks | medium | |
| `HX.GEN.FEVER_SWEATS_WEIGHT` | P5, P11 | No fevers, sweats or weight loss | medium | |
| `HX.NEURO.WEAKNESS` | P9 | Long-standing weak grip and thighs from the myositis, unchanged; nothing new in the wrists or feet | medium | G05 |
| `HX.NEURO.SENSORY` | P9 | No numbness or tingling | low | |
| `HX.NEURO.COGNITION_MOOD` | P1 | Tired and "foggy"; no confusion, no headaches | low | J |
| `HX.GEN.METALLIC_TASTE` | P1 | No | low | J: a classic sign the article does not report, so do not add it |
| `HX.MEDS.SUPPLEMENT_DETAILS` | P1, P12 | Capsules from a friend, taken most days for some weeks; does not know the contents or origin | high | J, G08 |
| `HX.EXPOSURE.OTHERS_EXPOSED` | P1 | Her friend takes the same product; nobody else she knows of | medium | J: supports the public-health must-do |
| `HX.EXPOSURE.OCCUPATION` | P1 | "I work in an office." The answer names the job only; the rationale records that it carries no lead exposure (Case Library SPEC §6.4, rule 8) | medium | G08 |
| `HX.EXPOSURE.HOBBIES` | P1 | "Reading and walking, mostly." The rationale records no shooting, soldering, stained glass, glazes or sinkers | medium | G08 |
| `HX.EXPOSURE.HOME` | P1 | No recent renovation or paint stripping at home; town water supply | medium | G08 |
| `HX.SOCIAL.ALCOHOL` | P4 | An occasional drink, well within safe limits | medium | |
| `HX.PMH.IVIG_DETAILS` | P2, P3 | Maintenance IVIG; last infusion within the past four weeks | high | J, G06 |
| `HX.PMH.MYCOPHENOLATE` | P10 | Standard dose, started some weeks before admission | medium | J, G07 |
| `HX.PMH.TRANSFUSION_PREGNANCY` | P2 | No transfusions; number of pregnancies set by Atul | low | reviewer |
| `HX.FAMILY.BLOOD` | P8 | No family history of anaemia or blood disorders | low | |
| `HX.GYN.MENSES` | P1 | Periods lighter and irregular over the past year; not heavy | low | J |

### Examination

| Item | Paths | Draft finding | Priority | J |
| --- | --- | --- | --- | --- |
| `EX.GEN.VITALS` | all | Temperature 36.8 °C; pulse about 100–105, regular; BP about 125/75; respiratory rate 16; SpO2 98% on air | high | J, G01 |
| `EX.GEN.PALLOR` | P1 | Conjunctival and palmar pallor | medium | G02 |
| `EX.GEN.JAUNDICE` | P2 | No clinical jaundice: a bilirubin of 29 µmol/L is below the level at which icterus is usually visible | medium | J, G02 (the dossier suggested mild icterus was possible) |
| `EX.GEN.LYMPH_NODES` | P5, P11 | No lymphadenopathy | medium | |
| `EX.ORAL.GUMS` | P1 | Gum margins normal, with no pigmentation | high | G04: never invent a gum line |
| `EX.ABD.PALPATION` | P7 | Soft; diffuse mild tenderness; no guarding or rebound; bowel sounds present | medium | G03 |
| `EX.ABD.LIVER_SPLEEN` | P2, P5 | Liver and spleen not palpable | medium | G02 |
| `EX.CVS.AUSCULTATION` | P1 | Soft systolic flow murmur; otherwise normal | low | J |
| `EX.NEURO.MOTOR` | P9 | Weak finger flexors and quadriceps with wasting, as expected in IBM; no wrist or foot drop | medium | G05 |
| `EX.NEURO.REFLEXES_SENSATION` | P9 | Knee reflexes reduced; sensation intact | low | J |
| `EX.SKIN.INSPECTION` | P9, P11 | No rash, purpura or signs of dermatomyositis | low | |

### Haematology and blood bank

| Item | Paths | Draft result | Priority | J |
| --- | --- | --- | --- | --- |
| `CMP.MCH`, `CMP.MCHC`, `CMP.RETIC_PCT` | — | `derived`: 30 pg, 327 g/L and 7.9% on day 0 | — | formula |
| Day-0 white cell differential | — | `derived`: carried back from day 1, scaled to the day-0 white count of 4.9 | — | formula |
| `CMP.RDW` | P1, P2 | Raised (about 16–18%) with the reticulocytosis | medium | |
| `LAB.HAEM.ESR` | P5, P11 | Moderately raised: anaemia and IVIG both raise the ESR while CRP stays normal | medium | J (value) |
| `LAB.TBS.ELUATE` | P2, P3 | Likeliest: non-reactive with group O panel cells, reactive with A1 cells (passively acquired anti-A in a group A patient on IVIG). Alternative: no specific reactivity | high | J: it steers towards IVIG-related haemolysis, a score-2 diagnosis |
| `LAB.TBS.DL_TEST` (Donath–Landsteiner) | P2 | Negative | low | |
| `LAB.HAEM.G6PD` | P2, P8 | Normal activity | medium | |
| `LAB.HAEM.PK` | P2 | Normal | low | |
| `LAB.HAEM.EMA_BINDING` | P2 | Normal | medium | |
| `LAB.HAEM.HB_HPLC` | P8 | Normal HbA2 and HbF; no variant | medium | G20 |
| `LAB.HAEM.PNH_FLOW` | P2 | No PNH clone | medium | |
| `LAB.HAEM.P5N_ACTIVITY` (pyrimidine 5′-nucleotidase) | P8 | Reduced, because lead inhibits the enzyme | high | J (value; whether the catalogue offers the test) |
| `LAB.HAEM.ALAD_ACTIVITY` (ALA dehydratase) | P1, P6 | Markedly reduced, because lead inhibits it | medium | |
| `CMP.EPO` (erythropoietin) | P1, P10 | Raised, appropriate for the anaemia | low | |
| `CMP.STFR` (soluble transferrin receptor) | P1 | Raised, reflecting erythroid expansion | low | |
| `CMP.IRF` (immature reticulocyte fraction) | P1, P2 | Raised | low | |

### Chemistry

| Item | Paths | Draft result | Priority | J |
| --- | --- | --- | --- | --- |
| `CMP.BILI_CONJ` | P2 | Conjugated bilirubin low (about 3–5 µmol/L); the rest unconjugated | medium | |
| `CMP.URATE` | P1 | Normal or mildly raised | low | J, G09 |
| `LAB.CHEM.LIPASE` | P7 | Normal | medium | |
| `LAB.CHEM.HBA1C` | P1 | Low-normal, falsely lowered by shortened red cell survival | low | J |
| `LAB.CHEM.ALDOLASE` | P9 | Raised (myositis) | low | |
| `LAB.CHEM.TROPONIN_T` | P9 | Mildly raised (re-expression in regenerating muscle in myositis), with troponin I normal | medium | J: realistic, but may send players down a cardiac path |
| `LAB.CHEM.TROPONIN_I` | P9 | Normal | low | |
| `LAB.CHEM.COPPER_CAERULOPLASMIN` | P4 | Normal | high | G13 |
| `LAB.CHEM.ZINC` | P4 | Normal | low | |
| `LAB.CHEM.VITAMIN_B6` | P4 | Normal | low | |
| `LAB.URINE.URINALYSIS` | P2 | No blood or protein; urobilinogen increased; bilirubin negative | medium | G10 |

### Toxicology and porphyrins

| Item | Paths | Draft result | Priority | J |
| --- | --- | --- | --- | --- |
| `LAB.TOX.ZPP` | P1, P4 | Raised (iron studies are replete, so iron deficiency does not explain it) | high | G11 |
| `LAB.TOX.URINE_ALA` | P1, P6 | Raised | high | G12 |
| `LAB.TOX.URINE_PBG` | P6 | Normal or only mildly raised; not in the acute porphyria range | high | G12 |
| `LAB.TOX.URINE_PORPHYRINS` | P6 | Coproporphyrin raised; pattern not typical of a porphyria | medium | |
| `LAB.TOX.FAECAL_PORPHYRINS` | P6 | Normal | low | |
| `LAB.TOX.URINE_LEAD` | P1 | Raised | medium | J (value) |
| `LAB.TOX.URINE_MERCURY` | P12 | Set by Atul: the product contained mercury, and the patient's level was not reported. Inorganic mercury from remedies is usually measured in urine | high | reviewer, G14 |
| `LAB.TOX.BLOOD_MERCURY` | P12 | Set by Atul, consistent with the urine value | medium | reviewer, G14 |
| `LAB.TOX.URINE_ARSENIC` | P12 | Set by Atul: arsenic is measured in urine, as blood levels fall quickly | high | reviewer, G14 |

### Marrow, flow and genetics

| Item | Paths | Draft result | Priority | J |
| --- | --- | --- | --- | --- |
| `PROC.BM.TREPHINE` | P4, P5 | Cellularity normal to mildly increased for age with erythroid hyperplasia; no excess blasts; no fibrosis; plasma cells not increased | high | J, G15 |
| Ring sideroblast percentage | P4 | Set by Atul | high | reviewer, G15 |
| `LAB.BM.FLOW` | P4, P5 | No abnormal blast population; plasma cells few and polyclonal | high | |
| `LAB.CYTOGEN.KARYOTYPE` | P4 | 46,XX | high | G15 |
| `LAB.MOL.MYELOID_NGS` (includes SF3B1) | P4 | No pathogenic variants detected | high | |
| `LAB.CYTOGEN.FISH_MDS` | P4 | Normal | medium | |

### Plasma cell screen

| Item | Paths | Draft result | Priority | J |
| --- | --- | --- | --- | --- |
| `LAB.IMM.URINE_BJP` | P5 | No Bence Jones protein | medium | |
| `LAB.IMM.B2M` | P5 | Normal | low | |
| `IMG.CT.WHOLE_BODY_LOW_DOSE` or skeletal survey | P5 | No lytic lesions | medium | |

### Infection and immunology

| Item | Paths | Draft result | Priority | J |
| --- | --- | --- | --- | --- |
| `LAB.SERO.PARVOVIRUS_B19` | P11 | IgM negative; IgG positive (past infection or passive from IVIG); PCR not detected | medium | |
| `LAB.SERO.CMV` | P11 | IgG positive (possibly passive); PCR not detected | low | |
| `LAB.SERO.HEPATITIS_B` | P11 | HBsAg negative; anti-HBc set by Atul (IVIG can transfer it passively) | low | reviewer |
| `LAB.IMM.ANA` | P2, P9 | Negative or low titre | low | J |
| `LAB.IMM.MYOSITIS_ANTIBODIES` (anti-cN1A) | P9 | Set by Atul: positive in a proportion of IBM | low | reviewer |
| `LAB.IMM.COMPLEMENT` | P2 | C3 and C4 normal | low | |
| `LAB.IMM.COELIAC_TTG` | P7 | tTG-IgA negative; total IgA slightly low (1.12 g/L) but not deficient, so the test is valid | low | |

### Imaging, endoscopy and physiology

| Item | Paths | Draft result | Priority | J |
| --- | --- | --- | --- | --- |
| `IMG.XR.ABDOMEN` | P1, P7 | No obstruction; no radio-opaque material | medium | J, G17: some contaminated remedies show radio-opaque flecks after recent ingestion |
| `IMG.US.ABDOMEN` | P2, P7 | Normal liver; spleen not enlarged; no gallstones | medium | G17 |
| `IMG.CT.ABDOMEN_PELVIS` | P5, P7 | No acute pathology; no lymphadenopathy | medium | G17 |
| `PROC.ENDO.OGD` | P7 | Normal or mild non-specific gastritis | low | G18 |
| `PROC.ENDO.COLONOSCOPY` | P7 | Normal | low | |
| `LAB.GI.FIT` | P7 | Negative | low | |
| `PROC.CARD.ECG` | P1 | Sinus tachycardia about 100/min; otherwise normal | low | |
| `PROC.NEURO.NCS_EMG` | P9 | Myopathic pattern of IBM; no motor neuropathy | medium | G19 |

**Everything else in the catalogue goes to the normal list,** including renal function and electrolytes (G09, apart from urate), calcium, glucose, thyroid function, the coagulation screen and the chest X-ray. Atul sees the list of names, not the values, and should flag anything that belongs above: lead also touches less common assays, such as the two enzyme activities listed under haematology.

**Component coverage notes:**

- Albumin (40 g/L) and total protein (67 g/L) come from the electrophoresis result (L18) and count as `article` for `CMP.ALBUMIN` and `CMP.TOTAL_PROTEIN`.
- Sparse series carry forward: the platelet count has no day-6 value, and nucleated red cells are reported only on day 1.
- Reticulocytes were not measured on days 3 and 5, so those days return the latest earlier value (as the dossier notes).

---

## 7. Judgement calls for Atul

The ones that matter most, roughly in order:

1. **Eluate:** passively acquired anti-A (reactive with A1 cells only), or no specific reactivity?
2. **Expert film comment:** is "Suggest a blood lead level and haemoglobin studies" the right nudge?
3. **Ground truth:** should "film reviewed for stippling" stay a must-do when a player reaches the blood lead through the history alone?
4. **Rubric:** does a final diagnosis of arsenic or mercury poisoning score 3? Does inherited pyrimidine 5′-nucleotidase deficiency score 2?
5. **Bowel habit:** constipation, or no change?
6. **Troponin T:** mildly raised (realistic in myositis), or normal (fewer red herrings)? If raised, approve the cardiology note in §8.
7. **Jaundice on examination:** none, or equivocal?
8. **Supplement details** and **others exposed.**
9. **Marrow (G15):** ring sideroblast percentage, cellularity and trephine wording.
10. **Mercury and arsenic (G14):** urine values, and blood mercury.
11. **Pyrimidine 5′-nucleotidase activity:** how low, and whether the catalogue offers the test at all.
12. **Anti-HBc**, **anti-cN1A** and the number of pregnancies (reviewer-set).
13. **ESR, HbA1c, urate and urine lead** values.
14. **Abdominal X-ray:** radio-opaque material or not.
15. **IVIG and mycophenolate details** (G06, G07); menses.

---

## 8. Consult notes (plan)

| Referral | Variants and conditions | Content principles |
| --- | --- | --- |
| `REF.HAEMATOLOGY` | V1: stippling not yet in the Chart. V2: stippling in the Chart (`finding_released: [FND.COARSE_BASOPHILIC_STIPPLING]`). V3: blood lead in the Chart (`released_any: [L26]`) | V1: a weak IgG-only DAT in a group A patient on IVIG may be passive; review the film for red cell inclusions; take a full medicine and remedy history; hold off escalating immunosuppression. V2 adds that coarse stippling calls for a blood lead, haemoglobin studies and, if those are unrevealing, pyrimidine 5′-nucleotidase activity. V3 supports chelation through toxicology and follow-up counts. Never names the diagnosis before V3 |
| `REF.TOXICOLOGY` | V1: blood lead not in the Chart. V2: blood lead in the Chart | V1: asks for an exposure history covering remedies and supplements, occupation and hobbies, and suggests a blood lead. V2: stop the source; oral succimer; repeat blood lead after the course and for rebound; notify public health; test the product and its other users |
| `REF.GASTROENTEROLOGY` | V1 only | No sign of a surgical abdomen or bleeding; lipase and imaging as needed; endoscopy not urgent; suggests considering metabolic or toxic causes of colicky pain with anaemia (judgement call: is this too strong a nudge?) |
| `REF.NEUROLOGY` | V1 only | Weakness fits the known IBM; no neuropathy on examination; nothing new neurologically. Decisions about IVIG are left to the treating team and haematology, given the haemolysis |
| `REF.CARDIOLOGY` | V1 only, if judgement call 6 makes troponin T raised | A troponin T rise with a normal troponin I and a normal ECG fits a skeletal-muscle source in myositis; no cardiac cause for the symptoms |
| All other `REF.*` | Generic note (`rule`) | "No specific concerns from our side; happy to review if new problems arise." |

---

## 9. Must-do and must-not-do as conditions

The dossier's lists, expressed over catalogue ids (vocabulary in Case Library SPEC §10.4).

| Must do | Condition (draft) |
| --- | --- |
| Ask specifically about supplements, herbal, traditional or imported medicines and over-the-counter products | `asked_any: [HX.MEDS.SUPPLEMENTS, HX.MEDS.SUPPLEMENT_DETAILS]` |
| Have the blood film reviewed for basophilic stippling | `finding_released: {findings: [FND.COARSE_BASOPHILIC_STIPPLING], from_tests: [LAB.HAEM.FILM, LAB.HAEM.FILM_REVIEW]}`. In Nidana this is RP02 (from the film review, or the first film in Guided mode); in Sambhasha, a Pathology Service film report that reports the stippling. See judgement call 3 |
| Measure venous blood lead | `ordered_any: [LAB.TOX.BLOOD_LEAD]` |
| Stop the exposure before or alongside chelation | `plan_has: [ACT.STOP_SUSPECTED_SOURCE]` and `plan_before: [ACT.STOP_SUSPECTED_SOURCE, RX.CHELATION.*]` |
| Chelate with oral succimer, with clinical toxicology input | `plan_has: [RX.CHELATION.SUCCIMER_ORAL]` and (`referred_any: [REF.TOXICOLOGY]` or `plan_has: [REF.TOXICOLOGY]`) |
| Notify public health, test the product and ask who else took it | `plan_has: [ACT.NOTIFY_PUBLIC_HEALTH]` and (`asked_any: [HX.EXPOSURE.OTHERS_EXPOSED]` or `plan_has: [ACT.SCREEN_CONTACTS]`) |
| Plan a repeat blood lead after chelation | `plan_has: [ACT.REPEAT_BLOOD_LEAD]` |

| Must not do | Condition (draft) |
| --- | --- |
| Escalate immunosuppression for presumed warm AIHA | `plan_has_any: [RX.STEROID.HIGH_DOSE, RX.IMMUNO.RITUXIMAB, RX.IMMUNO.ESCALATE, RX.SURGERY.SPLENECTOMY]` |
| Label MDS before excluding reversible causes | `dx_in: [DX.MDS_RING_SIDEROBLASTS]` and `not: ordered_all: [LAB.TOX.BLOOD_LEAD, LAB.CHEM.COPPER_CAERULOPLASMIN]` |
| Chelate while the exposure continues | `plan_has_any: [RX.CHELATION.*]` and `not: plan_has: [ACT.STOP_SUSPECTED_SOURCE]` |
| Start empirical iron | `plan_has_any: [RX.IRON.ORAL, RX.IRON.IV]` |

Rubric conditions are as in Case Library SPEC §10.4: anchor 5 needs lead poisoning with the supplement (H10) cited as evidence at commit. Stopping the source is scored once, as a must-do.

---

## 10. Reference paths (Standard difficulty)

The benchmark path follows the dossier's efficient path. It is written for Nidana's Standard difficulty. Times are simulated hours:minutes from arrival and are illustrative: the catalogue's turnaround times decide them, and prices come from the catalogue once it is built.

| Time | Action | Released |
| --- | --- | --- |
| 0:05 | Ask `HX.PC.PAIN_DETAILS` | Pain details |
| 0:10 | Ask `HX.MEDS.CURRENT` | H03, H04 |
| 0:15 | Ask `HX.GI.BLEEDING` | H08 |
| 0:25–0:45 | Examine `EX.GEN.VITALS`, `EX.GEN.PALLOR`, `EX.ABD.PALPATION` | Vital signs, pallor, mild diffuse tenderness |
| 0:45 | Order blood count, reticulocytes, liver tests, LDH, haptoglobin, DAT, film, renal function | — |
| 4:45 | (results) | Hb 72, MCV 93, reticulocytes 190, bilirubin 29, LDH 339, haptoglobin 0.20, DAT IgG 1+ C3d negative; film: provisional report (RP01), agglutination only |
| 4:50–4:55 | Ask `HX.MEDS.SUPPLEMENTS`, then `HX.EXPOSURE.OTHERS_EXPOSED` | H10; the friend takes it too |
| 4:55 | Order `LAB.HAEM.FILM_REVIEW` and `LAB.TOX.BLOOD_LEAD`; refer `REF.TOXICOLOGY` (orders take no simulated time) | — |
| 8:55 | (results) | Expert film report (RP02): stippling and Pappenheimer bodies; toxicology note V1 |
| 28:55 | (result) | Blood lead 77.8 µg/dL |
| 28:55 | Commit: `DX.LEAD_POISONING`, citing H10 and L26 as evidence; plan: stop the source, oral succimer, notify public health, repeat blood lead | Score: diagnosis 5, all must-dos |

A faster, equally sound path asks about remedies in the first ten minutes and orders the blood lead with the first bloods, committing at about 25 hours. Judgement call 3 decides whether that path also needs the film review.

---

## 11. Leak risks in this case

- The article's title and keywords name the diagnosis: never shown before the debrief.
- Every figure has arrows on the key finding. They stay in development (S-006); before the store release Atul decides for each figure: use, mask or exclude.
- The combination of IBM, IVIG, abdominal pain and anaemia is searchable. The vignette is paraphrased; accept the residual risk.
- The expert film comment and toxicology note V1 may name the blood lead test, never the diagnosis.
- Consult notes must not name the diagnosis before the blood lead is in the Chart.

---

## 12. Review checklist (in addition to the one in PILOT_CASE.md)

- [ ] Catalogue mapping and synonyms for H03, H04, H09 and H10
- [ ] The patient's words for every history fact, and the opening words
- [ ] Film report variants, their provisional and final status lines, and the expert comment
- [ ] The judgement calls in §7
- [ ] Consult note variants and their conditions
- [ ] Must-do, must-not-do and rubric conditions
- [ ] Reference paths and the benchmark cost
- [ ] Figures: kept as published in development; the production decision for each figure comes before the store release
- [ ] The normal list (in the review pack)
