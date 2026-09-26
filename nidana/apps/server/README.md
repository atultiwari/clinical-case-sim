# Nidana game server

Next.js route handlers only (SPEC §6.2); the engine runs here and nothing case-specific leaves it before the debrief.

```bash
cp .env.example .env.local        # then set SUPABASE_JWT_SECRET or SUPABASE_URL
pnpm --filter @nidana/server dev  # http://localhost:3100/api/...
pnpm --filter @nidana/server test
```

- Every endpoint needs `Authorization: Bearer <Supabase access token>`; responses are `{ success, data, error }`.
- `NIDANA_BUNDLE_SOURCE=files` plays the committed exports; `database` reads published bundles from the Case Vault through the `nidana_server` role.
- `NIDANA_STORE=memory` keeps play data in memory (local only); `database` uses the `play` schema (`../../supabase/proposed/`).
- The Postgres tests run only with `NIDANA_TEST_DB_URL` set (the Case Library's local stack), inside a transaction that is always rolled back.
