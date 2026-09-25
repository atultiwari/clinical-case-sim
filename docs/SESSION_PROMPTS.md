# Session prompts

Prompts for starting Claude Code on Clinical-Case-Sim. The rules every session follows are in [`../CLAUDE.md`](../CLAUDE.md), including its Git and GitHub section.

## Before the first session

Install the GitHub CLI and sign in to GitHub once, in the Terminal app:

1. `brew install gh` (or download it from cli.github.com).
2. `gh auth login`: choose GitHub.com, then HTTPS, answer yes to authenticating Git with your GitHub credentials, and log in with a web browser.

## First session (once): umbrella tasks U0.0 and U0.1

Start Claude Code in the `Clinical-Case-Sim` folder (in Terminal: `cd ~/Projects/research/Clinical-Case-Sim` and then `claude`; in the desktop app, choose that folder) and paste:

```text
This is the first Claude Code session for Clinical-Case-Sim. It is umbrella work at the root folder: repository set-up (see "Where to start a session" in CLAUDE.md).

Read CLAUDE.md, then docs/DECISIONS.md, docs/REPOSITORY.md, docs/CHANGELOG.md and docs/PLAN.md. Then do umbrella tasks U0.0 and U0.1, in that order.

U0.0: Git and a private GitHub repository

1. Run these checks before changing anything. If one fails, stop and tell me exactly what to do.
   - This folder is Clinical-Case-Sim, and it is not already inside a Git repository.
   - git and the GitHub CLI (gh) are installed, and `gh auth status` shows me signed in to github.com.
   - git has user.name and user.email set. If not, ask me which to use, and offer my GitHub no-reply address as an option.
   - I don't already have a GitHub repository called clinical-case-sim.
2. Review the root .gitignore that is already in the folder. Add anything missing, but ask me before removing an entry.
3. Run `git init -b main` and `git add -A`, but don't commit yet. Show me what is staged (the number of files in each folder) and confirm that nothing covered by .gitignore is staged.
4. Scan the staged files for secrets (API keys, tokens, passwords, private keys, database URLs with passwords), with gitleaks if it is installed and a careful grep if not, and list any staged file over 20 MB. If anything looks like a secret, stop and show me. Otherwise commit: "chore: initial import of the design documents and pilot case".
5. Create the private repository and push, with:
   gh repo create clinical-case-sim --private --source=. --remote=origin --push
6. Check that `gh repo view --json visibility,url` says PRIVATE and that `git status -sb` shows main level with origin/main. If the repository is not private, make it private at once and tell me.
7. Tick U0.0 in docs/PLAN.md with a one-line note, commit, push, and give me the repository link.

From now on, keep GitHub in step with this folder, following the "Git and GitHub" section of CLAUDE.md: pull at the start of every session, use one branch per task, commit after each working step, push after every commit and before the session ends, and merge finished tasks through a pull request. Never force-push, rewrite pushed history, make the repository public or commit a secret, and ask me before any Git command that could lose work.

U0.1: Monorepo scaffold

Work on the branch umbrella/U0.1-monorepo-scaffold. State the task and its acceptance criteria, then write the checks first. Ask me before installing anything on my Mac. When the acceptance criteria pass, merge the pull request and stop. Tell me in plain words what you set up, and remind me that the next session starts in case-library/ with task L0.1.
```

## Every later session

Start Claude Code in the folder of the part you are working on (the table in [`../CLAUDE.md`](../CLAUDE.md)), for example `case-library/` for task L0.1, and say:

```text
Continue with the next task in docs/PLAN.md.
```

To save and sync partway through a task:

```text
Commit and push what you have now, then tell me where we are.
```

Before you stop for the day:

```text
Wrap up: finish or pause the current step, commit and push, and tell me where we are and what comes next.
```
