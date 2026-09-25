# Decisions

Status as of 25 Sep 2026: every entry is **agreed** by Dr Atul Tiwari, with the changes he asked for recorded below. Change an agreed decision only with his explicit approval, as a new entry that supersedes the old one. Decisions shared with the Case Library and Sambhasha live in `../../docs/DECISIONS.md` (S-numbers); entries marked "Shared" point there.

Supersedes the HemoSim plan ([archive/HemoSim_Planning.md](archive/HemoSim_Planning.md)).

| Id | Decision | Why | Status |
| --- | --- | --- | --- |
| N-001 | The product is called **Nidana** (निदान, "diagnosis" or "root cause"). Code id `nidana`. It is not limited to haematology. | "HemoSim" tied the product to one specialty; Nidana pairs with the Sushruta atlas. Before launch, check domains and trademarks: the word is strongly linked to Ayurveda (Madhava Nidana), and a company called Nidana Technologies exists. | Agreed |
| N-002 | One shared case library feeds Nidana and Sambhasha. | Curate and review once. | Agreed. Shared: S-002 |
| N-003 | Claude curates cases through the Supabase MCP under a versioned skill; no copy-paste stage, no API pipeline, no MedGemma for now. | Claude can already reach Supabase. | Agreed. Shared: S-002 and the Case Library SPEC §4 |
| N-004 | Pre-generate everything a player can ask for, flag what is synthetic, and have Atul review in batches (about ten cases; the pilot on its own first). New needs are added on request. | No model runs while a student plays; nothing unreviewed reaches a student. | Agreed. Now in the Case Library SPEC §6–§7 |
| N-005 | Haematology first, with a specialty-agnostic design. Stay in haematology until ten cases are live and played; include common presentations. | Atul can review haematology confidently; case reports skew towards rare cases. | Agreed |
| N-006 | **Catalogue-first play.** Every player action is an item from the shared catalogues; in v1, free text is only a search box. | Makes full pre-generation, deterministic release and scoring possible. | Agreed for v1. Free-form voice comes later (N-021) |
| N-007 | Tiered origins (`article`, `derived`, `affected`, `normal`, `rule`, `reviewer`): Atul approves `affected` values one by one and the `normal` list as a list. | Review time goes where judgement is needed. | Agreed. Now in the Case Library SPEC §6.2 |
| N-008 | **The answer never reaches the player's device.** The engine runs on the server; opaque slugs, neutral titles; the citation appears only in the debrief. | Anything sent to a device can be read. | Agreed |
| N-009 | **Deterministic engine and scoring in v1.** No language model runs during play. | Safe, free to run, reproducible. | Agreed for v1. The AI layer comes later (N-021) |
| N-010 | The engine is a pure function of a case bundle and the player's actions; the bundle is the contract with the Case Library. | Easy to test and replay; one format for both projects. | Agreed |
| N-011 | Frozen case versions are immutable; later coverage creates new bundle revisions; encounters record the revision they used. | The catalogue can grow without breaking comparability. | Agreed. Now in the Case Library SPEC |
| N-012 | ~~Two databases from the start.~~ **One development database until the store release**; the production database on the VPS is created before the store release. | Atul: everything before the store release is development. | Changed. Shared: S-007 |
| N-013 | ~~No CMS in v1.~~ **A basic Case Studio** for viewing and accessing cases during development; no production CMS. | Atul: a development CMS makes cases easier to view and access. | Changed. Shared: S-008 |
| N-014 | **Provisional and final reports.** An interpretive test can carry the report as first issued and the report after expert review. A provisional report always shows a Provisional badge and a status line saying it is not final and that a review can be requested, so a player never takes it for the final report. | The pilot's real pitfall becomes playable without misleading players. | Agreed, with Atul's condition (SPEC §5.8) |
| N-015 | ~~Masked figures outside Guided mode.~~ **Every figure, whatever its licence or annotations, is included during development.** Atul decides per figure (use, mask or exclude) before the store release. Never generate medical images with AI. | Atul: he will review every case manually before production. | Changed. Shared: S-006 |
| N-016 | Scoring follows Sambhasha's structure: 5-point diagnosis anchors, must-do and must-not-do rules, test utility, cost in INR and simulated time; weights in `configs/scoring.yaml`. | One scoring language for the game and the benchmark. | Agreed |
| N-017 | ~~Game uses CC0 and CC BY only.~~ **CC BY-NC and ND cases are included during development**, marked "Development only" in the tables and the Case Studio; the store release uses production-eligible cases only. | Atul: more cases help testing (his note said N-016; applied here to the licence decision). | Changed. Shared: S-006 |
| N-018 | ~~Next.js game.~~ Stack: an Expo player app, a Next.js game server, the TypeScript engine; see N-022. | The store release needs native apps. | Superseded by N-022 |
| N-019 | British spelling in user-facing text; values stored as reported (SI) with a display toggle for conventional units (g/dL, mg/dL). | Consistent with Sambhasha; familiar units for Indian learners. | Agreed |
| N-020 | **Pathology seat** is a planned mode (Phase 3): the player reads the film or marrow and writes the report. | Nidana's point of difference, and Atul's own teaching area. | Agreed |
| N-021 | **Free-form voice consultation** (Phase 5): students talk to the patient by voice or text (English, Hindi, Hinglish), request tests and procedures and advise treatment; a router maps what they say to catalogue actions, a patient model speaks only released facts, and an AI examiner gives feedback after the case. The deterministic score stays the score of record. Design: SPEC §11. | Atul's idea, refined so that the model that talks never holds the answer. | Agreed direction; built after the core game |
| N-022 | **Expo player app for Android, iOS and the web, and a Next.js game server** that runs the engine. The engine is imported only by the server. | Atul's choice: one codebase for the store release and web testing. | Agreed |

## Open items (not blocking Phase 1)

- Scoring weights; tune after the development beta.
- Whether Guided mode lets players browse full question and test lists, or only search.
- Domain and trademark check for "Nidana" (classes 9 and 41) and a tagline that makes the modern-medicine positioning clear.
- Voice mode: free within a daily quota, or a paid tier; cloud or self-hosted speech models (SPEC §11.9).
- Pricing and access model for the store release.
