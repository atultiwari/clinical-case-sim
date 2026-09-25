# Case Studio

The private viewer of the Case Vault (Case Library tasks L0.7 and L1.5; `docs/SPEC.md` §8). It shows every case version, its facts, synthetic ledger, reports and consult notes, figures, ground truth, paths and coverage, and review history, plus the catalogue and the missing requests from Nidana and Sambhasha.

Version 2 adds Atul's own decisions, as an alternative to the Excel review pack:

- **Review decisions** (SPEC §7.2): Approve, Edit (with the new value) or Reject each ledger row, report, consult note and article fact. They are recorded in `review_decision`, under a batch `studio-<YYYY-MM-DD>-<username>` (UTC day) that the day's first decision creates. The Studio only records them: **Claude applies them to the content through the MCP** after Atul's go-ahead (SPEC §7.3), and then marks the batch applied; a later decision that day starts `studio-<day>-<username>-2`. Decisions are offered only for drafts and versions in review.
- **Figure decisions** (SPEC §9): use, mask or exclude each figure, written straight to its `media` row. Mask needs the masked copy's path in `case-media`, `<case id>/<file>` (for example `PMC12949993/M01-masked.png`). They are allowed after freeze (a new bundle revision follows), never for a retired version.

**It shows every diagnosis.** It is never public and never part of the game.

## Two modes

| | v1 (no login) | v2 (login) |
| --- | --- | --- |
| When | `STUDIO_USERS` empty or unset | `STUDIO_USERS` and `STUDIO_SESSION_SECRET` set |
| Access | Answers only requests addressed to `localhost` | Every page, route and server action needs a session, except `/login` |
| Writes | None: the write actions refuse on the server | Review and figure decisions, if `CASE_VAULT_DB_URL_STUDIO_WRITER` is set |

A malformed `STUDIO_USERS` or a missing or short secret makes the Studio refuse every request (it fails closed) and logs the reason.

## How it reads and writes the database

- Everything runs on the server (React Server Components and server actions). The browser receives only the rendered page.
- Reads: `src/server/db.ts` uses `CASE_VAULT_DB_URL_READONLY`. Every query runs in a `READ ONLY` transaction that first switches to `casevault_reader` (migration `20260925132542`), which can only `SELECT` and call the functions that read.
- Writes: `src/server/writer-db.ts` uses `CASE_VAULT_DB_URL_STUDIO_WRITER`. Each write runs in its own transaction as `casevault_studio_writer` (migration `20260926090000`). That role can insert Studio batches and review decisions, add a case version to an open Studio batch, and set `production_decision`, `masked_path`, `decided_by` and `decided_at` on `media`; nothing else, and no deletes. Row-level security repeats those limits.
- Every server action checks, on its own: writes are enabled, the `Origin` header names this site, the session is valid; then it validates each field against an allow-list or a narrow pattern and checks that the row belongs to the case version. `decided_by` is the logged-in username.
- Queries use postgres.js tagged templates, which send every value as a parameter.

## Login (v2)

- Accounts come from `STUDIO_USERS`: `username:scrypt$N$r$p$salt$hash`, comma-separated. Usernames are lower-case letters, digits, `_` and `-`. Passwords are hashed with scrypt from `node:crypto` (N=2^15, r=8, p=1).
- The session is a cookie signed with HMAC-SHA256 (`STUDIO_SESSION_SECRET`): HttpOnly, Secure (with the `__Host-` prefix), SameSite=Strict, Path=/, for 12 hours. Only the development server on `http://localhost` drops Secure. Logging out clears it. Changing an account's password, removing the account or rotating the secret ends its sessions.
- Comparisons are constant-time, unknown usernames go through the same scrypt check, and every failure shows the same message. Five failures from one address or for one username lock it for 15 minutes. The counts live in memory, so the Studio must run as **a single instance** (one process), and a restart clears them. No password or hash is ever logged.

### Adding an account

```bash
pnpm --filter @case-library/studio hash-password atul            # plain entry (systemd, Docker)
pnpm --filter @case-library/studio hash-password atul --dotenv   # for a .env file: every $ written \$
```

It asks for the password twice without echoing it (at least 12 characters; a passphrase is best) and prints one entry. Next.js expands `$NAME` inside `.env` files, even in quotes, so a `.env` or `.env.local` needs the `--dotenv` form; a systemd `EnvironmentFile` takes the plain one.

## Run it locally

From the repository root:

```bash
pnpm install
pnpm --filter @case-library/studio dev      # http://localhost:3000
```

Put the variables in `case-library/studio/.env.local` (copy `.env.example`). The two database URLs may instead live in `case-library/.env`: the Studio reads just those two lines from it. Both files are git-ignored. For the local database (`supabase start` in `case-library/`):

```
CASE_VAULT_DB_URL_READONLY=postgresql://postgres:postgres@127.0.0.1:55322/postgres
CASE_VAULT_DB_URL_STUDIO_WRITER=postgresql://postgres:postgres@127.0.0.1:55322/postgres
```

The superuser URL is safe for both here, because the Studio switches to `casevault_reader` or `casevault_studio_writer` inside each transaction. The banner shows which database you are reading (host, port and database name, never the password).

## The cloud Case Vault: login roles (Atul)

The cloud project is `case-vault` (`vxiymbaxsiavxuyxzhnt`). The Studio needs two login roles, one in each group role. In the Supabase dashboard, open the SQL editor for `case-vault` and run this yourself, with two different passwords you choose (never in Git, a chat, an issue or a prompt):

```sql
create role studio_reader login password '<password 1>' in role casevault_reader;
create role studio_writer login password '<password 2>' in role casevault_studio_writer;
```

Then use the session-pooler URLs:

```
CASE_VAULT_DB_URL_READONLY=postgresql://studio_reader.vxiymbaxsiavxuyxzhnt:<password 1>@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
CASE_VAULT_DB_URL_STUDIO_WRITER=postgresql://studio_writer.vxiymbaxsiavxuyxzhnt:<password 2>@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
```

`studio_reader` may already exist from v1. The migration `20260926090000_casevault_studio_writer.sql` must be applied to the cloud project first (a Case Library session does this through the MCP).

## Deploying on the VPS (Atul)

1. **HTTPS is required.** Put a reverse proxy in front that terminates TLS, for example Caddy, which gets certificates by itself:

   ```
   studio.example.org {
       reverse_proxy 127.0.0.1:3000
   }
   ```

   Caddy passes `Host` and appends the client's address to `X-Forwarded-For`, which the Studio uses for rate limiting.
2. **Bind the Studio to localhost** so that only the proxy can reach it, and run one process:

   ```bash
   pnpm --filter @case-library/studio build
   pnpm --filter @case-library/studio exec next start --hostname 127.0.0.1 --port 3000
   ```

   Run it under systemd (or similar) with `NODE_ENV=production` and an `EnvironmentFile` readable only by the service user (`chmod 600`), holding `CASE_VAULT_DB_URL_READONLY`, `CASE_VAULT_DB_URL_STUDIO_WRITER`, `STUDIO_USERS` (plain entries) and `STUDIO_SESSION_SECRET` (for example `openssl rand -base64 48`).
3. Firewall: open only 80 and 443 (and SSH); never port 3000.
4. Check: `https://studio.example.org/` redirects to `/login`; `http://<vps-ip>:3000/` does not answer from outside.

The Studio never uses the project's Supabase Auth, where Nidana's testers sign in.

### Rotating secrets

- **Session secret:** set a new `STUDIO_SESSION_SECRET` and restart. Every session ends; log in again.
- **A Studio password:** run `hash-password` again, replace that entry in `STUDIO_USERS`, restart. That account's sessions end.
- **Removing an account:** delete its entry and restart.
- **Database passwords:** in the SQL editor, `alter role studio_writer password '<new>';` (or `studio_reader`), update the URL in the environment file, restart.
- If a secret may have leaked, rotate it at once and check `review_decision` and `media.decided_by` for decisions you did not make.

## Scripts

Run from the repository root with `pnpm --filter @case-library/studio <script>`, or from this folder with `pnpm <script>`:

| Script | What it does |
| --- | --- |
| `dev` | The development server |
| `build`, `start` | A production build, and serving it |
| `lint` | ESLint (Next.js rules) |
| `typecheck` | `tsc --noEmit` |
| `test` | Vitest: unit tests in `src/**/*.test.ts` (login, sessions, rate limiting, the guard, input validation, and the v1 helpers). Integration tests (`*.int.test.ts`) run only with their database variables set. |
| `hash-password` | Prints a `STUDIO_USERS` entry (above) |

The integration tests against the local database:

```bash
L=postgresql://postgres:postgres@127.0.0.1:55322/postgres
CASE_VAULT_DB_URL_READONLY=$L CASE_VAULT_DB_URL_STUDIO_WRITER=$L CASE_VAULT_DB_URL_TEST_OWNER=$L \
  pnpm --filter @case-library/studio test
```

The read tests only read. The write tests (`src/server/actions/decisions.int.test.ts`) need `CASE_VAULT_DB_URL_TEST_OWNER` to be a local URL: they seed the de novo case `NID-9901@v1`, check that a logged-out, forged or cross-site request cannot write and that a logged-in one lands in `review_decision` and `media` as `casevault_studio_writer`, and then remove what they added.

## Layout

- `src/proxy.ts`: the guard on every request (Next.js Proxy); the rule itself is `src/lib/auth/guard.ts`.
- `src/lib/auth/`: password hashing, the configuration, sessions, cookies and the Origin check, rate limiting. Pure and tested.
- `src/lib/review-input.ts`: the validators for the write forms.
- `src/server/db.ts` and `src/server/writer-db.ts`: the only database connections. `src/server/queries/`: one read module for each area. `src/server/writes.ts`: the two writes. `src/server/actions/`: the server actions (login, logout, decisions).
- `src/app/`: the pages. `/` is the case list, `/cases/[cv]/…` holds the case tabs, and the other pages are `/catalogue`, `/missing-requests` and `/login`.
- `src/components/ui/`: shadcn/ui components copied into the project (Badge, Table, Card).

Figures appear as placeholders until L0.8 adds the images.
