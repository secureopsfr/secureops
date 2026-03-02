"use client";

import { useState, useCallback, useEffect } from "react";
import { fetchAuthSession } from "aws-amplify/auth";
import { AlertTriangle, Globe } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { useAuthUser } from "../../hooks/useAuthUser";
import { GenericButton } from "../buttons";
import AnimateInView from "../AnimateInView";
import Card from "../cards/Card";
import Modal from "../Modal";
import ScanLoader from "./ScanLoader";
import ScanResults from "./ScanResults";
import ScanResultsGate from "./ScanResultsGate";
import FakeScanResultsBlurred from "./FakeScanResultsBlurred";
import ScanHistoryBlock from "./ScanHistoryBlock";
import {
  runScan,
  type ScanResult,
  type ScanError,
  type ScanStepDisplay,
} from "../../services/scanService";
import {
  savePendingScanResult,
  consumePendingScanResult,
} from "../../utils/scanStorage";
import { saveScan } from "../../services/scanHistoryService";
import { showErrorToast } from "../../utils/toastNotifications";

type ScanState = "idle" | "loading" | "success" | "error";

export default function ScannerContent() {
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
    if (!authLoading && isAuthenticated) {
      const pending = consumePendingScanResult();
      if (pending) {
        setResult(pending);
        setState("success");
        // Sauvegarder dans l'historique (scan fait sans être connecté, puis connexion)
        saveScan(pending).catch(() => showErrorToast(t("scanner.saveFailed")));
      }
    }
  }, [authLoading, isAuthenticated, t]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = url.trim();
      if (!trimmed) return;
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

      try {
        await runScan(
          trimmed,
          (ev) => {
            if (ev.type === "step") {
              setSteps((prev) => [
                ...prev,
                {
                  step: ev.data.step,
                  message: ev.data.message,
                  done: ev.data.step.endsWith("_done"),
                },
              ]);
            } else if (ev.type === "result") {
              if (isAuthenticated) {
                setResult(ev.data);
                setState("success");
              } else {
                savePendingScanResult(ev.data);
                setResult(ev.data);
                setState("success");
              }
            } else if (ev.type === "error") {
              setError(ev.data);
              setState("error");
              setErrorModalOpen(true);
            } else if (ev.type === "save_failed") {
              showErrorToast(ev.data || t("scanner.saveFailed"));
            }
          },
          getToken,
        );
      } catch (err) {
        setError({
          message:
            err instanceof Error ? err.message : t("scanner.errorGeneric"),
          status_code: 500,
        });
        setState("error");
        setErrorModalOpen(true);
      }
    },
    [url, t, isAuthenticated],
  );

  const handleNewScan = useCallback(() => {
    setState("idle");
    setSteps([]);
    setResult(null);
    setError(null);
  }, []);

  const showHeader = state === "idle" || state === "error";

  return (
    <div className="mx-auto w-full max-w-[1200px] space-y-8 px-4 sm:px-6 md:px-8">
      {showHeader && (
        <AnimateInView
          initialOnly
          delay={80}
          className="page-section landing-reveal-page"
          as="section"
          aria-label="Scanner header"
        >
          <div className="page-container">
            <div className="page-header text-center">
              <h1 className="page-title">{t("scanner.title")}</h1>
              <p className="page-subtitle mt-4">{t("scanner.subtitle")}</p>
            </div>
          </div>
        </AnimateInView>
      )}

      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="section"
        aria-label="Scanner content"
      >
        <div className="scanner-content">
          {(state === "idle" || state === "error") && (
            <>
              <div className="w-full">
                <Card disableHover>
                  <div className="flex items-center gap-3 mb-4 -mt-2">
                    <Globe className="w-6 h-6 text-[rgb(var(--primary))]" />
                    <h2 className="section-title !text-left !mb-0">
                      {t("scanner.urlLabel")}
                    </h2>
                  </div>
                  <form
                    onSubmit={handleSubmit}
                    aria-label="Scan form"
                    className="space-y-4"
                  >
                    <div>
                      <label htmlFor="scan-url" className="label-form">
                        {t("scanner.urlLabel")}
                      </label>
                      <input
                        id="scan-url"
                        type="url"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder={t("scanner.urlPlaceholder")}
                        required
                        className="auth-input w-full"
                      />
                    </div>
                    <p className="text-sm text-muted-theme">
                      {t("scanner.disclaimer")}
                    </p>
                    <GenericButton
                      type="submit"
                      label={t("scanner.cta")}
                      variant="primary"
                      disabled={!url.trim()}
                    />
                  </form>
                </Card>
              </div>
              {isAuthenticated && !authLoading && (
                <ScanHistoryBlock
                  onSelectScan={(r) => {
                    setResult(r);
                    setState("success");
                  }}
                />
              )}
            </>
          )}

          {state === "loading" && <ScanLoader steps={steps} />}

          {state === "success" &&
            result &&
            !authLoading &&
            (isAuthenticated ? (
              <ScanResults result={result} onNewScan={handleNewScan} />
            ) : (
              <>
                <FakeScanResultsBlurred />
                <Modal
                  isOpen
                  onClose={() => {}}
                  title={t("scanner.gateTitle")}
                  maxWidth="420px"
                  showCloseButton={false}
                  closeOnBackdropClick={false}
                >
                  <ScanResultsGate
                    signInHref={`${lp("/connexion")}?returnTo=${encodeURIComponent(lp("/scanner"))}`}
                  />
                </Modal>
              </>
            ))}

          {state === "error" && error && (
            <Modal
              isOpen={errorModalOpen}
              onClose={() => setErrorModalOpen(false)}
              onExited={() => {
                setState("idle");
                setError(null);
              }}
              title={
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-6 h-6 text-[rgb(var(--danger))]" />
                  <span>{t("scanner.errorTitle")}</span>
                </div>
              }
              maxWidth="500px"
            >
              <p className="text-[var(--text)] leading-relaxed">
                {error.message}
              </p>
            </Modal>
          )}
        </div>
      </AnimateInView>
    </div>
  );
}
