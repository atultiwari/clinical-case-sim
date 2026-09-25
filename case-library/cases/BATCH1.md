# Batch 1: the nine cases

Task L1.2 · Case Library · 25 Sep 2026

> Spoiler warning. The shortlist this draws on (`SHORTLIST-batch1.md`) names the diagnoses. This file lists case ids only, but it is still for the Case Reviewer and developers, never for a player or a seat. Educational and research use only; nothing here is clinical advice.

## Decision

Atul delegated this choice to Claude on 25 Sep 2026 ("take decisions & actions on my behalf and document"). Claude chose the five highest-scoring report-based candidates on the shortlist, all CC BY 4.0. Atul can swap any of them before curation starts (L1.3); nothing has been written to the Case Vault for them.

| # | Case | Source | Licence (re-verified 25 Sep 2026) | production_ok | public_release_ok | Shortlist score |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | PMC11227049 | Sambhasha starter | https://creativecommons.org/licenses/by/4.0/ | Yes | Yes | starter |
| 2 | PMC12007988 | Sambhasha starter | https://creativecommons.org/licenses/by/4.0/ | Yes | Yes | starter |
| 3 | PMC11227436 | Sambhasha starter | https://creativecommons.org/licenses/by/4.0/ | Yes | Yes | starter |
| 4 | PMC11890614 | Sambhasha starter | https://creativecommons.org/licenses/by/4.0/ | Yes | Yes | starter |
| 5 | PMC12364935 | Shortlist #1 | https://creativecommons.org/licenses/by/4.0/ | Yes | Yes | 9 |
| 6 | PMC13193864 | Shortlist #2 | https://creativecommons.org/licenses/by/4.0/ | Yes | Yes | 8.5 |
| 7 | PMC12643702 | Shortlist #3 | https://creativecommons.org/licenses/by/4.0/ | Yes | Yes | 8 |
| 8 | PMC11015937 | Shortlist #4 | https://creativecommons.org/licenses/by/4.0/ | Yes | Yes | 7.5 |
| 9 | PMC13400839 | Shortlist #5 | https://creativecommons.org/licenses/by/4.0/ | Yes | Yes | 7.5 |

**Licence re-verification.** PMC's Open Access web service (`oa.fcgi`) still returned an error page on 25 Sep 2026, so each licence was read again from the article's JATS `<license>` element, fetched through E-utilities and cached under `data/articles/<PMCID>/`. The curation skill checks the licence once more at step 2 before any import.

## Answers to the shortlist's questions

1. **Licence source:** the JATS licence element is accepted when the OA service is down; step 2 of the skill re-checks it at curation time.
2. **Development-only reports (CC BY-NC-ND):** not in batch 1. Batch 1 feeds Nidana's production release, and these can never be released. They stay in reserve for internal testing.
3. **Theme balance:** keep shortlist #5 (folate deficiency with a marrow that mimics a myeloid neoplasm) over #6 (POEMS). It has the stronger pathology hinge and reuses the pilot's marrow items; POEMS is the first reserve.
4. **De novo cases (NID-0001, NID-0002):** not in batch 1. They need a de novo path in the curation skill (SPEC §4.4 assumes an article) and a reviewer value for every row; they are proposed for batch 2.

## Reserves, in order

PMC13558013 (#6), PMC13417352 (#7), PMC12611801 (#8).
