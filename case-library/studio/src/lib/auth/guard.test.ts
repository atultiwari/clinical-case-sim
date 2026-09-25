import { describe, expect, it } from "vitest";

import { decide, type GuardInput } from "@/lib/auth/guard";

function input(overrides: Partial<GuardInput>): GuardInput {
  return { mode: "login", pathname: "/", method: "GET", authenticated: false, localHost: false, ...overrides };
}

describe("the guard's allow/deny matrix", () => {
  const paths = ["/", "/cases/PMC1%40v1/ledger", "/catalogue", "/missing-requests", "/api/anything"];

  describe("with a login configured", () => {
    it.each(paths)("lets a valid session through to %s (GET and POST)", (pathname) => {
      expect(decide(input({ pathname, authenticated: true }))).toEqual({ action: "allow" });
      expect(decide(input({ pathname, method: "POST", authenticated: true }))).toEqual({ action: "allow" });
    });

    it.each(paths)("sends a GET of %s without a session to the login page", (pathname) => {
      expect(decide(input({ pathname }))).toEqual({
        action: "redirect",
        location: `/login?next=${encodeURIComponent(pathname)}`,
      });
    });

    it.each(["POST", "PUT", "PATCH", "DELETE"])("refuses %s without a session (server actions included)", (method) => {
      for (const pathname of paths) {
        expect(decide(input({ pathname, method }))).toMatchObject({ action: "deny", status: 401 });
      }
    });

    it("lets anyone reach the login page and post the login form", () => {
      expect(decide(input({ pathname: "/login" }))).toEqual({ action: "allow" });
      expect(decide(input({ pathname: "/login", method: "POST" }))).toEqual({ action: "allow" });
    });

    it("sends a logged-in visitor of the login page home", () => {
      expect(decide(input({ pathname: "/login", authenticated: true }))).toEqual({ action: "redirect", location: "/" });
    });

    it("does not treat look-alike paths as the login page", () => {
      expect(decide(input({ pathname: "/login/../cases" }))).toMatchObject({ action: "redirect" });
      expect(decide(input({ pathname: "/loginx", method: "POST" }))).toMatchObject({ action: "deny", status: 401 });
    });
  });

  describe("without a login (v1)", () => {
    it("serves localhost only", () => {
      expect(decide(input({ mode: "open", localHost: true }))).toEqual({ action: "allow" });
      expect(decide(input({ mode: "open", localHost: true, method: "POST" }))).toEqual({ action: "allow" });
      expect(decide(input({ mode: "open", localHost: false }))).toMatchObject({ action: "deny", status: 403 });
    });

    it("has no login page", () => {
      expect(decide(input({ mode: "open", localHost: true, pathname: "/login" }))).toEqual({
        action: "redirect",
        location: "/",
      });
    });
  });

  describe("with a malformed login configuration", () => {
    it.each([true, false])("refuses everything (authenticated: %s)", (authenticated) => {
      for (const pathname of [...paths, "/login"]) {
        expect(decide(input({ mode: "invalid", pathname, authenticated, localHost: true }))).toMatchObject({
          action: "deny",
          status: 500,
        });
      }
    });
  });
});
