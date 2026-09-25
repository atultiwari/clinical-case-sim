# Umbrella plan

Each part has its own PLAN. This file holds the umbrella tasks and the order in which the parts' milestones unlock one another.

## Umbrella tasks

- [ ] **U0.0 Git and the private GitHub repository**
  - Build: in the first Claude Code session, started at `Clinical-Case-Sim` with the prompt in [SESSION_PROMPTS.md](SESSION_PROMPTS.md): check that git and the GitHub CLI (`gh`) are installed and signed in, that the folder is not inside another Git repository, and that no repository named `clinical-case-sim` exists yet; review the root `.gitignore`; scan for secrets and large files; `git init -b main` and a first commit on `main`; create the private GitHub repository `clinical-case-sim` with `gh repo create --private` and push. From then on, the Git and GitHub section of [`../CLAUDE.md`](../CLAUDE.md) applies.
  - Accept: `gh repo view` reports visibility `PRIVATE`; `main` is level with `origin/main`; no tracked file matches `.gitignore` (`git ls-files -ci --exclude-standard` prints nothing); the scan found no secret.
  - Depends on: S-005.

- [ ] **U0.1 Monorepo scaffold**
  - Build: on the branch `umbrella/U0.1-monorepo-scaffold`: a root `package.json` and `pnpm-workspace.yaml` listing `nidana/apps/*`, `nidana/packages/*` and `case-library/studio`; a root `.pre-commit-config.yaml` with the changelog guard, a secret scanner and basic file checks (large files, merge-conflict markers); a contract workflow in `.github/workflows/` that runs the changelog guard now and gains the bundle checks once the schema and exports exist (`docs/REPOSITORY.md`). Each part's first build task (Case Library L0.1, Nidana N1.1, Sambhasha P0.1) adds that part's project files, its hooks in the root pre-commit config and its own workflow.
  - Accept: on a fresh clone, `pnpm install` and `pre-commit run --all-files` succeed; a commit that changes a file under `case-library/schemas/` or `case-library/catalogue/` without changing `docs/CHANGELOG.md` is blocked by the hook, and a pull request with such a change fails the contract workflow.
  - Depends on: U0.0. Do this before any part's first build task.

- [ ] **U1.1 Research release export**
  - Build: `scripts/export_research_release.py` with the allow-list in `docs/REPOSITORY.md`; checks for secrets, player data and licences; a dry-run report.
  - Accept: a dry run lists exactly the allowed files; an ND case or a held-out case in the input is refused.
  - Depends on: Sambhasha milestone M2 (the study). Must finish before Sambhasha's M4 (submission), so the paper can cite the DOI.

## Order of milestones

| Milestone | Part | Unlocks |
| --- | --- | --- |
| Case Library LM0: pilot bundle `PMC12949993@v1.r1` frozen | Case Library | Nidana Phase 1; Sambhasha P0.6 and Phase 1 |
| Nidana NM1: pilot playable in the development game | Nidana | Nidana Phase 2 |
| Case Library LM1: ten cases frozen | Case Library | Nidana's development beta (NM2); Sambhasha's starter runs |
| Sambhasha M1: pilot runs end to end | Sambhasha | Sambhasha's study (M2) |
| Case Library L2.1 and Nidana's production database, both done | Case Library, Nidana | Nidana's store release (NM4) |
| Sambhasha M2: study complete | Sambhasha | U1.1, the research release |
| U1.1 done | Umbrella | Sambhasha M4: paper submitted, citing the release DOI |
