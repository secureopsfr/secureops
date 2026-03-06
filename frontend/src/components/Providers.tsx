"use client";

import { Toaster } from "react-hot-toast";
// Side-effect: configure Amplify before any auth hook runs.
// The OAuth listener is lazy-loaded only in OAuthCallbackHandler.
import "./AmplifyProvider";
import { ThemeProvider } from "./ThemeProvider";
import { LanguageProvider } from "./LanguageProvider";
import { AnalyticsProvider } from "./AnalyticsProvider";
import { SWRProvider } from "../providers/SWRProvider";
import ErrorBoundary, { ErrorBoundaryFallback } from "./ErrorBoundary";
import type { Locale } from "../i18n/config";

export function Providers({
  children,
  locale,
}: {
  children: React.ReactNode;
  locale: Locale;
}) {
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
            <Toaster />
          </ErrorBoundary>
        </LanguageProvider>
      </ThemeProvider>
    </SWRProvider>
  );
}
