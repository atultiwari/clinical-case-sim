# Deploying Nidana to staging (Coolify)

Task N1.8. Staging runs the game server and the web build of the player app on Atul's VPS through Coolify, against the development database (the `play` schema in the Case Vault project, S-007). Android testers get a development build that points at the staging server.

Nothing secret goes in Git. The only secrets are the game server's `DATABASE_URL` (the `nidana_game` login) and, where the project signs with a shared secret, `SUPABASE_JWT_SECRET`; both are typed into Coolify's environment screen, never into a file or a chat.

## What runs

| Resource    | Built from                                                | Listens on | Health check      |
| ----------- | --------------------------------------------------------- | ---------- | ----------------- |
| Game server | `nidana/apps/server/Dockerfile`                           | 3100       | `GET /api/health` |
| Web build   | `nidana/apps/player/Dockerfile.web` (static files, nginx) | 80         | `GET /`           |

Both are built from the repository root (`atultiwari/clinical-case-sim`, branch `main`). The repository is public, so Coolify needs no deploy key. CI builds both images on every Nidana change (`.github/workflows/nidana.yml`, "Container images build"), so a broken Dockerfile shows up before a deploy.

## 1. The game server

In Coolify: **New resource → Public repository** → `https://github.com/atultiwari/clinical-case-sim`, branch `main`.

- Build pack: **Dockerfile**. Base directory: `/`. Dockerfile location: `/nidana/apps/server/Dockerfile`.
- Ports exposed: `3100`.
- Domain: for example `https://nidana-api.<your domain>` (Coolify gets the certificate).
- Health check: path `/api/health`, port `3100`.
- Environment variables (runtime, not build):

| Key                      | Value                                                                                    |
| ------------------------ | ---------------------------------------------------------------------------------------- |
| `NIDANA_BUNDLE_SOURCE`   | `database`                                                                               |
| `NIDANA_STORE`           | `database`                                                                               |
| `DATABASE_URL`           | the `nidana_game` URL from `apps/server/.env.local` (session pooler, port 5432)          |
| `SUPABASE_URL`           | `https://vxiymbaxsiavxuyxzhnt.supabase.co`                                               |
| `SUPABASE_JWT_SECRET`    | only if `.env.local` has one; otherwise leave it out (keys come from the project's JWKS) |
| `NIDANA_ALLOWED_ORIGINS` | the web build's address from step 2, for example `https://nidana.<your domain>`          |

Deploy. `https://nidana-api.<your domain>/api/health` should answer `{"success":true,"data":{"status":"ok"},"error":null}`, and `/api/cases` should answer 401 (sign-in needed). The server loads the published cases at start-up, which takes a few seconds from a distant database.

## 2. The web build

Another **Public repository** resource from the same repository and branch.

- Build pack: **Dockerfile**. Base directory: `/`. Dockerfile location: `/nidana/apps/player/Dockerfile.web`.
- Ports exposed: `80`.
- Domain: for example `https://nidana.<your domain>`.
- Environment variables, each marked **Build variable** (they are inlined into the JavaScript, and all three are public by design):

| Key                        | Value                                                    |
| -------------------------- | -------------------------------------------------------- |
| `EXPO_PUBLIC_API_URL`      | the game server's address from step 1, no trailing slash |
| `EXPO_PUBLIC_SUPABASE_URL` | `https://vxiymbaxsiavxuyxzhnt.supabase.co`               |
| `EXPO_PUBLIC_SUPABASE_KEY` | the project's publishable key (`sb_publishable_…`)       |

Deploy. The address should open the consent screen. If the page loads but every request fails, check that `NIDANA_ALLOWED_ORIGINS` on the game server matches this address exactly (scheme and host, no trailing slash), then redeploy the server.

## 3. The Android development build

Built on Atul's Mac with Java 17 (`apps/player/README.md`), pointing at the staging server, and signed with the debug key (it is for testing, not for a store):

```bash
cd nidana/apps/player
EXPO_PUBLIC_API_URL=https://nidana-api.<your domain> npx expo prebuild --platform android
cd android && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew assembleRelease
```

The file is `android/app/build/outputs/apk/release/app-release.apk`; install it with `adb install` or by copying it to the phone. `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_KEY` come from `apps/player/.env.local`.

## Updating staging

Merging to `main` and pressing **Redeploy** in Coolify (or turning on automatic deploys for `main`) rebuilds both images. The web build must be rebuilt whenever its three build variables change.

## Before the store release

Staging uses the development database and development-only cases (S-010). The store release gets its own database on the VPS (N-012) and a new, private case set; none of this staging set-up carries over unchanged.
