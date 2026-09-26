import { describe, expect, it } from "vitest";
import { loadConfig } from "@/lib/config";

describe("loadConfig", () => {
  it("defaults to files and memory, with monorepo paths", () => {
    const config = loadConfig(
      { SUPABASE_JWT_SECRET: "x".repeat(32) },
      "/repo/nidana/apps/server",
    );
    expect(config).toMatchObject({
      bundleSource: "files",
      store: "memory",
      exportsDir: "/repo/case-library/exports",
      cataloguePath: "/repo/nidana/conformance/catalogue/catalogue.v2.json",
      configDir: "/repo/nidana/configs",
    });
  });

  it("derives the JWKS URL and issuer from the project URL", () => {
    const config = loadConfig({ SUPABASE_URL: "https://abc.supabase.co/" });
    expect(config.jwksUrl).toBe(
      "https://abc.supabase.co/auth/v1/.well-known/jwks.json",
    );
    expect(config.issuer).toBe("https://abc.supabase.co/auth/v1");
  });

  it.each([
    [
      { NIDANA_STORE: "database", SUPABASE_URL: "https://a.supabase.co" },
      /DATABASE_URL/,
    ],
    [
      { NODE_ENV: "production", SUPABASE_URL: "https://a.supabase.co" },
      /NIDANA_STORE/,
    ],
    [{}, /SUPABASE_URL/],
    [
      { NIDANA_BUNDLE_SOURCE: "s3", SUPABASE_URL: "https://a.supabase.co" },
      /NIDANA_BUNDLE_SOURCE/,
    ],
  ])("refuses %j", (env, message) => {
    expect(() => loadConfig(env)).toThrow(message);
  });
});
