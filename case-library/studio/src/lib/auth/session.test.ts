import { createHmac } from "node:crypto";

import { describe, expect, it } from "vitest";

import { parseAuthConfig, passwordVersion } from "@/lib/auth/config";
import { authenticate, createSessionToken, SESSION_TTL_SECONDS, verifySessionToken } from "@/lib/auth/session";

const SECRET = "s".repeat(32);
const OTHER_SECRET = "t".repeat(32);
const NOW = 1_800_000_000;

function forge(payload: object, secret = SECRET): string {
  const data = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `${data}.${createHmac("sha256", secret).update(data).digest("base64url")}`;
}

describe("session tokens", () => {
  it("verify with the secret they were signed with", () => {
    const token = createSessionToken("atul", "pv1", SECRET, NOW);
    expect(verifySessionToken(token, SECRET, NOW)).toEqual({
      v: 1,
      u: "atul",
      pv: "pv1",
      iat: NOW,
      exp: NOW + SESSION_TTL_SECONDS,
    });
  });

  it("expire after 12 hours", () => {
    const token = createSessionToken("atul", "pv1", SECRET, NOW);
    expect(SESSION_TTL_SECONDS).toBe(12 * 3600);
    expect(verifySessionToken(token, SECRET, NOW + SESSION_TTL_SECONDS - 1)).not.toBeNull();
    expect(verifySessionToken(token, SECRET, NOW + SESSION_TTL_SECONDS)).toBeNull();
  });

  it("are rejected with another secret", () => {
    expect(verifySessionToken(createSessionToken("atul", "pv1", SECRET, NOW), OTHER_SECRET, NOW)).toBeNull();
  });

  it("are rejected when the payload is changed", () => {
    const token = createSessionToken("atul", "pv1", SECRET, NOW);
    const [, signature] = token.split(".");
    const tampered = Buffer.from(JSON.stringify({ v: 1, u: "admin", pv: "pv1", iat: NOW, exp: NOW + 60 })).toString(
      "base64url",
    );
    expect(verifySessionToken(`${tampered}.${signature}`, SECRET, NOW)).toBeNull();
  });

  it("are rejected when the signature is changed or truncated", () => {
    const token = createSessionToken("atul", "pv1", SECRET, NOW);
    const [data, signature] = token.split(".") as [string, string];
    const flipped = (signature[0] === "A" ? "B" : "A") + signature.slice(1);
    expect(verifySessionToken(`${data}.${flipped}`, SECRET, NOW)).toBeNull();
    expect(verifySessionToken(`${data}.${signature.slice(0, 20)}`, SECRET, NOW)).toBeNull();
    expect(verifySessionToken(`${data}.`, SECRET, NOW)).toBeNull();
  });

  it.each([
    [undefined],
    [""],
    ["garbage"],
    ["a.b.c"],
    ["!!.??"],
    ["x".repeat(2000)],
  ])("reject malformed input %#", (token) => {
    expect(verifySessionToken(token, SECRET, NOW)).toBeNull();
  });

  it("reject correctly signed payloads of the wrong shape or with impossible times", () => {
    expect(verifySessionToken(forge({ v: 2, u: "atul", pv: "p", iat: NOW, exp: NOW + 60 }), SECRET, NOW)).toBeNull();
    expect(verifySessionToken(forge({ v: 1, u: 7, pv: "p", iat: NOW, exp: NOW + 60 }), SECRET, NOW)).toBeNull();
    // Issued in the future.
    expect(verifySessionToken(forge({ v: 1, u: "atul", pv: "p", iat: NOW + 3600, exp: NOW + 7200 }), SECRET, NOW)).toBeNull();
    // Longer than the allowed lifetime.
    expect(
      verifySessionToken(forge({ v: 1, u: "atul", pv: "p", iat: NOW, exp: NOW + SESSION_TTL_SECONDS + 1 }), SECRET, NOW),
    ).toBeNull();
    const notJson = Buffer.from("not json").toString("base64url");
    expect(verifySessionToken(`${notJson}.${createHmac("sha256", SECRET).update(notJson).digest("base64url")}`, SECRET, NOW)).toBeNull();
  });
});

describe("authenticate", () => {
  const salt = Buffer.alloc(16, 1).toString("base64");
  const entry = `scrypt$16384$8$1$${salt}$${Buffer.alloc(32, 2).toString("base64")}`;
  const changed = `scrypt$16384$8$1$${salt}$${Buffer.alloc(32, 3).toString("base64")}`;
  const config = parseAuthConfig({ STUDIO_USERS: `atul:${entry}`, STUDIO_SESSION_SECRET: SECRET });

  it("returns the username for a valid session of a listed account", () => {
    const token = createSessionToken("atul", passwordVersion(entry), SECRET, NOW);
    expect(authenticate(config, token, NOW)).toBe("atul");
  });

  it("refuses an account no longer on the allow-list", () => {
    const token = createSessionToken("reviewer", passwordVersion(entry), SECRET, NOW);
    expect(authenticate(config, token, NOW)).toBeNull();
  });

  it("refuses a session from before a password change", () => {
    const token = createSessionToken("atul", passwordVersion(changed), SECRET, NOW);
    expect(authenticate(config, token, NOW)).toBeNull();
  });

  it("refuses everything without a login configured", () => {
    const token = createSessionToken("atul", passwordVersion(entry), SECRET, NOW);
    expect(authenticate({ mode: "open" }, token, NOW)).toBeNull();
    expect(authenticate({ mode: "invalid", reason: "x" }, token, NOW)).toBeNull();
  });
});
