"use client";

import { useEffect, useRef, useImperativeHandle, forwardRef } from "react";
import logger from "../utils/logger";

type TurnstileCallbacks = {
  callback?: (token: string) => void;
  "expired-callback"?: () => void;
  "error-callback"?: () => void;
};

type TurnstileRenderOptions = {
  sitekey: string;
  size?: "normal" | "compact";
  execution?: "execute";
} & TurnstileCallbacks;

type TurnstileApi = {
  render: (
    container: HTMLElement,
    options: TurnstileRenderOptions,
  ) => string | null;
  execute: (widgetId: string | null) => void;
  remove: (widgetId: string | null) => void;
  reset?: (widgetId: string | null) => void;
};

declare global {
  interface Window {
    turnstile?: TurnstileApi;
  }
}

interface Props {
  onSuccess: (token: string) => void;
}

export interface TurnstileRef {
  execute: () => void;
}

const TurnstileWidget = forwardRef<TurnstileRef, Props>(
  ({ onSuccess }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const widgetIdRef = useRef<string | null>(null);
    const onSuccessRef = useRef(onSuccess);
    const initializedRef = useRef(false);

    useEffect(() => {
      onSuccessRef.current = onSuccess;
    }, [onSuccess]);

    // Charger le script Turnstile une seule fois
    useEffect(() => {
      if (
        typeof window !== "undefined" &&
        !window.turnstile &&
        !document.querySelector('script[src*="turnstile"]')
      ) {
        const script = document.createElement("script");
        script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
      }
    }, []);

    const handleToken = (token: string) => {
      logger.debug("[TURNSTILE] callback fired");
      logger.debug(
        "[TURNSTILE] token:",
        token ? `${token.substring(0, 20)}...` : "EMPTY",
      );

      if (!token) return;

      try {
        onSuccessRef.current(token);
        logger.debug("[TURNSTILE] onSuccess called");
      } catch (error) {
        logger.warn("[TURNSTILE] onSuccess threw:", error);
      }
    };

    const handleExpired = () => {
      logger.warn("[TURNSTILE] expired");
    };

    const handleError = () => {
      logger.warn("[TURNSTILE] error (silent in production)");
    };

    useImperativeHandle(ref, () => ({
      execute: () => {
        logger.debug("[TURNSTILE] execute() called");

        if (!window.turnstile) {
          logger.warn("[TURNSTILE] window.turnstile not available");
          return;
        }

        if (!widgetIdRef.current || !initializedRef.current) {
          logger.warn("[TURNSTILE] widget not ready yet");
          return;
        }

        try {
          window.turnstile.execute(widgetIdRef.current);
          logger.debug("[TURNSTILE] execute() invoked on", widgetIdRef.current);
        } catch (error) {
          logger.warn("[TURNSTILE] execute() failed:", error);
          handleError();
        }
      },
    }));

    useEffect(() => {
      logger.debug("[TURNSTILE] init useEffect");

      if (!containerRef.current) {
        logger.warn("[TURNSTILE] container not mounted");
        return;
      }

      if (initializedRef.current) {
        logger.debug("[TURNSTILE] already initialized, skip");
        return;
      }

      const siteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;

      logger.debug(
        "[TURNSTILE] sitekey:",
        siteKey ? `${siteKey.substring(0, 10)}...` : "MISSING",
      );

      if (!siteKey) {
        logger.warn("[TURNSTILE] missing sitekey (silent in production)");
        return;
      }

      const init = (retry = 0) => {
        if (!window.turnstile) {
          if (retry < 50) {
            setTimeout(() => init(retry + 1), 100);
          } else {
            logger.warn(
              "[TURNSTILE] script never loaded (silent in production)",
            );
            handleError();
          }
          return;
        }

        if (!containerRef.current || initializedRef.current) return;

        try {
          const widgetId = window.turnstile.render(containerRef.current, {
            sitekey: siteKey,
            size: "normal",
            execution: "execute",
            callback: handleToken,
            "expired-callback": handleExpired,
            "error-callback": handleError,
          });

          widgetIdRef.current = widgetId;
          initializedRef.current = true;

          logger.debug("[TURNSTILE] initialized with id:", widgetId);
        } catch (err) {
          logger.warn(
            "[TURNSTILE] error during render (silent in production):",
            err,
          );
        }
      };

      init();

      return () => {
        logger.debug("[TURNSTILE] cleanup");
        widgetIdRef.current = null;
        initializedRef.current = false;
      };
    }, []);

    /**
     * ⚠️ CRITIQUE
     * ❌ display: none  → PAS DE TOKEN
     * ✅ visibility: hidden → TOKEN OK
     */
    return (
      <div
        ref={containerRef}
        style={{
          width: 0,
          height: 0,
          overflow: "hidden",
          visibility: "hidden",
        }}
      />
    );
  },
);

TurnstileWidget.displayName = "TurnstileWidget";

export default TurnstileWidget;
