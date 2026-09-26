# CLAUDE.md: Clinical-Case-Sim

This folder holds three parts built around one shared library of real, open-access case reports.

| Folder | Part | What it is |
| --- | --- | --- |
| `case-library/` | Case Library | The shared Case Vault: database schema, catalogues, the curation skill, the Case Studio and the exported case bundles |
| `nidana/` | Nidana | The teaching game: an Expo app for students and a small game server |
| `sambhasha/` | Sambhasha | The research simulator, formerly the Virtual Diagnostic Team (VDT): AI doctor seats work up hidden cases for a benchmark and a paper |

Owner: Dr Atul Tiwari. Claude Code loads this file in every session started inside any of these folders, so these rules apply everywhere. Educational and research tools only: nothing here is clinical advice.

## Read first

1. `docs/DECISIONS.md`: the decisions shared by all three parts (S-numbers).
2. `docs/CHANGELOG.md`: shared-contract changes, and whether each part has acknowledged them.
3. The `CLAUDE.md` of the part you are working in.

## Rules

1. **One part per session.** Start Claude Code in the folder of the part you are changing, and say at the start which part it is. The one exception is an approved shared-contract change (rule 3): it starts in `case-library/` and may update the other parts in the same branch.
2. **Stay in your part.** Do not edit another part's files, except to carry out a shared-contract change that Atul has approved (rule 3). In the shared root files (`.gitignore`, `pnpm-workspace.yaml`, `.pre-commit-config.yaml` and `.github/workflows/`), change only your own part's entries and workflow.
3. **The shared contract changes only through the Case Library.** The contract is the case bundle format and its schema version, the catalogue ids and their patterns, the origin labels, the licence flags, the price and turnaround tables, and the scoring structure (rubric anchors and must-do and must-not-do conditions). A change needs Atul's approval and a new entry in `docs/CHANGELOG.md` with a version bump. For each of Nidana and Sambhasha, the entry needs either the matching change in the same branch or an open acknowledgement item.
4. **Acknowledge before anything else.** At the start of a session in `nidana/` or `sambhasha/`, read `docs/CHANGELOG.md`. If an entry has an open item for this part, deal with it first (update, pin, or record why not) and tick it with a note.
5. **Pins.** Each part records, in its own CLAUDE.md, the bundle schema version and the catalogue version it supports. Upgrading is an explicit task in that part's PLAN.
6. **Database writes.** Only Case Library sessions can use Supabase: the account-level connector, limited to the Case Vault by `case-library/.claude/settings.json` and its hook; the account-level Supabase connector is denied in `nidana/.claude/settings.json` and `sambhasha/.claude/settings.json` (set up in Case Library task L0.2). Nidana and Sambhasha never write to the Case Vault. The development Supabase project keeps one migration history, in `case-library/supabase/migrations/`: Nidana proposes changes to its `play` schema as migration files, and a Case Library session applies them.
7. **This repository is public; production and held-out cases never enter it** (S-010). Everything committed here is public, including the diagnoses in the current cases' bundles, analyses and conformance files. So those cases are for building and testing only: they never go into Nidana's store release, and never count as held-out or primary-result cases in a Sambhasha study. Cases for production and for a study are curated as a new set and kept outside this repository, somewhere private chosen before curation starts. They reach the public only through the research release (`docs/REPOSITORY.md`). Case answers never go into the prompt of a model under test, whichever set they come from.
8. **Names:** Clinical-Case-Sim, Case Library, Case Vault, Nidana, Sambhasha, exactly as written. British spelling in user-facing text.
9. **Secrets** are never committed. Each part keeps a `.env.example`.

## Git and GitHub

The umbrella is one public Git repository, `clinical-case-sim` on GitHub (S-010, `docs/REPOSITORY.md`). Keep GitHub in step with this folder:

- **Start of a session:** run `git status`. If there are changes that no session made (Atul may edit files himself), show them to Atul and ask before committing or discarding them. Then run `git fetch` and `git pull --rebase` on the branch you are on (`main`, or a task branch you are continuing).
- **One branch per PLAN task,** started from an up-to-date `main` and named `<part>/<task-id>-<short-name>`, for example `case-library/L0.3-schema` or `umbrella/U0.1-monorepo-scaffold`. Only U0.0's commits go straight to `main`.
- **Commit** after each working step: small commits with conventional-commit messages, for example `feat(case-library): add the ledger trigger`. Look at `git status` first, so that nothing ignored or secret goes in.
- **Push** after every commit, and always before a session ends. If a push fails, tell Atul; never end a session with unpushed work without saying so.
- **Merge** when the task's acceptance criteria pass and its box is ticked: open a pull request with `gh pr create`, wait for the checks once CI exists (U0.1), then run `gh pr merge --squash --delete-branch`, switch to `main` and pull. For a **[human]** task, merge after Atul has done his part.
- **One session at a time** in this repository, because Git has one checked-out branch per working folder. A second session running at the same time needs its own git worktree.
- **Not in Git:** secrets and `.env` files, review packs, raw downloads and run data (`data/`), case figures (they live in the `case-media` bucket), player or tester data, and any production or held-out case (rule 7). Keep every file under 50 MB. Before each commit, remember it is public.
- **Ask Atul first** before force-pushing, rewriting history that has been pushed, running `git reset --hard`, `git clean` or `git checkout -- .`, dropping a stash, deleting a branch whose pull request has not been merged, changing the repository's visibility or settings, or adding a remote.
- If a pull, rebase or merge hits a conflict, stop and explain it to Atul in plain words before resolving it.

## Where to start a session

| Work | Start Claude Code in |
| --- | --- |
| Curating and reviewing cases, catalogues, the Case Studio | `case-library/` |
| The game: player app, game server, engine | `nidana/` |
| Research runs, the study, the paper | `sambhasha/` |
| Repository set-up, CI, the research release | this folder |
