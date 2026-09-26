import type { ReactNode } from "react";

// The game server is an API; this layout exists only because Next.js requires one.
export default function RootLayout({
  children,
}: {
  readonly children: ReactNode;
}) {
  return (
    <html lang="en-GB">
      <body>{children}</body>
    </html>
  );
}
