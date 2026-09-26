import AsyncStorage from "@react-native-async-storage/async-storage";
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { Platform } from "react-native";
import { config } from "./config";

/**
 * Sign-in (SPEC §8.1): a pseudonymous Supabase account, created anonymously on first launch.
 * N1.6 adds the consent screen, nickname and training level. The session lives in local
 * storage on the web and AsyncStorage on phones.
 */

let client: SupabaseClient | null = null;

function supabase(): SupabaseClient {
  if (config.supabaseUrl === "" || config.supabaseKey === "") {
    throw new Error(
      "Set EXPO_PUBLIC_SUPABASE_URL and EXPO_PUBLIC_SUPABASE_KEY to sign in.",
    );
  }
  client ??= createClient(config.supabaseUrl, config.supabaseKey, {
    auth: {
      storage: Platform.OS === "web" ? undefined : AsyncStorage,
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: false,
    },
  });
  return client;
}

/** The current access token, signing in anonymously the first time. */
export async function accessToken(): Promise<string> {
  const auth = supabase().auth;
  const { data } = await auth.getSession();
  if (data.session !== null) return data.session.access_token;
  const { data: signedIn, error } = await auth.signInAnonymously();
  if (error !== null || signedIn.session === null) {
    throw new Error(`Could not sign in: ${error?.message ?? "no session"}`);
  }
  return signedIn.session.access_token;
}
