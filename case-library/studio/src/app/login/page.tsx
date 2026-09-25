import type { Metadata } from "next";

import { LoginForm } from "@/components/login-form";
import { safeNextPath } from "@/lib/auth/request";
import type { SearchParams } from "@/lib/search-params";

export const metadata: Metadata = { title: "Log in · Case Studio" };

export default async function LoginPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const { next } = await searchParams;
  return (
    <div className="mx-auto mt-12 max-w-sm rounded-md border bg-white p-6">
      <h1 className="mb-1 text-lg font-semibold">Log in to the Case Studio</h1>
      <p className="mb-4 text-xs text-muted-foreground">
        Private: the Studio shows every diagnosis. Accounts are on the Studio&apos;s allow-list only.
      </p>
      <LoginForm next={safeNextPath(Array.isArray(next) ? next[0] : next)} />
    </div>
  );
}
