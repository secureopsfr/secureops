"use client";

import { useState, useCallback } from "react";
import { AlertTriangle } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { GenericButton } from "../buttons";
import AnimateInView from "../AnimateInView";
import Card from "../cards/Card";
import Modal from "../Modal";
import ScanLoader from "./ScanLoader";
import ScanResults from "./ScanResults";
import {
  runScan,
  type ScanResult,
  type ScanError,
  type ScanStepDisplay,
} from "../../services/scanService";

type ScanState = "idle" | "loading" | "success" | "error";

export default function ScannerContent() {
  const { t } = useLanguage();
  const [url, setUrl] = useState("");
  const [state, setState] = useState<ScanState>("idle");
  const [steps, setSteps] = useState<ScanStepDisplay[]>([]);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<ScanError | null>(null);
  const [errorModalOpen, setErrorModalOpen] = useState(false);

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

      try {
        await runScan(trimmed, (ev) => {
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
            setResult(ev.data);
            setState("success");
          } else if (ev.type === "error") {
            setError(ev.data);
            setState("error");
            setErrorModalOpen(true);
          }
        });
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
    [url, t],
  );

  const handleNewScan = useCallback(() => {
    setState("idle");
    setSteps([]);
    setResult(null);
    setError(null);
  }, []);

  return (
    <div className="mx-auto max-w-2xl space-y-8">
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

      <AnimateInView
        className="landing-section landing-reveal-scanner"
        as="section"
        aria-label="Scanner content"
      >
        <div className="scanner-content">
          {(state === "idle" || state === "error") && (
            <div className="form-container">
              <Card disableHover>
                <h2 className="section-title !text-left -mt-2">
                  {t("scanner.urlLabel")}
                </h2>
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
          )}

          {state === "loading" && <ScanLoader steps={steps} />}

          {state === "success" && result && (
            <ScanResults result={result} onNewScan={handleNewScan} />
          )}

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
