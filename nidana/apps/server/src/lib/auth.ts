import { createRemoteJWKSet, jwtVerify, type JWTVerifyGetKey } from "jose";

/**
 * Sign-in checks (SPEC §6.5): every request carries a Supabase Auth access token, verified
 * here without a network call per request. Anonymous (pseudonymous) sign-ins count (N1.6).
 */

export interface Player {
  readonly playerId: string;
}

export interface Verifier {
  verify(token: string): Promise<Player | null>;
}

export interface VerifierOptions {
  /** The project's JWT secret (HS256), as the local Supabase stack and legacy projects use. */
  readonly jwtSecret?: string;
  /** The project's JWKS endpoint, for asymmetric signing keys. */
  readonly jwksUrl?: string;
  /** Required: a token from any other issuer is refused (fail closed). */
  readonly issuer: string;
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function createVerifier(options: VerifierOptions): Verifier {
  let key: Uint8Array | JWTVerifyGetKey;
  if (options.jwtSecret !== undefined && options.jwtSecret.length >= 32) {
    key = new TextEncoder().encode(options.jwtSecret);
  } else if (options.jwksUrl !== undefined) {
    key = createRemoteJWKSet(new URL(options.jwksUrl));
  } else {
    throw new Error(
      "Sign-in checks need SUPABASE_JWT_SECRET (32+ characters) or SUPABASE_URL",
    );
  }
  return {
    async verify(token) {
      try {
        const verifyOptions = {
          audience: "authenticated",
          issuer: options.issuer,
        };
        const { payload } = await (key instanceof Uint8Array
          ? jwtVerify(token, key, verifyOptions)
          : jwtVerify(token, key, verifyOptions));
        return typeof payload.sub === "string" && UUID.test(payload.sub)
          ? { playerId: payload.sub }
          : null;
      } catch {
        return null;
      }
    },
  };
}

export function bearerToken(header: string | null): string | null {
  const match = /^Bearer\s+(\S+)$/i.exec(header ?? "");
  return match?.[1] ?? null;
}
