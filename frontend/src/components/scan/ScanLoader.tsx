"use client";

import { useLanguage } from "../LanguageProvider";
import { LoadingSpinner } from "../LoadingScreen";
import Card from "../ui/cards/Card";
import { Check } from "lucide-react";
import type { ScanStepDisplay } from "../../services/scanService";

interface ScanLoaderProps {
  steps: ScanStepDisplay[];
  /** Clé i18n pour le titre (défaut: scanner.loading). */
  titleKey?: string;
  /** Mode both : affiche 3 colonnes (HTML | Commun | Playwright). */
  crawlMode?: "html" | "playwright" | "both";
}

const STEP_I18N_KEYS: Record<string, string> = {
  crawl_html_done: "scanner.crawlHtmlDone",
  crawl_playwright_done: "scanner.crawlPlaywrightDone",
  crawl_stopping_other: "scanner.crawlStoppingOther",
  crawl_merging: "scanner.crawlMerging",
};

function StepRow({
  step,
  message,
  done,
  asLi = false,
}: {
  step: string;
  message: string;
  done: boolean;
  asLi?: boolean;
}) {
  const { t } = useLanguage();
  const displayMessage = STEP_I18N_KEYS[step]
    ? t(STEP_I18N_KEYS[step])
    : message;
  const Wrapper = asLi ? "li" : "div";
  return (
    <Wrapper className="flex items-center gap-4 text-base">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center">
        {done ? (
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[rgba(var(--success),0.2)] text-[rgb(var(--success))]">
            <Check className="h-4 w-4" strokeWidth={3} />
          </span>
        ) : (
          <LoadingSpinner size="md" />
        )}
      </span>
      <span className={done ? "" : "text-muted-theme"}>{displayMessage}</span>
    </Wrapper>
  );
}

function getStepColumn(step: string): "html" | "common" | "playwright" {
  if (step.startsWith("html_")) return "html";
  if (step.startsWith("playwright_")) return "playwright";
  return "common";
}

export default function ScanLoader({
  steps,
  titleKey = "scanner.loading",
  crawlMode,
}: ScanLoaderProps) {
  const { t } = useLanguage();

  const htmlSteps = steps.filter((s) => s.step.startsWith("html_"));
  const playwrightSteps = steps.filter((s) => s.step.startsWith("playwright_"));
  const useTripleColumn =
    crawlMode === "both" &&
    (htmlSteps.length > 0 || playwrightSteps.length > 0);

  return (
    <Card disableHover className="mx-auto max-w-4xl p-14 text-center">
      <h3 className="section-title -mt-2 mb-8 text-center text-2xl">
        {t(titleKey)}
      </h3>
      {steps.length === 0 ? (
        <div className="flex items-center justify-center gap-4 text-base text-muted-theme">
          <LoadingSpinner size="md" />
          <span>{t(titleKey)}</span>
        </div>
      ) : useTripleColumn ? (
        <div className="mx-auto w-full max-w-4xl">
          <div className="mb-3 grid grid-cols-3 gap-4 text-sm font-semibold text-[var(--text)]">
            <div>{t("scanner.crawlColumnHtml")}</div>
            <div>{t("scanner.crawlColumnCommon")}</div>
            <div>{t("scanner.crawlColumnPlaywright")}</div>
          </div>
          <div className="flex flex-col space-y-3">
            {steps.map((s, i) => {
              const col = getStepColumn(s.step);
              return (
                <div key={`${s.step}-${i}`} className="grid grid-cols-3 gap-4">
                  <div className="min-w-0">
                    {col === "html" && (
                      <StepRow
                        step={s.step}
                        message={s.message}
                        done={s.done}
                      />
                    )}
                  </div>
                  <div className="min-w-0">
                    {col === "common" && (
                      <StepRow
                        step={s.step}
                        message={s.message}
                        done={s.done}
                      />
                    )}
                  </div>
                  <div className="min-w-0">
                    {col === "playwright" && (
                      <StepRow
                        step={s.step}
                        message={s.message}
                        done={s.done}
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <ul className="mx-auto flex w-full max-w-md flex-col items-stretch space-y-4">
          {steps.map((s, i) => (
            <StepRow
              key={`${s.step}-${i}`}
              step={s.step}
              message={s.message}
              done={s.done}
              asLi
            />
          ))}
        </ul>
      )}
    </Card>
  );
}
