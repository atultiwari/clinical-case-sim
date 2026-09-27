# Nidana player app

Expo (React Native) for Android, iOS and the web. It talks only to the game server (`../server`); nothing case-specific ships inside it (invariant I1).

## Run it

```bash
cp .env.example .env.local                                   # set EXPO_PUBLIC_SUPABASE_KEY (publishable key)
pnpm --filter @nidana/server dev                              # the game server on :3100 (see ../server/README.md)
pnpm --filter @nidana/player start                            # press w for the web
```

The web build needs the server to allow its origin: set `NIDANA_ALLOWED_ORIGINS=http://localhost:8081` for the server.

## Android (development build)

- Java 17 is needed for Android builds; Android Studio's bundled Java 25 stops the native build ("A restricted method in java.lang.System has been called"). `brew install openjdk@17`, then build with `JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home`.
- `npx expo run:android --no-bundler` builds and installs on the running emulator; `npx expo start --clear` serves the JavaScript. Without Watchman, Metro can miss file changes: restart it with `--clear` if the app shows old code.
- From the emulator, the Mac is `10.0.2.2`: set `EXPO_PUBLIC_API_URL=http://10.0.2.2:3100`, or run `adb reverse tcp:3100 tcp:3100`.

## Tests

| Command                               | What it runs                                                                                                                  |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `pnpm --filter @nidana/player test`   | Vitest: the app's logic (Chart grouping, units, search, commit rules, the API client)                                         |
| `pnpm --filter @nidana/player e2e`    | Playwright: the pilot's benchmark path on the web build, with its own game server; screenshots in `test-results/screenshots/` |
| `maestro test maestro/benchmark.yaml` | Maestro: the same path on Android; needs the game server on the Mac and anonymous sign-in on the Supabase project             |
