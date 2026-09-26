/**
 * The app's settings, inlined at build time from EXPO_PUBLIC_* variables (see .env.example).
 * Nothing here is secret: the Supabase publishable key ships in every app by design.
 */
export const config = {
  apiUrl: (process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:3100").replace(
    /\/$/,
    "",
  ),
  supabaseUrl: process.env.EXPO_PUBLIC_SUPABASE_URL ?? "",
  supabaseKey: process.env.EXPO_PUBLIC_SUPABASE_KEY ?? "",
};
