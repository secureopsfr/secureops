"use client";

/**
 * Side-effect module: configure Amplify as early as possible.
 *
 * Imported from Providers.tsx so that the config runs before any
 * component (Header, useAuthUser, etc.) tries to call getCurrentUser().
 *
 * The OAuth listener (aws-amplify/auth/enable-oauth-listener) is
 * NOT imported here — it's only loaded by OAuthCallbackHandler on
 * pages that handle OAuth redirects, saving ~10-15KB for anonymous visitors.
 */

import { Amplify } from "aws-amplify";
import awsconfig from "../config/aws-exports";
import { log, error } from "../utils/logger";

let isConfigured = false;

export function ensureAmplifyConfigured(): void {
  if (isConfigured) return;
  try {
    Amplify.configure(awsconfig);
    isConfigured = true;
    log("Amplify configuré avec succès");
  } catch (err) {
    error("Erreur lors de la configuration Amplify:", err);
  }
}

// Run configuration immediately on module load (client-side only)
if (typeof window !== "undefined") {
  ensureAmplifyConfigured();
}
