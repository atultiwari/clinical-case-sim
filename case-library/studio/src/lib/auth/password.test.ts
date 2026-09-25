import { describe, expect, it } from "vitest";

import {
  dummyHash,
  formatScryptHash,
  hashPassword,
  MAX_PASSWORD_LENGTH,
  parseScryptHash,
  verifyPassword,
} from "@/lib/auth/password";

// The smallest cost the parser accepts, to keep the tests fast.
const FAST = { N: 2 ** 14, r: 8, p: 1 };

describe("hashPassword and verifyPassword", () => {
  it("round-trips a password", async () => {
    const encoded = await hashPassword("correct horse battery", FAST);
    expect(encoded).toMatch(/^scrypt\$16384\$8\$1\$[A-Za-z0-9+/=]+\$[A-Za-z0-9+/=]+$/);
    const parsed = parseScryptHash(encoded);
    expect(parsed).not.toBeNull();
    expect(await verifyPassword("correct horse battery", parsed!)).toBe(true);
  });

  it("rejects a wrong, empty or differently normalised password", async () => {
    const parsed = parseScryptHash(await hashPassword("correct horse battery", FAST))!;
    expect(await verifyPassword("correct horse batterY", parsed)).toBe(false);
    expect(await verifyPassword("", parsed)).toBe(false);
    expect(await verifyPassword("correct horse battery ", parsed)).toBe(false);
  });

  it("treats NFC and NFD forms of the same password alike", async () => {
    const parsed = parseScryptHash(await hashPassword("café au lait 1", FAST))!;
    expect(await verifyPassword("café au lait 1", parsed)).toBe(true);
  });

  it("salts every hash", async () => {
    const a = await hashPassword("same password here", FAST);
    const b = await hashPassword("same password here", FAST);
    expect(a).not.toBe(b);
  });

  it("refuses empty and over-long passwords and unsafe parameters", async () => {
    await expect(hashPassword("", FAST)).rejects.toThrow();
    await expect(hashPassword("x".repeat(MAX_PASSWORD_LENGTH + 1), FAST)).rejects.toThrow();
    await expect(hashPassword("long enough pw", { N: 1024, r: 8, p: 1 })).rejects.toThrow(/Unsafe/);
    const parsed = parseScryptHash(await hashPassword("long enough pw", FAST))!;
    expect(await verifyPassword("x".repeat(MAX_PASSWORD_LENGTH + 1), parsed)).toBe(false);
  });

  it("never matches the dummy entry used for unknown usernames", async () => {
    expect(await verifyPassword("", dummyHash(FAST))).toBe(false);
    expect(await verifyPassword("anything at all", dummyHash(FAST))).toBe(false);
  });
});

describe("parseScryptHash", () => {
  const salt = Buffer.alloc(16, 1).toString("base64");
  const hash = Buffer.alloc(32, 2).toString("base64");

  it("accepts a well-formed entry and formats it back", () => {
    const encoded = `scrypt$16384$8$1$${salt}$${hash}`;
    expect(formatScryptHash(parseScryptHash(encoded)!)).toBe(encoded);
  });

  it.each([
    ["", "empty"],
    [`bcrypt$16384$8$1$${salt}$${hash}`, "another scheme"],
    [`scrypt$16384$8$1$${salt}`, "missing a part"],
    [`scrypt$16000$8$1$${salt}$${hash}`, "N not a power of two"],
    [`scrypt$1024$8$1$${salt}$${hash}`, "N too small"],
    [`scrypt$2097152$8$1$${salt}$${hash}`, "N too large"],
    [`scrypt$16384$64$1$${salt}$${hash}`, "r too large"],
    [`scrypt$16384$8$0$${salt}$${hash}`, "p zero"],
    [`scrypt$16384$8$1$${Buffer.alloc(8).toString("base64")}$${hash}`, "short salt"],
    [`scrypt$16384$8$1$${salt}$${Buffer.alloc(16).toString("base64")}`, "short hash"],
    [`scrypt$16384$8$1$not*base64$${hash}`, "bad base64"],
    [`scrypt$0x4000$8$1$${salt}$${hash}`, "hex number"],
  ])("rejects %s (%s)", (encoded) => {
    expect(parseScryptHash(encoded)).toBeNull();
  });
});
