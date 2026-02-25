"use client";

import { Toaster } from "react-hot-toast";
// Side-effect: configure Amplify before any auth hook runs.
// The OAuth listener is lazy-loaded only in OAuthCallbackHandler.
import "./AmplifyProvider";
import { ThemeProvider } from "./ThemeProvider";
import { LanguageProvider } from "./LanguageProvider";
import { AnalyticsProvider } from "./AnalyticsProvider";
import { SWRProvider } from "../providers/SWRProvider";
import ErrorBoundary from "./ErrorBoundary";
import type { Locale } from "../i18n/config";

export function Providers({
  children,
  locale,
}: {
  children: React.ReactNode;
  locale: Locale;
}) {
  return (
    <ErrorBoundary
      showDetails={process.env.NODE_ENV === "development"}
      fallbackMessage="Une erreur inattendue s'est produite. Nous travaillons à la résoudre."
    >
      <SWRProvider>
        <ThemeProvider>
          <LanguageProvider initialLocale={locale}>
            <AnalyticsProvider>{children}</AnalyticsProvider>
            <Toaster />
          </LanguageProvider>
        </ThemeProvider>
      </SWRProvider>
    </ErrorBoundary>
  );
}
