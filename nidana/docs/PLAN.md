# Nidana: implementation plan

How to use this file: work top to bottom. Pick the first unchecked task whose dependencies are done, restate its acceptance criteria, write the tests first, then build. When it passes, tick the box and add a one-line note (date, what changed). Tasks marked **[human]** need Dr Atul Tiwari: prepare everything he needs, tell him exactly what to check, and move on to the next task you can do.

Design: [SPEC.md](SPEC.md). Decisions: [DECISIONS.md](DECISIONS.md). Cases: the Case Library ([`../../case-library/docs/PLAN.md`](../../case-library/docs/PLAN.md)); its milestone LM0 (the pilot bundle) gates Nidana's acceptance tests. Umbrella order of milestones: [`../../docs/PLAN.md`](../../docs/PLAN.md).

Version 0.1 of this plan also held the Case Vault tasks; they are now the Case Library's L0.x and L1.x.

## Milestones

| Milestone | Done when |
| --- | --- |
| NM1 | The pilot is playable end to end in the Attending seat (web build and an Android development build), deterministic, with no leaks, and Atul has played it at all three difficulties |
| NM2 | Ten cases are playable and 5–10 testers have played them in a development beta |
| NM3 | The Pathology seat is live on at least three cases |
| NM4 | Nidana is released on the Play Store and the App Store, on its own production database |
| NM5 | Free-form voice consultation is live |

Rough effort: Phase 1 three to four weeks (two apps: player and server), Phase 2 two to three weeks. Atul's review time in the Case Library is the main variable.

---

## Phase 1: the game (Attending seat, deterministic)

- [x] **N1.1 Contracts**
  - Done 2026-09-26: `@nidana/contracts` generates Zod validators and types from schema 0.3, validates the catalogue export (v2 checked by hand) and reports every problem with its path; the fixture and all 11 exported bundles validate, the pilot's `r2` included, after Case Library L1.7 corrected the schema; Nidana's workflow and Prettier hook added; catalogue pinned at v2.
  - Build: `packages/contracts` with TypeScript types and Zod validators generated from `../case-library/schemas/case-bundle.v0.3.schema.json`; the catalogue export format; a hand-made fixture bundle for tests until the pilot bundle exists. Record the pinned versions (schema 0.3, catalogue v2; v1 before the catalogue v2 changelog entry) in `nidana/CLAUDE.md`. Add Nidana's hooks to the root `.pre-commit-config.yaml` and its GitHub Actions workflow (lint, type-check, tests), limited to `nidana/`.
  - Accept: the fixture validates; an invalid bundle (missing licence, unknown origin) is rejected with a clear message; once LM0 is reached, the pilot bundle validates too.
  - Depends on: umbrella U0.1; Case Library L0.3 (the schema).

- [x] **N1.2 Engine core**
  - Done 2026-09-26: `@nidana/engine` with `prepareCase`, `applyAction` and `replay` (a pure fold), the condition vocabulary (Case Library SPEC §10.4, both forms of `finding_released`), difficulty settings in `configs/difficulty.json`, the pinned catalogue snapshot and the pilot's benchmark playthrough (on `PMC12949993@v1.r3`) in `conformance/`. Every acceptance item below passes, including carry-forward; every current bundle answers every Attending item; property tests with fast-check. SPEC §5.4 updated: orders take no time, budget-exceeding orders are refused, and the SPEC's 24-hour carry-back rule is replaced by the Case Library's carry-forward.
  - Build: `packages/engine` with `replay(bundle, actions)`: clock, day buckets and carry rules, release by `released_by`, orders with turnaround and INR cost, report variants and status by difficulty, referrals with consult note conditions, limits and forced commit.
  - Accept (pilot conformance playthroughs, once LM0 is reached):
    - Current medicines releases H03 and H04 and not H10; a toxin question releases H09 only; the remedies question releases H10.
    - A blood count ordered on day 0 shows Hb 72; ordered on day 4 it shows Hb 64.
    - A blood lead appears only after its turnaround, at 77.8 µg/dL.
    - Standard mode gives the provisional film report with its status line; the film review gives the final report; Guided mode gives the final report first.
    - Costs add up; the same actions give an identical state.
    - An order on a day with no value for a component returns the latest earlier value, marked with its day ("result from day 0"); a value with no day holds throughout (changelog entry of 2026-09-25, schema 0.3 carry-forward; Case Library SPEC §10.2).
  - Depends on: N1.1.

- [x] **N1.3 Scoring and debrief**
  - Done 2026-09-26: the commit action (diagnosis, up to five released items as evidence, a plan of actions and referrals); `scoreEncounter` with the components of SPEC §7 (rules written out there) and weights in `configs/scoring.json`; `buildDebrief` with the paths compared, origins revealed, provisional and final reports paired, figures, key discriminators, teaching points and attribution. All five acceptance items pass on `PMC12949993@v1.r3`; the benchmark path scores 94.9 (98.9 with a differential holding the diagnosis). The conformance playthrough now checks the score too. Note for the Case Library: the pilot's `teaching_points` and `efficient_path` are empty in its ground truth.
  - Build: the condition evaluator (Case Library SPEC §10.4), component scores, the safety cap, `configs/scoring.yaml`, and the debrief payload (paths compared, origins revealed, provisional and final reports side by side, teaching points, attribution).
  - Accept (pilot):
    - The benchmark path (`ANALYSIS.md` §10), citing the supplement (H10) as evidence, scores diagnosis 5 with every must-do met.
    - The same path without citing H10 scores diagnosis 4.
    - A plan with high-dose steroids registers a must-not-do and triggers the cap.
    - A player who asks only the generic toxin question never releases H10 and cannot score 5.
    - Committing to MDS with ring sideroblasts without a blood lead or copper scores 2 with a violation.
  - Depends on: N1.2.

- [x] **N1.4 Game server**
  - Done 2026-09-26: `apps/server` (Next.js 16, route handlers only) with the SPEC §6.2 endpoints plus `GET /api/cases`; the PlayerView with per-encounter chart references; bundle checks (SHA-256, re-derived from the Case Vault's jsonb with RFC 8785; schema and catalogue pins; newest published revision per case); Supabase Auth tokens checked with `jose`; per-player rate limits; the `{ success, data, error }` envelope. Proposed migration `supabase/proposed/20260926190000_play_schema.sql` (the `play` tables, role `nidana_server`, RLS, an insert-only action log), tested on the local Case Vault inside a rolled-back transaction: the server role reads published bundles only, and `anon` and `authenticated` cannot read `casevault` or `play`. Leak tests scan every encounter response on the benchmark path, in Guided mode and on random action sequences. Open: a Case Library session applies the migration to the development project and Atul creates the login role; figures need their endpoint (with N1.5). Follow-ups from the security review, before the store release: rate limits live in one process (move them to the database if the server ever runs as several); the database policies trust `nidana_server` for all rows, so per-player isolation rests on the server's ownership check (add a per-request player setting to the policies with the production database).
  - Build: `apps/server`, Next.js route handlers from SPEC §6.2; a proposed migration in `supabase/proposed/` for the `play` tables (SPEC §8.2), which a Case Library session applies to the development project; a least-privilege database role that reads published bundles and writes `play`; bundle version and hash checks; auth checks and rate limits.
  - Accept: the leak tests in SPEC §6.4 pass on every encounter endpoint; a client using the public key cannot read `casevault` or `play` tables; a bundle with an unsupported schema or catalogue version, or a wrong hash, is refused.
  - Depends on: N1.3.

- [x] **N1.5 Player app**
  - Done 2026-09-27: `apps/player` (Expo SDK 57, Expo Router, NativeWind 4): home, case card, workspace (Chart as a day-by-day timeline with result tables, trends and an SI/conventional toggle; Ask, Examine, Order with price and turnaround, Refer, Differential, Wait, Commit), commit and debrief; Provisional and Final badges with the status line; the disclaimer fixed on every screen; tabs on phones, side by side from 900 px; anonymous Supabase sign-in (Atul enabled it on the Case Vault project). Shared API types in `@nidana/contracts/api`; the server gained CORS and a debrief keyed by Chart references. Playwright plays the benchmark path on the web build (also in CI) and Maestro on an Android development build (emulator `nidana`, real sign-in); both reach diagnosis 5 with all 7 must-dos. Screenshots at phone, tablet and desktop sizes sent to Atul. Needed on the Mac: Java 17 (Homebrew) for Android builds and Maestro.
  - Build: `apps/player`, an Expo app with Expo Router and NativeWind: home, case card, workspace (Chart, Ask, Examine, Order, Refer, Differential, Wait, Commit), results with trends and a units toggle, commit (diagnosis, evidence, plan) and debrief screens; Provisional and Final badges; the disclaimer on every screen. Phone layout with tabs; side-by-side on tablets and the web.
  - Accept: a Playwright test completes the benchmark path on the web build; a Maestro test does the same on an Android development build; screenshots at phone, tablet and desktop sizes go to Atul.
  - Depends on: N1.4.

- [ ] **N1.6 Accounts and credits**
  - Build: Supabase Auth in the app with pseudonymous accounts (anonymous sign-in, or an invite code and a nickname), a consent screen, `admin` and `player` roles, a minimal profile (nickname, training level) and a credits page with every case's attribution.
  - Accept: a tester can join without a real name or email, play, and see only their own encounters.
  - Depends on: N1.4.

- [ ] **N1.7 Missing requests**
  - Build: log unmatched searches in `play.missing_request` (bundle id, kind and query text; no player identity) through the game server. The Case Library picks them up (Case Library SPEC §4.4).
  - Accept: an unmatched search is logged with the bundle id and query text, costs nothing and shows the no-match message; the row holds nothing that identifies the player.
  - Depends on: N1.5.

- [ ] **N1.8 [human] First play**
  - Build: deploy the game server and the web build to Coolify (staging) against the development database; make an Android development build; Atul plays the pilot at all three difficulties; Claude fixes what he finds.
  - Accept: Atul signs off the pilot experience. Milestone NM1.
  - Depends on: N1.5, N1.6, N1.7; Case Library LM0.

---

## Phase 2: ten cases and a development beta

- [ ] **N2.1 Load batch 1**
  - Build: play-test the nine new bundles from the Case Library's batch 1 with scripted conformance runs; report any engine or content problem to a Case Library session.
  - Accept: every bundle loads, its benchmark path scores as its analysis predicts, and the leak tests pass.
  - Depends on: NM1; Case Library LM1.

- [ ] **N2.2 [human] Development beta**
  - Build: 5–10 testers (for example pathology residents) with pseudonymous accounts play at least three cases each, after consent; a short feedback form; completion, score and missing-request reports. CC BY-NC cases may be included and are labelled "Development only" for Atul; ND cases stay in Atul's own testing and are not shown to testers.
  - Accept: a findings note for Atul with the changes proposed. Milestone NM2.
  - Depends on: N2.1.

---

## Phase 3: the Pathology seat (outline)

- A morphology findings catalogue (for example coarse basophilic stippling, Pappenheimer bodies, agglutination, spherocytes, schistocytes, polychromasia) and an impression catalogue, added to the Case Library (a shared-contract change).
- The Pathology seat screen: requisition, figures as published during development, findings, impression, reflex tests.
- Scoring against the final report: key findings, false findings, suggested tests.
- Live on at least three cases. Milestone NM3.

## Phase 4: store release (outline)

- Atul's production gate: for each case, confirm `production_ok`; for each figure, decide use, mask or exclude (in the Case Studio).
- The production database on the VPS (self-hosted Supabase on Coolify, no MCP) with `play` and published bundles; the Case Library's publish job (L2.1); nightly backups.
- Delete development test data; switch sign-in to the release model (minimal data, consent); in-app account deletion.
- If the Play developer account is a new personal account, run a closed test with at least 12 testers for 14 days before applying for production access (an organisation account for Vedant Research Labs avoids this but needs a D-U-N-S number).
- Privacy policy, the Play Store data-safety form and App Store privacy details; store listings; EAS builds; submission. Milestone NM4.

## Phase 5: free-form voice consultation (outline; design in SPEC §11)

- 5a typed free text: router (catalogue actions, or conversation) and patient model in text; confirmation chips; a draft plan from spoken treatment advice; missing requests from the router; a way to report offensive AI output (Play policy).
- 5b voice: speech-to-text and text-to-speech; push-to-talk; latency under 2.5 seconds median.
- 5c examiner feedback with the rubric in SPEC §11.6, calibrated against Atul's ratings; the Guided-mode tutor, which sees only the PlayerView.
- 5d Hindi and Hinglish, with reviewed Hindi lay texts from the Case Library.
- Release tests from SPEC §11.10. Milestone NM5.
