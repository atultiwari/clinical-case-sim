# Pilot case: lead poisoning disguised as autoimmune haemolytic anaemia

Case id `PMC12949993` · Status: **draft, awaiting Case Reviewer verification** · Structured data: [`gold-case-file.draft.json`](gold-case-file.draft.json) · Path analysis: [`ANALYSIS.md`](ANALYSIS.md)

> Spoiler warning. This file and the JSON contain the answer. They are for the Case Reviewer and for developers, never for a player or a seat.

Written on 24–25 Sep 2026 with Sambhasha's design (then called the Virtual Diagnostic Team, VDT) and moved to the shared Case Library when the umbrella was created (S-001). "Seat", "Gatekeeper" and "Synthetic Findings Service" are Sambhasha's terms; in the Case Library, gaps are filled before play as ledger rows (Case Library SPEC §6).

## Source

Chew JE, Klose N. *Lead Toxicity Masquerading as Autoimmune Haemolytic Anaemia: A Diagnostic Pitfall in Unexplained Anaemia.* Cureus 18(1): e102622. Published 30 Jan 2026. doi:[10.7759/cureus.102622](https://doi.org/10.7759/cureus.102622) · [PMC12949993](https://pmc.ncbi.nlm.nih.gov/articles/PMC12949993/)

- **Licence:** CC BY 4.0. Verified on the PMC article page on 25 Sep 2026. The figures carry no separate credit line, so the article licence covers them.
- **Attribution to reuse:** "Adapted from Chew JE, Klose N, Cureus 18(1): e102622 (2026), CC BY 4.0. Restructured into atomic facts; diagnosis redacted from seat-facing text; simulated findings added where marked."
- **Setting:** Queensland, Australia (authors' affiliations: University of Queensland; Greenslopes Private Hospital).

## Why this case

| Criterion | This case |
| --- | --- |
| Licence allows adaptation and release | Yes, CC BY 4.0 |
| Full text in PMC (JATS XML) | Yes |
| Pathology decides the case | Yes. Coarse basophilic stippling on the film and ring sideroblasts in the marrow are the hinge. |
| A hidden history the Gatekeeper must guard | Yes. The herbal supplement was disclosed only when the exposure history was revisited with specific questions. |
| A fair anchoring trap | Yes. A weak IgG-only DAT in a patient on IVIG, plus agglutination on the film, points to warm autoimmune haemolytic anaemia (AIHA). |
| Several consultants plausibly involved | Gastroenterology (abdominal pain), haematology, neurology (inclusion body myositis on IVIG), clinical toxicology |
| Rich, dated data | Baseline values plus seven days of serial results across five tables |
| Clear management to score | Blood lead, remove the source, oral succimer, public health notification |
| Relevance to Indian practice | Heavy-metal contamination of herbal and Ayurvedic products is a known problem; an India-set sibling case is in the starter set below |
| Recency | Published January 2026, after the training cutoff of many current models |

Other candidates we checked (all CC BY), with our pilot score out of 10:

| Case | Why not the pilot |
| --- | --- |
| [PMC12007988](https://pmc.ncbi.nlm.nih.gov/articles/PMC12007988/): B12 deficiency pseudo-TMA mimicking TTP (Cureus 2025) · 8.5 | Excellent trap, but fewer consultants and no hidden history |
| [PMC11890614](https://pmc.ncbi.nlm.nih.gov/articles/PMC11890614/): miliary TB mimicking sarcoidosis, then HLH (Cureus 2025) · 8.5 | Too long and complex for a first case; kept as "hard mode" |
| [PMC12611801](https://pmc.ncbi.nlm.nih.gov/articles/PMC12611801/): Ayurvedic lead poisoning in a child (Front Pediatr 2025) · 8 | Paediatric dosing and a 550-day course complicate a pilot |
| [PMC11227049](https://pmc.ncbi.nlm.nih.gov/articles/PMC11227049/): herbal diabetes medicine, Kerala (EDM Case Rep 2024) · 7.5 | India-set but thin: no MCV, LDH or dated timeline |
| [PMC13089664](https://pmc.ncbi.nlm.nih.gov/articles/PMC13089664/): Kikuchi-Fujimoto disease (Cureus 2026) · 7 | Pathology decides it, but labs are thin and it resolves on its own |

## The case in brief

A 49-year-old woman with inclusion body myositis, on long-term IVIG and recently started on mycophenolate, had three weeks of worsening abdominal pain and lethargy. Haemoglobin had fallen from 127 g/L (three months earlier) to 72 g/L, with a normal MCV (93 fL), reticulocytes 190 ×10⁹/L, bilirubin 29 µmol/L, LDH 339 U/L and haptoglobin 0.20 g/L. The DAT was weakly positive (IgG 1+, C3d negative). The first film report described marked red-cell agglutination, so warm AIHA was presumed. Iron, B12 and folate were replete, and paraprotein, infection and cold-agglutinin work-ups were unremarkable.

A bone marrow aspirate showed dyserythropoiesis, coarse basophilic stippling and ring sideroblasts, plus atypical plasma cells. Re-review of the film then found stippling and Pappenheimer bodies. A revisited exposure history uncovered an unlabelled herbal supplement from a friend. Venous blood lead was 77.8 µg/dL (3.76 µmol/L). She was treated with oral succimer after clinical toxicology advice and recovered. Public health testing confirmed lead in the supplement; mercury and arsenic were also reported.

## What the seats start with

> A 49-year-old woman with inclusion body myositis, on long-term intravenous immunoglobulin, presents with a three-week history of worsening abdominal pain and progressive lethargy.

## Timeline in the article

Day 0 is admission, 13 Jul 2022.

| Day | Event |
| --- | --- |
| −100 | Baseline blood count: Hb 127 g/L, MCV 93 fL |
| 0 | Admission. Hb 72 g/L, reticulocytes 190 ×10⁹/L, DAT IgG 1+ / C3d negative. First film report: marked agglutination |
| 0 | Iron studies, B12/folate, electrophoresis, immunofixation, serology, cold agglutinins, urinary haemosiderin |
| 1–6 | Daily bloods. Hb nadir 64 g/L on day 4; reticulocytes up to 286 ×10⁹/L on day 6; bilirubin falls to 12 µmol/L |
| Not dated | Bone marrow aspirate and iron stain; film re-review; supplement disclosed; blood lead 77.8 µg/dL; succimer started |

The article does not date the marrow, the disclosure or the blood lead. The case file treats them as available whenever ordered during the admission (`day: null`).

## Hidden and conditional facts

| Fact | Released when |
| --- | --- |
| H09 "No known toxin exposure." | Any generic question about toxins, chemicals or exposures |
| H10 "She has recently been taking an unlabelled herbal supplement given to her by a friend." | Only when a seat asks specifically about supplements, herbal, traditional, Ayurvedic or imported medicines, or over-the-counter remedies |

This mirrors the article: the first history recorded no toxin exposure, and the supplement came out only on targeted questioning.

## Raw material for the Pathology Service

| Id | Test | Raw findings the service receives |
| --- | --- | --- |
| R01 | Peripheral blood film (day 0) | Marked red-cell agglutination. Coarse basophilic stippling in a proportion of red cells. Pappenheimer bodies present. |
| R02 | Bone marrow aspirate, MGG | Dyserythropoietic features. Coarse basophilic stippling in erythroid cells. Atypical plasma cells present. |
| R03 | Bone marrow iron stain | Ring sideroblasts present. |

The case file records what the film shows, including the stippling the original team first missed. The service must still notice it, report it and interpret it. In a later image mode, the service receives only the figures (M01–M04) with neutral captions.

## Gaps to fill

The article reports no vital signs or examination and several tests a team might order. The Case Library fills these before play, conditioned on the true diagnosis (Case Library SPEC §6; the full list is in `ANALYSIS.md` §6). Items marked "review" are checked by the Case Reviewer before any player or study run sees them.

| Id | Item | Guidance | Review |
| --- | --- | --- | --- |
| G01 | Vital signs | Afebrile; mild tachycardia; BP normal or mildly raised | review |
| G02 | General examination | Pallor; mild icterus possible; no nodes or organomegaly | review |
| G03 | Abdominal examination | Soft, diffuse mild tenderness, no guarding | review |
| G04 | Lead line on gums | Not seen (do not invent a pathognomonic sign) | review |
| G05 | Neurological examination | Weakness consistent with known inclusion body myositis; no wrist drop | review |
| G06 | IVIG regimen, last infusion | Maintenance; last infusion within four weeks | review |
| G07 | Mycophenolate dose and start | Standard dose, started weeks before admission | review |
| G08 | Occupational and social history | No occupational or hobby lead exposure | review |
| G09 | Renal function, electrolytes, urate | Normal; urate normal or mildly raised | auto |
| G10 | Urinalysis | No haemoglobinuria or proteinuria | auto |
| G11 | Zinc protoporphyrin | Raised | review |
| G12 | Urine ALA and porphobilinogen | ALA raised; PBG not in the acute porphyria range | review |
| G13 | Copper and caeruloplasmin | Normal | auto |
| G14 | Blood mercury and arsenic | Not auto-generated. Case Reviewer sets values | review |
| G15 | Marrow cellularity, iron stores, ring sideroblast %, karyotype | Case Reviewer sets values; karyotype normal | review |
| G16 | Other film features | Polychromasia; no schistocytes or spherocytes | review |
| G17 | Abdominal imaging | No acute pathology; no radio-opaque material | review |
| G18 | Upper GI endoscopy | Normal or non-specific | review |
| G19 | Nerve conduction / EMG | No neuropathy; myopathic pattern of IBM | review |
| G20 | Haemoglobin HPLC | Normal | auto |

## Ground truth and scoring

**Final diagnosis:** lead poisoning from an unlabelled herbal supplement, presenting with abdominal pain and anaemia with coarse basophilic stippling and ring sideroblasts (ICD-10 T56.0, D64.2).

| Score | Meaning for this case |
| --- | --- |
| 5 | Lead poisoning, with the herbal supplement identified as the source |
| 4 | Lead poisoning, source not identified |
| 3 | Heavy-metal poisoning without naming lead, or toxic sideroblastic anaemia without naming lead |
| 2 | Warm AIHA, IVIG-related haemolysis, MDS with ring sideroblasts or drug-induced anaemia |
| 1 | Unrelated, or harmful |

**Must do**

- Ask specifically about supplements, herbal, traditional or imported medicines and over-the-counter products.
- Have the blood film reviewed for basophilic stippling.
- Measure venous blood lead.
- Stop the exposure before or alongside chelation.
- Chelate with oral succimer (symptomatic, blood lead about 78 µg/dL), with clinical toxicology input.
- Notify public health, arrange testing of the product and ask who else took it.
- Plan a repeat blood lead after chelation, because levels rebound.

**Must not do**

- Escalate immunosuppression for presumed warm AIHA on a weak IgG-only DAT in a patient on IVIG without re-evaluating.
- Label myelodysplasia with ring sideroblasts before excluding reversible causes (lead, copper deficiency, alcohol, drugs).
- Chelate while the exposure continues.
- Start empirical iron (iron studies are replete; transferrin saturation 53%).

**Red herrings:** IgG 1+ DAT, film agglutination, cold agglutinin titre 32 with low thermal amplitude, atypical plasma cells, raised polyclonal free light chains, mild transaminase rise, raised CK from myositis.

## What a good run looks like

An illustrative efficient run, not the article's actual course:

1. History: medications (IVIG, mycophenolate) and relevant negatives.
2. Orders: blood count, reticulocytes, haemolysis screen, DAT and blood film.
3. The Pathology Service reports agglutination, coarse basophilic stippling and Pappenheimer bodies, and suggests a blood lead.
4. The Challenger warns against anchoring on AIHA: a weak IgG-only DAT on IVIG may be passive antibody.
5. A targeted question about supplements releases H10.
6. Venous blood lead comes back at 77.8 µg/dL.
7. Clinical toxicology advises stopping the supplement, oral succimer and public health notification.
8. The Attending Physician commits to lead poisoning from the supplement, with a plan covering the must-do items.

Typical failure paths the Evaluator should catch: anchoring on AIHA and escalating immunosuppression; ordering a marrow first and calling it myelodysplasia; asking only a generic toxin question and never uncovering the supplement.

## Case Reviewer checklist

- [ ] Every value in `series` and `single_results` matches Tables 1–5 of the article
- [ ] Day mapping is correct (day 0 = 13 Jul 2022; baseline = day −100)
- [ ] The vignette reveals nothing diagnostic
- [ ] The H10 release condition is acceptable
- [ ] R01–R03 are faithful raw findings with no interpretation
- [ ] Redacted figure captions leak nothing
- [ ] Ground truth, rubric anchors, must-do and must-not-do are agreed
- [ ] Gap guidance agreed; values set for G14 and G15
- [ ] Signed off: freeze as `PMC12949993@v1`

## Starter set (cases 2–5, part of the Case Library's batch 1)

Re-verify each licence on the PMC page during Case Library task L1.2.

| PMCID | Case | Journal, year | Role in the set |
| --- | --- | --- | --- |
| [PMC11227049](https://pmc.ncbi.nlm.nih.gov/articles/PMC11227049/) | Lead poisoning from herbal diabetes medicine, Kerala | Endocrinol Diabetes Metab Case Rep, 2024 | India-set sibling of the pilot; tests generalisation within one diagnosis |
| [PMC12007988](https://pmc.ncbi.nlm.nih.gov/articles/PMC12007988/) | B12 deficiency pseudo-thrombotic microangiopathy | Cureus, 2025 | TTP-mimic anchoring trap; plasma exchange as a must-not-do |
| [PMC11227436](https://pmc.ncbi.nlm.nih.gov/articles/PMC11227436/) | Pseudomicroangiopathy from pernicious anaemia, with gastric biopsy | Cureus, 2024 | Adds a gastroenterology referral and histology |
| [PMC11890614](https://pmc.ncbi.nlm.nih.gov/articles/PMC11890614/) | Miliary TB mimicking sarcoidosis, progressing to HLH | Cureus, 2025 | Hard mode: long course, many services, steroids as the harmful step |

Reserves: [PMC12677959](https://pmc.ncbi.nlm.nih.gov/articles/PMC12677959/) (TB-triggered HLH, Cureus 2025), [PMC11285735](https://pmc.ncbi.nlm.nih.gov/articles/PMC11285735/) (B12 pseudo-TMA with stroke-like onset, Cureus 2024), [PMC13089664](https://pmc.ncbi.nlm.nih.gov/articles/PMC13089664/) (Kikuchi-Fujimoto disease, Cureus 2026).
