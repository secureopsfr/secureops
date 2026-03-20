"use client";

import { createPortal } from "react-dom";
import { useEffect, useState } from "react";
import { Toaster } from "react-hot-toast";
// Side-effect: configure Amplify before any auth hook runs.
import "./AmplifyProvider";
import { ThemeProvider } from "./ThemeProvider";
import { LanguageProvider } from "./LanguageProvider";
import { AnalyticsProvider } from "./AnalyticsProvider";
import { SWRProvider } from "../providers/SWRProvider";
import ErrorBoundary, { ErrorBoundaryFallback } from "./ErrorBoundary";
import type { Locale } from "../i18n/config";

/** z-index maximum pour que les toasts restent au-dessus des modals (blur) partout. */
const TOAST_Z_INDEX = 2147483647;

export function Providers({
  children,
  locale,
}: {
  children: React.ReactNode;
  locale: Locale;
}) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <SWRProvider>
      <ThemeProvider>
        <LanguageProvider initialLocale={locale}>
          <ErrorBoundary
            showDetails={process.env.NODE_ENV === "development"}
            renderFallback={(error, errorInfo, actions) => (
              <ErrorBoundaryFallback
                error={error}
                errorInfo={errorInfo}
                showDetails={process.env.NODE_ENV === "development"}
                onReset={actions.onReset}
                onReload={actions.onReload}
              />
            )}
          >
            <AnalyticsProvider>{children}</AnalyticsProvider>
            {mounted &&
              createPortal(
                <div
                  style={{
                    position: "fixed",
                    zIndex: TOAST_Z_INDEX,
                    inset: 0,
                    pointerEvents: "none",
                    isolation: "isolate",
                  }}
                  aria-hidden="true"
                >
                  <div style={{ pointerEvents: "auto", position: "relative" }}>
                    <Toaster
                      position="bottom-center"
                      containerStyle={{
                        zIndex: TOAST_Z_INDEX,
                      }}
                      toastOptions={{
                        style: { position: "relative" },
                      }}
                    />
                  </div>
                </div>,
                document.body,
              )}
          </ErrorBoundary>
        </LanguageProvider>
      </ThemeProvider>
    </SWRProvider>
  );
}
