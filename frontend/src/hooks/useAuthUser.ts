"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { getCurrentUser, type AuthUser } from "aws-amplify/auth";
import logger from "../utils/logger";

/* ────────────────────────────────────────────────────────────
 *  Core utility: resolve the current Amplify user with retry.
 *  Handles the "UserPool not configured" race-condition that
 *  happens because AmplifyProvider configures Amplify inside a
 *  useEffect (runs after the first render).
 * ──────────────────────────────────────────────────────────── */

const INITIAL_DELAY = 100; // ms – wait for Amplify config
const RETRY_DELAY = 200; // ms – retry if config not ready yet

function isNotConfigured(err: unknown): boolean {
  if (!(err instanceof Error)) return false;
  return (
    err.message.includes("UserPool not configured") ||
    err.message.includes("not configured")
  );
}

function isUnauthenticated(err: unknown): boolean {
  const name = (err as { name?: string })?.name;
  const msg = err instanceof Error ? err.message : "";
  return (
    name === "UserUnauthenticatedException" || msg.includes("not authenticated")
  );
}

/**
 * Attempt to get the current authenticated user.
 * Retries once if Amplify is not configured yet.
 *
 * @returns The AuthUser or `null` if not authenticated.
 * @throws  Re-throws unexpected errors (network, etc.).
 */
export async function resolveCurrentUser(): Promise<AuthUser | null> {
  await new Promise((r) => setTimeout(r, INITIAL_DELAY));

  try {
    return await getCurrentUser();
  } catch (err: unknown) {
    if (isNotConfigured(err)) {
      // Amplify not ready → wait & retry once
      await new Promise((r) => setTimeout(r, RETRY_DELAY));
      try {
        return await getCurrentUser();
      } catch (retryErr: unknown) {
        if (isUnauthenticated(retryErr)) return null;
        throw retryErr;
      }
    }
    if (isUnauthenticated(err)) return null;
    throw err;
  }
}

/* ────────────────────────────────────────────────────────────
 *  Hook: useAuthUser
 * ──────────────────────────────────────────────────────────── */

export interface UseAuthUserOptions {
  /** Re-check auth when custom events / storage events fire (default: false). */
  listenToAuthEvents?: boolean;
}

export interface UseAuthUserResult {
  /** The Amplify AuthUser, or null if not authenticated / still loading. */
  user: AuthUser | null;
  /** `true` while the initial check is in progress. */
  isLoading: boolean;
  /** Convenience boolean derived from `user`. */
  isAuthenticated: boolean;
  /** Manually trigger a re-check (e.g. after sign-in / sign-out). */
  recheck: () => void;
}

/**
 * Centralised hook for Amplify auth state.
 *
 * Replaces the duplicated `try/catch getCurrentUser → retry` blocks
 * found in Header, MonComptePage and AdminGuard.
 */
export function useAuthUser(
  options: UseAuthUserOptions = {},
): UseAuthUserResult {
  const { listenToAuthEvents = false } = options;

  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const mountedRef = useRef(true);

  const check = useCallback(async () => {
    try {
      const u = await resolveCurrentUser();
      if (mountedRef.current) {
        setUser(u);
      }
    } catch (err) {
      logger.warn("useAuthUser – unexpected error:", err);
      if (mountedRef.current) setUser(null);
    } finally {
      if (mountedRef.current) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    check();
    return () => {
      mountedRef.current = false;
    };
  }, [check]);

  // Optional: listen to auth custom events & cross-tab storage events
  useEffect(() => {
    if (!listenToAuthEvents) return;

    const onAuthEvent = () => check();

    const onStorage = (e: StorageEvent) => {
      if (e.key === "auth:signIn" || e.key === "auth:signOut") {
        check();
      }
    };

    window.addEventListener("auth:signIn", onAuthEvent);
    window.addEventListener("auth:signOut", onAuthEvent);
    window.addEventListener("storage", onStorage);

    return () => {
      window.removeEventListener("auth:signIn", onAuthEvent);
      window.removeEventListener("auth:signOut", onAuthEvent);
      window.removeEventListener("storage", onStorage);
    };
  }, [listenToAuthEvents, check]);

  return {
    user,
    isLoading,
    isAuthenticated: user !== null,
    recheck: check,
  };
}

export default useAuthUser;
