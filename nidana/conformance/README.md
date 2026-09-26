# Conformance

Scripted playthroughs with expected outcomes, and the pinned catalogue they run against. They contain case answers: server-side and tests only, never in the player app.

- `catalogue/catalogue.v2.json`: the catalogue export pinned in `nidana/CLAUDE.md`, built from the Case Library's CSV files with `cd case-library && uv run python -m scripts.catalogue build --version 2 --out <path>` on 2026-09-26 and formatted by Prettier. Replace it only when the pin moves.
- `<case>/`: playthroughs for one case, run by `@nidana/engine`'s tests. Each file lists actions and the releases, values and totals expected after them. Sambhasha can later run the same files.
