import type { Profile } from "@nidana/contracts/api";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { hasSession } from "./auth";
import { useApi } from "./game";

/**
 * Whether the player has agreed yet (N1.6). Until they have, the app shows the consent screen
 * and makes no network call: there is no session, and none is created before they agree.
 */

export type AccountStatus = "checking" | "needs_consent" | "ready" | "error";

interface Account {
  readonly status: AccountStatus;
  readonly profile: Profile | null;
  readonly error: string | null;
  readonly setProfile: (profile: Profile) => void;
  readonly recheck: () => void;
}

const AccountContext = createContext<Account | null>(null);

export function AccountProvider({
  children,
  sessionCheck = hasSession,
}: {
  readonly children: ReactNode;
  readonly sessionCheck?: () => Promise<boolean>;
}) {
  const api = useApi();
  const [status, setStatus] = useState<AccountStatus>("checking");
  const [profile, setProfileState] = useState<Profile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let live = true;
    (async () => {
      if (!(await sessionCheck())) return null;
      return api.me();
    })().then(
      (me) => {
        if (!live) return;
        setProfileState(me);
        setStatus(me === null ? "needs_consent" : "ready");
      },
      (e: unknown) => {
        if (!live) return;
        setError(
          e instanceof Error ? e.message : "Could not check your account",
        );
        setStatus("error");
      },
    );
    return () => {
      live = false;
    };
  }, [api, sessionCheck, attempt]);

  const setProfile = useCallback((next: Profile) => {
    setProfileState(next);
    setStatus("ready");
  }, []);
  const recheck = useCallback(() => {
    setStatus("checking");
    setAttempt((n) => n + 1);
  }, []);

  const value = useMemo<Account>(
    () => ({ status, profile, error, setProfile, recheck }),
    [status, profile, error, setProfile, recheck],
  );
  return (
    <AccountContext.Provider value={value}>{children}</AccountContext.Provider>
  );
}

export function useAccount(): Account {
  const account = useContext(AccountContext);
  if (account === null)
    throw new Error("useAccount must be used inside AccountProvider");
  return account;
}

export { TRAINING_LEVELS, nicknameProblem } from "./account-rules";
