"use client";

import { useEffect } from "react";
import { Hub } from "aws-amplify/utils";
// CRITICAL: This side-effect import registers the OAuth callback handler.
// Without it, Amplify does NOT process ?code=&state= in the URL after
// Google/OAuth redirect. Only needed on pages that handle OAuth redirects.
import "aws-amplify/auth/enable-oauth-listener";
import logger from "../utils/logger";

/**
 * Gère le callback OAuth après une redirection Google sign-in.
 * Écoute les événements Hub Amplify, nettoie l'URL et notifie le Header.
 * Ne rend aucun élément visible.
 */
export default function OAuthCallbackHandler() {
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get("code");
    const errorParam = urlParams.get("error");

    if (errorParam) {
      logger.warn("[OAuth] Error in URL:", errorParam);
      window.history.replaceState({}, document.title, window.location.pathname);
      return;
    }

    if (!code) return;

    logger.debug("[OAuth] Code detected in URL, listening for Hub events...");

    let handled = false;

    const hubListener = Hub.listen("auth", async ({ payload }) => {
      logger.debug("[OAuth] Hub event:", payload.event);

      if (payload.event === "signInWithRedirect") {
        logger.debug("[OAuth] signInWithRedirect completed!");
        handled = true;
        hubListener(); // unsubscribe

        // Clean URL
        window.history.replaceState(
          {},
          document.title,
          window.location.pathname,
        );
        // Notify Header
        sessionStorage.setItem("justLoggedIn", "true");
        window.dispatchEvent(new CustomEvent("auth:signIn"));
        localStorage.setItem("auth:signIn", Date.now().toString());
        localStorage.removeItem("auth:signIn");
        logger.debug("[OAuth] SUCCESS - auth:signIn dispatched");
      }

      if (payload.event === "signInWithRedirect_failure") {
        logger.error("[OAuth] signInWithRedirect FAILED:", payload.data);
        handled = true;
        hubListener();
        window.history.replaceState(
          {},
          document.title,
          window.location.pathname,
        );
      }
    });

    // Timeout fallback (10s)
    const timeout = setTimeout(() => {
      if (handled) return;
      logger.error("[OAuth] Timeout: no Hub event after 10s. Cleaning URL.");
      hubListener();
      window.history.replaceState({}, document.title, window.location.pathname);
    }, 10000);

    return () => {
      hubListener();
      clearTimeout(timeout);
    };
  }, []);

  return null;
}
