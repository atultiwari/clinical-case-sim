// Prints one STUDIO_USERS entry: <username>:scrypt$N$r$p$salt$hash.
//
//   pnpm --filter @case-library/studio hash-password <username> [--dotenv]
//
// With --dotenv every '$' is written as '\$', as a .env or .env.local file needs
// (Next.js expands $NAME in those files; quotes do not stop it). A systemd
// EnvironmentFile or a Docker env file takes the plain entry.
//
// The password is read from the terminal without echo (asked twice), or from
// the first line of standard input when it is piped. It is never printed or
// logged. Run with Node's type stripping (Node 22.18 or later).

import { stdin, stdout, stderr, argv, exit } from "node:process";

import { hashPassword, MAX_PASSWORD_LENGTH } from "../src/lib/auth/password.ts";

const USERNAME_PATTERN = /^[a-z][a-z0-9_-]{0,31}$/;
const MIN_PASSWORD_LENGTH = 12;

function fail(message: string): never {
  stderr.write(`${message}\n`);
  exit(1);
}

/** Reads one line from the terminal in raw mode, echoing nothing. */
function readHidden(prompt: string): Promise<string> {
  return new Promise((resolve) => {
    stderr.write(prompt);
    stdin.setRawMode(true);
    stdin.resume();
    stdin.setEncoding("utf8");
    let value = "";
    const onData = (chunk: string) => {
      for (const char of chunk) {
        if (char === "\u0003") {
          stdin.setRawMode(false);
          stderr.write("\n");
          exit(130);
        } else if (char === "\r" || char === "\n" || char === "\u0004") {
          stdin.setRawMode(false);
          stdin.pause();
          stdin.off("data", onData);
          stderr.write("\n");
          resolve(value);
          return;
        } else if (char === "\u007f" || char === "\b") {
          value = [...value].slice(0, -1).join("");
        } else if (char >= " ") {
          value += char;
        }
      }
    };
    stdin.on("data", onData);
  });
}

async function readPiped(): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of stdin) chunks.push(Buffer.from(chunk));
  return (Buffer.concat(chunks).toString("utf8").split(/\r?\n/)[0] ?? "");
}

async function main(): Promise<void> {
  const args = argv.slice(2);
  const dotenv = args.includes("--dotenv");
  const username = args.find((arg) => !arg.startsWith("--"))?.trim() ?? "";
  if (!USERNAME_PATTERN.test(username)) {
    fail("Usage: pnpm --filter @case-library/studio hash-password <username> [--dotenv]\n" +
      "The username: lower-case letters, digits, '_' or '-', starting with a letter, at most 32 characters.");
  }

  let password: string;
  if (stdin.isTTY) {
    password = await readHidden(`Password for ${username}: `);
    const again = await readHidden("Again: ");
    if (password !== again) fail("The two passwords differ.");
  } else {
    password = await readPiped();
  }
  if (password.length < MIN_PASSWORD_LENGTH) fail(`Use at least ${MIN_PASSWORD_LENGTH} characters (a passphrase is best).`);
  if (password.length > MAX_PASSWORD_LENGTH) fail(`Use at most ${MAX_PASSWORD_LENGTH} characters.`);

  const entry = `${username}:${await hashPassword(password)}`;
  stdout.write(`${dotenv ? entry.replaceAll("$", "\\$") : entry}\n`);
}

main().catch((error: unknown) => fail(`hash-password failed: ${error instanceof Error ? error.message : String(error)}`));
