import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

import { SiteHeader } from "@/components/site-header";
import { databaseHost, isDatabaseConfigured } from "@/server/db";
import { DB_URL_VARIABLE } from "@/server/env";

export const metadata: Metadata = {
  title: "Case Studio",
  description: "Private, read-only viewer of the Case Vault.",
  robots: { index: false, follow: false },
};

// Every page reads the Case Vault at request time; nothing is prerendered.
export const dynamic = "force-dynamic";

export default function RootLayout({ children }: { children: ReactNode }) {
  const configured = isDatabaseConfigured();
  return (
    <html lang="en-GB">
      <body>
        <SiteHeader host={configured ? databaseHost() : null} />
        <main className="mx-auto max-w-[1400px] px-4 py-4">
          {configured ? children : <MissingDatabase />}
        </main>
      </body>
    </html>
  );
}

function MissingDatabase() {
  return (
    <div className="max-w-2xl rounded-md border border-red-300 bg-red-50 p-4 text-red-900">
      <h1 className="mb-2 font-semibold">The Case Vault is not configured</h1>
      <p className="mb-2">
        Set <code>{DB_URL_VARIABLE}</code> in <code>case-library/studio/.env.local</code> or{" "}
        <code>case-library/.env</code>, then restart the Studio.
      </p>
      <p>
        Locally: <code>postgresql://postgres:postgres@127.0.0.1:55322/postgres</code> (the Studio reads as{" "}
        <code>casevault_reader</code>). See <code>case-library/studio/README.md</code>.
      </p>
    </div>
  );
}
