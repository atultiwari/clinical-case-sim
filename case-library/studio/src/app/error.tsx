"use client";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="max-w-2xl rounded-md border border-red-300 bg-red-50 p-4 text-red-900">
      <h1 className="mb-2 font-semibold">Could not read the Case Vault</h1>
      <p className="mb-2">
        Check that the database is running and that the URL points at it. The details are in the Studio&apos;s
        terminal{error.digest ? ` (reference ${error.digest})` : ""}.
      </p>
      <button type="button" onClick={reset} className="rounded-md border border-red-300 bg-white px-2 py-1">
        Try again
      </button>
    </div>
  );
}
