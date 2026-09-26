# CLAUDE.md: Nidana

Nidana (निदान, "diagnosis") is a diagnostic simulation game built from real, open-access case reports. Players take a history, examine, order tests with real prices and turnaround times, commit to a diagnosis and a plan, and are scored and debriefed against the published case. It is one Expo app (Android, iOS, web) with a small Next.js game server that runs the engine. Haematology first; the design is specialty-agnostic.

Nidana is one part of Clinical-Case-Sim. Its cases come from the shared Case Library (`../case-library/`); the research simulator Sambhasha (`../sambhasha/`) uses the same cases. Claude Code also loads the umbrella rules in `../CLAUDE.md`. Follow both.

Owner: Dr Atul Tiwari, a pathologist who builds by directing Claude. Explain choices in plain language and keep him in the loop on anything clinical.

This is an educational tool. Nothing it produces is clinical advice.

## Pinned shared-contract versions

- Case bundle schema: **0.3**
- Catalogue: **v2** (Case Library L1.3; pinned in N1.1 on 2026-09-26, because every published bundle except the pilot's first revision is on v2)

The pins are also constants in `packages/contracts/src/versions.ts`.

Upgrade only through a PLAN task, after the changelog entry in `../docs/CHANGELOG.md`.

## Read before any work

1. `../docs/CHANGELOG.md`: deal with any open item for Nidana first.
2. `docs/DECISIONS.md`: Nidana's decisions (shared ones are in `../docs/DECISIONS.md`).
3. `docs/SPEC.md`: the design source of truth. Names are in §1 and invariants in §2.
4. `docs/PLAN.md`: tasks with acceptance criteria. Work in order.
5. `../case-library/docs/SPEC.md` for the bundle format, catalogues and the condition vocabulary.
6. `../case-library/cases/PMC12949993/ANALYSIS.md`: the pilot analysis. It contains spoilers, so never put its content in player-facing code, UI text or anything a player can see.

## Invariants (never violate; tests enforce them)

1. The answer never reaches the player's device. The engine runs on the game server; bundles, ground truth, rubrics, test utility and origins stay there; nothing case-specific ships inside the app.
2. Players act only through catalogue items, and the engine releases stored text only. Nothing is generated during play (the future voice mode has one written exception, SPEC §11.4).
3. Nidana loads only exported bundles.
4. Origins are hidden during play and shown in the debrief.
5. The action log is append-only, and every encounter records its bundle revision.
6. The same bundle revision and the same actions give the same releases and the same score.
7. Nidana never writes to the Case Vault. There is no Supabase MCP in this folder, and `.claude/settings.json` denies the account-level Supabase connector (set up in Case Library task L0.2). Changes to the `play` schema are proposed as migration files in `supabase/proposed/`; a Case Library session applies them to the development project.
8. Store builds carry only production-eligible cases and cleared figures.

## Names (exactly these)

| Name | Code id or form |
| --- | --- |
| Player app, game server | `apps/player`, `apps/server` |
| Engine, contracts | `@nidana/engine`, `@nidana/contracts` |
| Player, encounter | `player`, `encounter` |
| Seats | `attending`, `service.pathology` |
| Case version, bundle | `PMC12949993@v1`, `PMC12949993@v1.r1` |
| Catalogue ids | `HX.*`, `EX.*`, `LAB.*`, `IMG.*`, `PROC.*`, `CMP.*`, `RX.*`, `ACT.*`, `REF.*`, `DX.*` |
| Report status | `provisional`, `final` |

British spelling in user-facing text ("haematology", "anaemia").

## Stack

- Player app: Expo (React Native) with Expo Router and NativeWind; EAS Build for store binaries.
- Game server: Next.js (App Router) route handlers only; the only public server.
- Engine: `packages/engine`, pure TypeScript functions, imported only by the server.
- Data: development uses the `play` schema in the Case Vault's Supabase project, through a least-privilege role; the store release uses self-hosted Supabase on the VPS.
- Validation: Zod (contracts generated from the bundle schema).
- Tests: Vitest with `@vitest/coverage-v8`, fast-check, Playwright (web build), Maestro (Android and iOS).
- Quality: ESLint with `@eslint/js` and `typescript-eslint`, Prettier, pre-commit, GitHub Actions; `@types/node` for TypeScript (approved by Atul, 2026-09-26).

## Commands (created in N1.1–N1.5; until then they don't exist)

Run these from `nidana/`:

```bash
pnpm install
pnpm --filter "./**" --fail-if-no-match run lint      # engine, contracts, apps
pnpm --filter "./**" --fail-if-no-match run typecheck
pnpm --filter "./**" --fail-if-no-match run test
pnpm --filter @nidana/server dev                      # the game server, locally
pnpm --filter @nidana/player start                    # the Expo app (press w for web)
```

## Conventions

- Type everything. Contracts are generated from the Case Library's bundle schema; never hand-edit them.
- Configuration over code: scoring weights and difficulty settings live in `configs/`; prices, turnaround and reference ranges come from the catalogue.
- Never put a PMCID, DOI, article title or diagnosis in a link, a screen title or any response before the debrief.
- Keep commits small, in conventional-commit style, one PLAN task per branch.

## Testing

- Write each task's acceptance tests first.
- Engine tests use bundle fixtures and conformance playthroughs in `conformance/`. No network access and no paid API calls in tests or CI.
- Leak tests scan every encounter response (SPEC §6.4).
- Never skip, weaken or delete an invariant or leak test to make a change pass. Ask Atul instead.

## Working agreement

- **Start of a session:** check `../docs/CHANGELOG.md`; then open `docs/PLAN.md`, pick the first unchecked task whose dependencies are done, and state it with its acceptance criteria.
- **End of a task:** run lint, type-check and tests, tick the box in `docs/PLAN.md` with a one-line note, and summarise for Atul in plain words.
- **Ask Atul before:**
  - changing an agreed decision or an invariant;
  - anything that needs a shared-contract change (it happens in a Case Library session);
  - adding a dependency not listed above;
  - anything that costs money (store accounts, paid APIs, hosting);
  - anything touching licences or testers' data.
- **[human] tasks:** prepare the materials (builds, screenshots, summaries), tell Atul exactly what to check, and continue with other tasks.
- **Secrets:** never commit them. `.env` is git-ignored; `.env.example` lists the keys.

## Out of scope for now

- Any language model at play time before Phase 5; MedGemma or any local model.
- Simulated treatment responses, multiplayer, payments, offline play.
- Specialties other than haematology until milestone NM2.
