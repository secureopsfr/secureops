"use client";

import { useState, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import { fetchAuthSession } from "aws-amplify/auth";
import { useLanguage } from "../LanguageProvider";
import { useAuthUser } from "../../hooks/useAuthUser";
import { GenericButton } from "../buttons";
import Modal from "../ui/Modal";
import { useRouter } from "next/navigation";
import ScanLoader from "../scan/ScanLoader";
import ScanResultsGate from "../scan/ScanResultsGate";
import FakeScanResultsBlurred from "../scan/FakeScanResultsBlurred";
import {
  runScan,
  type ScanResult,
  type ScanError,
  type ScanStepDisplay,
} from "../../services/scanService";
import { normalizeScanUrl } from "../../utils/scanUrl";
import {
  savePendingScanResult,
  hasPendingScanResult,
} from "../../utils/scanStorage";
import { showErrorToast } from "../../utils/toastNotifications";

type ScanState = "idle" | "loading" | "success" | "error";

/**
 * Bloc de scan basique sur la landing : champ URL + CTA, scan direct (pas de crawler),
 * gate connexion pour les résultats si non authentifié.
 */
export default function LandingScanBlock() {
  const router = useRouter();
  const { t, lp } = useLanguage();
  const { isAuthenticated, isLoading: authLoading } = useAuthUser({
    listenToAuthEvents: true,
  });
  const [url, setUrl] = useState("");
  const [state, setState] = useState<ScanState>("idle");
  const [steps, setSteps] = useState<ScanStepDisplay[]>([]);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<ScanError | null>(null);
  const [errorModalOpen, setErrorModalOpen] = useState(false);

  useEffect(() => {
    if (!authLoading && isAuthenticated && hasPendingScanResult()) {
      router.push(lp("/scanner"));
    }
  }, [authLoading, isAuthenticated, router, lp]);

  const runScanOnUrl = useCallback(
    (urlToScan: string) => {
      setState("loading");
      setSteps([]);
      setResult(null);
      setError(null);
      setErrorModalOpen(false);

      const getToken = isAuthenticated
        ? async () => {
            try {
              const session = await fetchAuthSession();
              return session.tokens?.accessToken?.toString() ?? null;
            } catch {
              return null;
            }
          }
        : undefined;

      runScan(
        urlToScan,
        (ev) => {
          if (ev.type === "step") {
            const done = ev.data.step.endsWith("_done");
            setSteps((prev) => {
              if (done && prev.length > 0) {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  step: ev.data.step,
                  message: ev.data.message,
                  done: true,
                };
                return updated;
              }
              return [
                ...prev,
                {
                  step: ev.data.step,
                  message: ev.data.message,
                  done: false,
                },
              ];
            });
          } else if (ev.type === "result") {
            savePendingScanResult(ev.data);
            setResult(ev.data);
            if (!isAuthenticated) setState("success");
          } else if (ev.type === "save_done") {
            // Résultats affichés sur la page Scanner
          } else if (ev.type === "error") {
            setError(ev.data);
            setState("error");
            setErrorModalOpen(true);
          } else if (ev.type === "save_failed") {
            showErrorToast(ev.data || t("scanner.saveFailed"));
          }
        },
        getToken,
      ).catch((err) => {
        setError({
          message:
            err instanceof Error ? err.message : t("scanner.errorGeneric"),
          status_code: 500,
        });
        setState("error");
        setErrorModalOpen(true);
      });
    },
    [t, isAuthenticated],
  );

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = url.trim();
      if (!trimmed) return;
      runScanOnUrl(normalizeScanUrl(trimmed));
    },
    [url, runScanOnUrl],
  );

  const signInHref = `${lp("/connexion")}?returnTo=${encodeURIComponent(lp("/scanner"))}`;

  if (state === "loading") {
    const overlay = (
      <div className="scan-loading-overlay fixed inset-0 z-[60]">
        <ScanLoader
          steps={steps}
          titleKey="scanner.loading"
          onAnimationComplete={
            result
              ? () => {
                  router.push(lp("/scanner"));
                }
              : undefined
          }
        />
      </div>
    );
    return typeof document !== "undefined"
      ? createPortal(overlay, document.body)
      : overlay;
  }

  if (state === "success" && result && !authLoading && !isAuthenticated) {
    return (
      <div className="landing-scan-block mt-8 space-y-4">
        <FakeScanResultsBlurred />
        <Modal
          isOpen
          onClose={() => {}}
          title={t("scanner.gateTitle")}
          maxWidth="420px"
          showCloseButton={false}
          closeOnBackdropClick={false}
        >
          <ScanResultsGate signInHref={signInHref} />
        </Modal>
      </div>
    );
  }

  return (
    <div className="landing-scan-block mt-8 mb-12 text-left w-full max-w-3xl mx-auto">
      <p className="landing-scan-intro mb-4 text-base text-[var(--text)] w-full text-left">
        {t("home.scanIntro")}
      </p>
      <form
        onSubmit={handleSubmit}
        className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center w-full"
        aria-label={t("scanner.ariaForm")}
      >
        <input
          id="landing-scan-url"
          type="text"
          inputMode="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder={t("scheduledScans.urlPlaceholder")}
          required
          className="auth-input flex-1 min-w-0"
          aria-label={t("scheduledScans.urlLabel")}
        />
        <GenericButton
          type="submit"
          label={t("scanner.cta")}
          variant="primary"
          className="shrink-0"
        />
      </form>

      {state === "error" && error && (
        <Modal
          isOpen={errorModalOpen}
          onClose={() => setErrorModalOpen(false)}
          onExited={() => {
            setState("idle");
            setError(null);
          }}
          title={t("scanner.errorTitle")}
          maxWidth="500px"
        >
          <p className="text-[var(--text)] leading-relaxed">
            {error.i18nKey ? t(error.i18nKey) : error.message}
          </p>
        </Modal>
      )}
    </div>
  );
}
