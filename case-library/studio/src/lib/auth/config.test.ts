import { describe, expect, it } from "vitest";

import { parseAuthConfig } from "@/lib/auth/config";

const SALT = Buffer.alloc(16, 1).toString("base64");
const ENTRY = `scrypt$16384$8$1$${SALT}$${Buffer.alloc(32, 2).toString("base64")}`;
const SECRET = "x".repeat(32);

describe("parseAuthConfig", () => {
  it("is open (v1, read-only) without STUDIO_USERS", () => {
    expect(parseAuthConfig({})).toEqual({ mode: "open" });
    expect(parseAuthConfig({ STUDIO_USERS: "  " })).toEqual({ mode: "open" });
  });

  it("reads the allow-list and keeps the secret", () => {
    const config = parseAuthConfig({ STUDIO_USERS: ` atul:${ENTRY} , second_user:${ENTRY}`, STUDIO_SESSION_SECRET: SECRET });
    expect(config.mode).toBe("login");
    if (config.mode !== "login") return;
    expect([...config.users.keys()]).toEqual(["atul", "second_user"]);
    expect(config.secret).toBe(SECRET);
    expect(config.dummy.N).toBe(16384);
  });

  it.each([
    [{ STUDIO_USERS: `atul:${ENTRY}` }, /STUDIO_SESSION_SECRET/],
    [{ STUDIO_USERS: `atul:${ENTRY}`, STUDIO_SESSION_SECRET: "short" }, /at least 32 bytes/],
    [{ STUDIO_USERS: `Atul:${ENTRY}`, STUDIO_SESSION_SECRET: SECRET }, /username/],
    [{ STUDIO_USERS: `:${ENTRY}`, STUDIO_SESSION_SECRET: SECRET }, /username/],
    [{ STUDIO_USERS: "atul", STUDIO_SESSION_SECRET: SECRET }, /username/],
    [{ STUDIO_USERS: "atul:plaintext-password", STUDIO_SESSION_SECRET: SECRET }, /not a valid scrypt entry/],
    [{ STUDIO_USERS: `atul:${ENTRY},atul:${ENTRY}`, STUDIO_SESSION_SECRET: SECRET }, /twice/],
    [{ STUDIO_USERS: ",,,", STUDIO_SESSION_SECRET: SECRET }, /no accounts/],
  ])("is invalid (fails closed) for %j", (env, reason) => {
    const config = parseAuthConfig(env);
    expect(config.mode).toBe("invalid");
    if (config.mode === "invalid") expect(config.reason).toMatch(reason);
  });

  it("never puts a hash or the secret in its message", () => {
    const config = parseAuthConfig({ STUDIO_USERS: `atul:${ENTRY}`, STUDIO_SESSION_SECRET: "tooshortsecret" });
    expect(config.mode).toBe("invalid");
    if (config.mode === "invalid") {
      expect(config.reason).not.toContain(SALT);
      expect(config.reason).not.toContain("tooshortsecret");
    }
    const bad = parseAuthConfig({ STUDIO_USERS: "atul:scrypt$1$2$3$secretish$x", STUDIO_SESSION_SECRET: SECRET });
    if (bad.mode === "invalid") expect(bad.reason).not.toContain("secretish");
  });
});
