"use client";

import { AlertTriangle, ShieldAlert, Timer, WandSparkles } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { GenericButton } from "../buttons";
import Card from "../ui/cards/Card";
import EditableUrlList, { EDITABLE_URL_LIST_MAX } from "./EditableUrlList";
import FloatingActionDock from "./FloatingActionDock";
import type { CrawlUrlEntry } from "../../services/crawlService";

interface CrawlValidationStepProps {
  urls: CrawlUrlEntry[];
  /** Nombre d'URLs initialement identifiées par le crawl (avant édition manuelle). */
  identifiedCount?: number;
  startUrl: string;
  /** True si le crawl a été interrompu par le timeout (résultats partiels). */
  timeoutReached?: boolean;
  /** True si timeout sur le crawler HTML. */
  timeoutHtml?: boolean;
  /** True si timeout sur le crawler avancé. */
  timeoutPlaywright?: boolean;
  /** True si une signature anti-bot explicite a été détectée. */
  antiBotSignatureDetected?: boolean;
  /** True si peu d'URLs ont été découvertes (suspicion liée aux protections anti-bot). */
  antiBotLowUrlSuspected?: boolean;
  /** True si trop de requêtes 403 (protection anti-bot, WAF) ; crawl arrêté. */
  requestsBlocked?: boolean;
  /** True si blocage 403 sur le crawler HTML. */
  requestsBlockedHtml?: boolean;
  /** True si blocage 403 sur le crawler avancé. */
  requestsBlockedPlaywright?: boolean;
  /** Maximum de 403 consécutifs observés pendant l'exploration. */
  maxConsecutive403?: number;
  /** Chemins Disallow extraits de robots.txt. */
  disallowPaths?: string[];
  /** Autorise l'ajout manuel d'URL depuis cette étape. */
  allowManualAdd?: boolean;
  /** Si true, autorise les URLs complètes avec path (utile pour endpoints API). */
  allowFullUrlAdd?: boolean;
  /** Autorise l'action de lancement du scan depuis cette étape. */
  allowLaunchScan?: boolean;
  /** Clé i18n du libellé du bouton d'action principal. */
  launchButtonLabelKey?: string;
  /** Autorise la suppression d'URLs depuis la liste. */
  allowUrlRemoval?: boolean;
  /** Affiche l'action flottante "Nouveau crawl". */
  showFloatingBackAction?: boolean;
  /** Active une version plus compacte (utile en popup). */
  compact?: boolean;
  onUrlsChange: (urls: CrawlUrlEntry[]) => void;
  onLaunchScan: () => void;
  onBack: () => void;
}

export default function CrawlValidationStep({
  urls,
  identifiedCount,
  startUrl,
  timeoutReached,
  timeoutHtml,
  timeoutPlaywright,
  antiBotSignatureDetected,
  antiBotLowUrlSuspected,
  requestsBlocked,
  requestsBlockedHtml,
  requestsBlockedPlaywright,
  maxConsecutive403 = 0,
  disallowPaths = [],
  allowManualAdd = true,
  allowFullUrlAdd = false,
  allowLaunchScan = true,
  launchButtonLabelKey = "scanner.launchScanFromList",
  allowUrlRemoval = true,
  showFloatingBackAction = true,
  compact = false,
  onUrlsChange,
  onLaunchScan,
  onBack,
}: CrawlValidationStepProps) {
  const { t } = useLanguage();
  const hasWarnings =
    timeoutReached ||
    antiBotSignatureDetected ||
    antiBotLowUrlSuspected ||
    requestsBlocked;
  const timeoutCrawlers = [
    timeoutHtml ? t("scanner.crawlEngineHtmlLabel") : null,
    timeoutPlaywright ? t("scanner.crawlEngineAdvancedLabel") : null,
  ]
    .filter(Boolean)
    .join(", ");
  const blockedCrawlers = [
    requestsBlockedHtml ? t("scanner.crawlEngineHtmlLabel") : null,
    requestsBlockedPlaywright ? t("scanner.crawlEngineAdvancedLabel") : null,
  ]
    .filter(Boolean)
    .join(", ");
  const isOverUrlLimit = urls.length > EDITABLE_URL_LIST_MAX;
  const displayIdentifiedCount = identifiedCount ?? urls.length;
  const bodyScrollClass = compact ? "min-h-0 flex-1 overflow-y-auto pr-1" : "";

  return (
    <Card
      disableHover
      className={`mx-auto max-w-5xl ${compact ? "flex h-[78vh] flex-col p-4 md:p-5" : "p-6 md:p-7"}`}
    >
      <div className="mb-5 rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)]/40 p-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <h3 className="section-title !mb-0 !text-left text-[1.35rem]">
              {t("scanner.crawlValidationTitle")}
            </h3>
            <p className="text-sm text-[var(--muted)]">
              {t("scanner.crawlValidationDesc")}
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--color-surface)] px-3 py-1.5">
            <WandSparkles className="h-4 w-4 text-[rgb(var(--primary))]" />
            <span className="text-sm font-medium text-[var(--text)]">
              {t("scanner.crawlValidationCount", {
                count: displayIdentifiedCount,
              })}
            </span>
          </div>
        </div>
      </div>

      <div className={bodyScrollClass}>
        {hasWarnings && (
          <div className="mb-5 space-y-2">
            {timeoutReached && (
              <div className="flex items-start gap-2 rounded-lg border border-[rgb(var(--warning))]/35 bg-[rgb(var(--warning))]/10 px-3 py-2.5">
                <Timer className="mt-0.5 h-4 w-4 shrink-0 text-[rgb(var(--warning))]" />
                <p className="text-sm text-[var(--text)]">
                  {t("scanner.crawlValidationTimeoutDesc", {
                    crawlers:
                      timeoutCrawlers || t("scanner.crawlEngineUnknownLabel"),
                  })}
                </p>
              </div>
            )}
            {antiBotSignatureDetected && (
              <div className="flex items-start gap-2 rounded-lg border border-[rgb(var(--warning))]/35 bg-[rgb(var(--warning))]/10 px-3 py-2.5">
                <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-[rgb(var(--warning))]" />
                <p className="text-sm text-[var(--text)]">
                  {t("scanner.crawlValidationAntiBotDesc")}
                </p>
              </div>
            )}
            {antiBotLowUrlSuspected && (
              <div className="flex items-start gap-2 rounded-lg border border-[rgb(var(--warning))]/35 bg-[rgb(var(--warning))]/10 px-3 py-2.5">
                <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-[rgb(var(--warning))]" />
                <p className="text-sm text-[var(--text)]">
                  {t("scanner.crawlValidationAntiBotLowUrlsDesc", {
                    count: displayIdentifiedCount,
                  })}
                </p>
              </div>
            )}
            {requestsBlocked && (
              <div className="flex items-start gap-2 rounded-lg border border-[rgb(var(--warning))]/35 bg-[rgb(var(--warning))]/10 px-3 py-2.5">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[rgb(var(--warning))]" />
                <p className="text-sm text-[var(--text)]">
                  {t("scanner.crawlValidationRequestsBlockedDesc", {
                    count: maxConsecutive403 || 5,
                    crawlers:
                      blockedCrawlers || t("scanner.crawlEngineUnknownLabel"),
                  })}
                </p>
              </div>
            )}
          </div>
        )}

        {disallowPaths.length > 0 && (
          <section className="mb-5 rounded-xl border border-[var(--border)] p-4">
            <p className="mb-2 text-sm font-medium text-[var(--text)]">
              {t("scanner.crawlValidationDisallowTitle")}
            </p>
            <div
              className={`flex flex-wrap gap-2 overflow-y-auto pr-1 ${compact ? "max-h-24" : "max-h-32"}`}
            >
              {disallowPaths.map((path, i) => (
                <code
                  key={`${path}-${i}`}
                  className="rounded-full border border-[var(--border)] bg-[var(--surface-secondary)]/40 px-2.5 py-1 text-xs text-[var(--muted)]"
                >
                  {path || "/"}
                </code>
              ))}
            </div>
          </section>
        )}

        <EditableUrlList
          urls={urls}
          onUrlsChange={onUrlsChange}
          startUrl={startUrl}
          allowFullUrlAdd={allowFullUrlAdd}
          allowUrlRemoval={allowUrlRemoval}
          allowManualAdd={allowManualAdd}
          compact={compact}
          showOverLimitAlert={true}
          t={t}
        />
      </div>

      <div className="flex flex-wrap justify-end gap-2">
        {allowLaunchScan && (
          <GenericButton
            type="button"
            label={t(launchButtonLabelKey)}
            variant="primary"
            onClick={onLaunchScan}
            disabled={isOverUrlLimit}
          />
        )}
      </div>

      {showFloatingBackAction && (
        <FloatingActionDock
          ariaLabel={t("scanner.newCrawl")}
          actions={[
            {
              key: "new-crawl",
              label: t("scanner.newCrawl"),
              variant: "outline",
              onClick: onBack,
            },
          ]}
        />
      )}
    </Card>
  );
}
