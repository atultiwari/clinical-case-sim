import { describe, expect, it } from "vitest";

import {
  clientAddress,
  hostnameOf,
  isLocalHost,
  isSameOrigin,
  LOCAL_COOKIE_NAME,
  safeNextPath,
  SECURE_COOKIE_NAME,
  sessionCookie,
} from "@/lib/auth/request";

function headers(values: Record<string, string>) {
  return new Headers(values);
}

describe("hosts", () => {
  it.each([
    ["localhost:3000", "localhost", true],
    ["127.0.0.1", "127.0.0.1", true],
    ["[::1]:3000", "[::1]", true],
    ["studio.example.org", "studio.example.org", false],
    ["LOCALHOST", "localhost", true],
    ["localhost.example.org", "localhost.example.org", false],
  ])("%s", (host, name, local) => {
    expect(hostnameOf(host)).toBe(name);
    expect(isLocalHost(host)).toBe(local);
  });
});

describe("sessionCookie", () => {
  it("is HttpOnly, SameSite=Strict, Path=/, 12 hours, and Secure with the __Host- prefix in production", () => {
    expect(sessionCookie("studio.example.org", "production")).toEqual({
      name: SECURE_COOKIE_NAME,
      options: { httpOnly: true, secure: true, sameSite: "strict", path: "/", maxAge: 43_200 },
    });
    expect(sessionCookie("localhost:3000", "production").options.secure).toBe(true);
  });

  it("drops Secure only for the development server on localhost", () => {
    expect(sessionCookie("localhost:3000", "development")).toMatchObject({ name: LOCAL_COOKIE_NAME, options: { secure: false } });
    expect(sessionCookie("studio.example.org", "development").options.secure).toBe(true);
  });
});

describe("isSameOrigin", () => {
  it.each([
    [{ origin: "https://studio.example.org", host: "studio.example.org" }, true],
    [{ origin: "http://localhost:3000", host: "localhost:3000" }, true],
    [{ origin: "https://studio.example.org", host: "127.0.0.1:3000", "x-forwarded-host": "studio.example.org" }, true],
    [{ origin: "https://evil.example", host: "studio.example.org" }, false],
    [{ origin: "https://studio.example.org.evil.example", host: "studio.example.org" }, false],
    [{ origin: "null", host: "studio.example.org" }, false],
    [{ host: "studio.example.org" }, false],
    [{ origin: "javascript:alert(1)", host: "studio.example.org" }, false],
  ])("%j → %s", (values, expected) => {
    expect(isSameOrigin(headers(values))).toBe(expected);
  });
});

describe("clientAddress", () => {
  it("takes the last X-Forwarded-For entry (the one the reverse proxy added)", () => {
    expect(clientAddress(headers({ "x-forwarded-for": "10.0.0.1, 203.0.113.9" }))).toBe("203.0.113.9");
    expect(clientAddress(headers({ "x-real-ip": "203.0.113.10" }))).toBe("203.0.113.10");
    expect(clientAddress(headers({}))).toBe("unknown");
  });
});

describe("safeNextPath", () => {
  it.each([
    ["/cases/PMC1%40v1/ledger", "/cases/PMC1%40v1/ledger"],
    ["/catalogue?q=hb&page=2", "/catalogue?q=hb&page=2"],
    ["//evil.example", "/"],
    ["/\\evil.example", "/"],
    ["https://evil.example", "/"],
    ["javascript:alert(1)", "/"],
    ["/login", "/"],
    [undefined, "/"],
    ["/x y", "/"],
  ])("%s → %s", (value, expected) => {
    expect(safeNextPath(value)).toBe(expected);
  });
});
