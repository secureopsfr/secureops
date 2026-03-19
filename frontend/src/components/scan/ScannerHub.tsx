"use client";

import Link from "next/link";
import {
  BarChart3,
  Terminal,
  Bot,
  ShieldCheck,
  Bug,
  Flame,
  BookOpen,
  Construction,
  Gauge,
} from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import AnimateInView from "../AnimateInView";
import Card from "../ui/cards/Card";
import { useAuthUser } from "../../hooks/useAuthUser";
import { useQuota } from "../../hooks/useQuota";

export default function ScannerHub() {
  const { t, lp } = useLanguage();
  const { isAuthenticated } = useAuthUser({});
  const { quota, loading: quotaLoading } = useQuota(isAuthenticated);

  const sectionGestion = [
    {
      id: "suivi-scans",
      titleKey: "scanner.hub.cardSuiviScans",
      bodyKey: "scanner.hub.cardSuiviScansBody",
      href: lp("/scanner/vue-d-ensemble"),
      icon: BarChart3,
      comingSoon: false,
    },
    {
      id: "cles-api",
      titleKey: "scanner.hub.cardApiPublique",
      bodyKey: "scanner.hub.cardApiPubliqueBody",
      href: lp("/scanner/cles-api"),
      icon: Terminal,
      comingSoon: false,
    },
    {
      id: "documentation",
      titleKey: "scanner.hub.cardDocs",
      bodyKey: "scanner.hub.cardDocsBody",
      href: lp("/scanner/docs"),
      icon: BookOpen,
      comingSoon: false,
    },
  ];

  const sectionScanner = [
    {
      id: "crawlers",
      titleKey: "scanner.hub.cardCrawlers",
      bodyKey: "scanner.hub.cardCrawlersBody",
      href: lp("/scanner/crawlers"),
      icon: Bot,
      comingSoon: false,
    },
    {
      id: "scan-passif",
      titleKey: "scanner.hub.cardScanPassive",
      bodyKey: "scanner.hub.cardScanPassiveBody",
      href: lp("/scanner/analyses?mode=passive"),
      icon: ShieldCheck,
      comingSoon: false,
    },
    {
      id: "scan-intrusif",
      titleKey: "scanner.hub.cardScanIntrusive",
      bodyKey: "scanner.hub.cardScanIntrusiveBody",
      href: lp("/scanner/analyses?mode=intrusive"),
      icon: Bug,
      comingSoon: true,
    },
    {
      id: "scan-destructeur",
      titleKey: "scanner.hub.cardScanDestructive",
      bodyKey: "scanner.hub.cardScanDestructiveBody",
      href: lp("/scanner/analyses?mode=destructive"),
      icon: Flame,
      comingSoon: true,
    },
    {
      id: "scans-personnalises",
      titleKey: "scanner.hub.cardScansPersonnalises",
      bodyKey: "scanner.hub.cardScansPersonnalisesBody",
      href: lp("/scanner/scans-personnalises"),
      icon: Construction,
      comingSoon: true,
    },
  ];

  type CardItem = (typeof sectionGestion)[0] | (typeof sectionScanner)[0];
  const isComingSoon = (c: CardItem): c is CardItem & { comingSoon: true } =>
    "comingSoon" in c && c.comingSoon === true;

  const renderCard = (card: CardItem) => {
    const Icon = card.icon;
    const soon = isComingSoon(card);

    const cardContent = (
      <Card
        disableHover
        className={
          "h-full flex flex-col pt-6 transition-all " +
          (soon
            ? "opacity-55 cursor-not-allowed border-dashed"
            : "hover:border-[rgb(var(--primary))] hover:shadow-lg cursor-pointer")
        }
      >
        <div className={`flex items-center gap-3 ${soon ? "mb-1" : "mb-3"}`}>
          <Icon
            className="w-6 h-6 shrink-0"
            style={{ color: "rgb(var(--primary))" }}
          />
          <h3 className="section-title !text-left !mb-0">{t(card.titleKey)}</h3>
        </div>
        {soon && (
          <span className="inline-block text-xs font-medium text-[rgb(var(--primary))] bg-[rgba(var(--primary),0.12)] px-2.5 py-1 rounded-full w-fit mb-3">
            {t("scanner.hub.comingSoon")}
          </span>
        )}
        <p className="text-sm text-[var(--muted)] flex-1">{t(card.bodyKey)}</p>
      </Card>
    );

    if (soon) {
      return (
        <div key={card.id} className="block h-full" aria-disabled="true">
          {cardContent}
        </div>
      );
    }

    return (
      <Link key={card.id} href={card.href} className="block h-full">
        {cardContent}
      </Link>
    );
  };

  return (
    <div className="space-y-6 w-full">
      <AnimateInView
        initialOnly
        delay={80}
        className="page-section landing-reveal-page"
        as="section"
        aria-label={t("scanner.ariaHeader")}
      >
        <div className="page-container">
          <div className="page-header text-center mb-1">
            <h1 className="page-title mb-2">{t("scanner.hub.title")}</h1>
            <p className="page-subtitle mt-0 max-w-2xl mx-auto">
              {t("scanner.hub.subtitle")}
            </p>
            {isAuthenticated && (
              <div className="flex justify-center mt-4">
                <span
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-full border text-sm font-medium transition-colors ${
                    quotaLoading || quota === null
                      ? "border-[var(--color-border)] text-[var(--muted)] bg-transparent animate-pulse"
                      : quota.remaining === 0
                        ? "border-[rgb(var(--danger))] text-[rgb(var(--danger))] bg-[rgba(var(--danger),0.08)]"
                        : quota.remaining <= Math.ceil(quota.limit * 0.2)
                          ? "border-[var(--color-warning,#f59e0b)] text-[var(--color-warning,#f59e0b)] bg-[rgba(245,158,11,0.08)]"
                          : "border-[var(--color-border)] text-[var(--text)] bg-transparent"
                  }`}
                >
                  <Gauge className="w-4 h-4 shrink-0" />
                  {quotaLoading || quota === null
                    ? "— / 50"
                    : quota.remaining === 0
                      ? t("header.quotaExhausted", { limit: quota.limit })
                      : t("header.quotaRemaining", {
                          remaining: quota.remaining,
                          limit: quota.limit,
                        })}
                </span>
              </div>
            )}
          </div>
        </div>
      </AnimateInView>

      <section className="space-y-4">
        <h2 className="text-xl sm:text-2xl font-semibold text-[var(--text)] pb-3 border-b border-[var(--color-border)]/60">
          {t("scanner.hub.sectionVueEnsemble")}
        </h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 items-stretch">
          {sectionGestion.map(renderCard)}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl sm:text-2xl font-semibold text-[var(--text)] pb-3 border-b border-[var(--color-border)]/60">
          {t("scanner.hub.sectionScanner")}
        </h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 sm:grid-rows-2 lg:grid-rows-none sm:min-h-[360px] lg:min-h-0 items-stretch">
          {sectionScanner.map(renderCard)}
        </div>
      </section>
    </div>
  );
}
