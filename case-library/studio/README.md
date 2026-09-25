# Case Studio

The private, read-only viewer of the Case Vault (Case Library task L0.7; `docs/SPEC.md` §8). It shows every case version, its facts, synthetic ledger, reports and consult notes, figures, ground truth, paths and coverage, and review history, plus the catalogue and the missing requests from Nidana and Sambhasha.

**It shows every diagnosis.** It is never public and never part of the game.

## How it reads the database

- Everything is read on the server (React Server Components). The browser receives only the rendered page.
- One module, `src/server/db.ts`, opens the connection. It reads `CASE_VAULT_DB_URL_READONLY` from the server environment (never a `NEXT_PUBLIC_` variable).
- Every query runs inside a `READ ONLY` transaction that first switches to the role `casevault_reader` (migration `20260925132542_casevault_reader_role.sql`). That role can only `SELECT` and call the functions that read. So even the local superuser URL cannot write through the Studio.
- Queries use postgres.js tagged templates, which send every value as a parameter.

## Run it locally

From the repository root:

```bash
pnpm install
pnpm --filter @case-library/studio dev      # http://localhost:3000
```

The Studio needs one variable, `CASE_VAULT_DB_URL_READONLY`. It looks in two places:

1. `case-library/studio/.env.local`: copy `.env.example` and fill it in.
2. `case-library/.env`: if the variable is not set anywhere else, the Studio reads that one line from this file and ignores the rest (such as the backup URL).

Both files are git-ignored. For the local database (`supabase start` in `case-library/`), use:

```
CASE_VAULT_DB_URL_READONLY=postgresql://postgres:postgres@127.0.0.1:55322/postgres
```

This superuser URL is safe to use here, because the Studio switches to `casevault_reader` in a read-only transaction. The banner at the top shows which database you are reading (host, port and database name, never the password), so you can tell local from cloud.

## Reading the cloud Case Vault (Atul)

The cloud project is `case-vault` (`vxiymbaxsiavxuyxzhnt`). Give the Studio its own login role, which is a member of `casevault_reader`:

1. In the Supabase dashboard, open the SQL editor for `case-vault` and run this yourself, with a password you choose:

   ```sql
   create role studio_reader login password '<choose one>' in role casevault_reader;
   ```

2. Put the session-pooler URL in `case-library/studio/.env.local` (or `case-library/.env`):

   ```
   CASE_VAULT_DB_URL_READONLY=postgresql://studio_reader.vxiymbaxsiavxuyxzhnt:<password>@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres
   ```

Never commit this URL, and never paste it into a chat, an issue or a prompt.

## Deploying (later)

A deployed Studio must sit behind its own login at the proxy (for example an access proxy or basic authentication), with an allow-list that holds Atul's account only (SPEC §8). It never uses the project's Supabase Auth, where Nidana's anonymous testers sign in. It is never public.

## Scripts

Run from the repository root with `pnpm --filter @case-library/studio <script>`, or from this folder with `pnpm <script>`:

| Script | What it does |
| --- | --- |
| `dev` | The development server |
| `build`, `start` | A production build, and serving it |
| `lint` | ESLint (Next.js rules) |
| `typecheck` | `tsc --noEmit` |
| `test` | Vitest: unit tests in `src/lib/*.test.ts`. Integration tests in `src/server/queries/*.int.test.ts` run only when `CASE_VAULT_DB_URL_READONLY` is set. They only read, and they check that writes are refused. |

For example, to run the integration tests against the local database:

```bash
CASE_VAULT_DB_URL_READONLY=postgresql://postgres:postgres@127.0.0.1:55322/postgres \
  pnpm --filter @case-library/studio test
```

## Layout

- `src/app/`: the pages. `/` is the case list, `/cases/[cv]/…` holds the case tabs, and the other pages are `/catalogue` and `/missing-requests`.
- `src/server/db.ts`: the only database connection. `src/server/queries/`: one module for each area, each returning typed rows.
- `src/lib/`: pure helpers (licence badges, fact grouping, sparklines, ledger filters, coverage), each with its own tests.
- `src/components/ui/`: shadcn/ui components copied into the project (Badge, Table, Card).

Figures appear as placeholders until L0.8 adds the images.
