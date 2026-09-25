"use client";

import { useActionState } from "react";

import type { ActionState } from "@/lib/action-state";
import { login } from "@/server/actions/session";

export function LoginForm({ next }: { next: string }) {
  const [state, action, pending] = useActionState<ActionState, FormData>(login, null);
  return (
    <form action={action} className="space-y-3">
      <input type="hidden" name="next" value={next} />
      <label className="block">
        <span className="mb-1 block text-xs text-muted-foreground">Username</span>
        <input
          name="username"
          autoComplete="username"
          required
          maxLength={64}
          className="w-full rounded-md border px-2 py-1"
        />
      </label>
      <label className="block">
        <span className="mb-1 block text-xs text-muted-foreground">Password</span>
        <input
          name="password"
          type="password"
          autoComplete="current-password"
          required
          maxLength={1024}
          className="w-full rounded-md border px-2 py-1"
        />
      </label>
      {state && !state.ok ? (
        <p role="alert" className="text-xs text-red-700">
          {state.message}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={pending}
        className="w-full rounded-md border bg-neutral-900 px-3 py-1.5 text-white hover:bg-neutral-700 disabled:opacity-50"
      >
        {pending ? "Checking…" : "Log in"}
      </button>
    </form>
  );
}
