"use client";

import Link from "next/link";
import {
  BarChart3,
  Key,
  Bot,
  Monitor,
  Server,
  BookOpen,
  Construction,
} from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import Card from "../ui/cards/Card";

export default function ScannerHub() {
  const { t, lp } = useLanguage();

  const sectionGestion = [
    {
      id: "suivi-scans",
      titleKey: "scanner.hub.cardSuiviScans",
      bodyKey: "scanner.hub.cardSuiviScansBody",
      href: lp("/scanner/vue-d-ensemble"),
      icon: BarChart3,
    },
    {
      id: "cles-api",
      titleKey: "scanner.hub.cardClesApi",
      bodyKey: "scanner.hub.cardClesApiBody",
      href: lp("/scanner/cles-api"),
      icon: Key,
    },
    {
      id: "documentation",
      titleKey: "scanner.hub.cardDocs",
      bodyKey: "scanner.hub.cardDocsBody",
      href: lp("/scanner/docs"),
      icon: BookOpen,
    },
  ];

  const sectionScanner = [
    {
      id: "crawlers",
      titleKey: "scanner.hub.cardCrawlers",
      bodyKey: "scanner.hub.cardCrawlersBody",
      href: lp("/scanner/crawlers"),
      icon: Bot,
    },
    {
      id: "scan-frontend",
      titleKey: "scanner.hub.cardScanFrontend",
      bodyKey: "scanner.hub.cardScanFrontendBody",
      href: lp("/scanner/analyses"),
      icon: Monitor,
    },
    {
      id: "scan-backend",
      titleKey: "scanner.hub.cardScanBackend",
      bodyKey: "scanner.hub.cardScanBackendBody",
      href: lp("/scanner/backend"),
      icon: Server,
    },
    {
      id: "scans-personnalises",
      titleKey: "scanner.hub.cardScansPersonnalises",
      bodyKey: "scanner.hub.cardScansPersonnalisesBody",
      href: lp("/scanner/scans-personnalises"),
      icon: Construction,
    },
  ];

  const renderCard = (card: (typeof sectionGestion)[0]) => {
    const Icon = card.icon;
    return (
      <Link key={card.id} href={card.href} className="block h-full">
        <Card
          disableHover
          className="h-full flex flex-col pt-6 transition-all hover:border-[rgb(var(--primary))] hover:shadow-lg cursor-pointer"
        >
          <div className="flex items-center gap-3 mb-3">
            <Icon
              className="w-6 h-6 shrink-0"
              style={{ color: "rgb(var(--primary))" }}
            />
            <h3 className="section-title !text-left !mb-0">
              {t(card.titleKey)}
            </h3>
          </div>
          <p className="text-sm text-[var(--muted)] flex-1">
            {t(card.bodyKey)}
          </p>
        </Card>
      </Link>
    );
  };

  return (
    <div className="space-y-6 w-full">
      <div className="text-center mb-6 pt-6">
        <h1 className="page-title mb-2">{t("scanner.hub.title")}</h1>
        <p className="page-subtitle mt-0 max-w-2xl mx-auto">
          {t("scanner.hub.subtitle")}
        </p>
      </div>

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
