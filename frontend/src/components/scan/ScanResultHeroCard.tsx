"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Card from "../ui/cards/Card";
import Badge from "../ui/Badge";
import { useLanguage } from "../LanguageProvider";
import type { ScanFinding } from "../../services/scanService";
import { getCategoryKey, getScoreBadge } from "./scanConstants";
import { formatUrlDisplay } from "../../utils/urlFormat";

interface ScanResultHeroCardProps {
  url: string;
  score: number;
  findings: ScanFinding[];
  durationSeconds?: number;
}

/** Icône globe SVG vectorielle pour fallback favicon (évite la pixellisation). */
const DefaultFavicon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-8 w-8 text-[var(--muted)]"
    aria-hidden
  >
    <circle cx="12" cy="12" r="10" />
    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    <path d="M2 12h20" />
  </svg>
);

export default function ScanResultHeroCard({
  url,
  score,
  findings,
  durationSeconds,
}: ScanResultHeroCardProps) {
  const { t } = useLanguage();
  const [faviconError, setFaviconError] = useState(false);
  const [gaugeScore, setGaugeScore] = useState(0);
  const badge = getScoreBadge(score);

  useEffect(() => {
    setFaviconError(false);
  }, [url]);

  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      setGaugeScore(score);
    });
    return () => cancelAnimationFrame(raf);
  }, [score]);

  const byCategory = findings.reduce<Record<string, number>>((acc, f) => {
    acc[f.category] = (acc[f.category] ?? 0) + 1;
    return acc;
  }, {});

  const displayUrl = formatUrlDisplay(url);
  const domain = (() => {
    try {
      return new URL(url).hostname;
    } catch {
      return displayUrl.split("/")[0] || displayUrl;
    }
  })();
  const faviconUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;

  return (
    <Card
      disableHover
      className="scanner-block overflow-hidden border-2 border-[var(--color-border)]"
    >
      <div className="p-6 sm:p-8 text-center">
        <div className="mb-4 flex justify-center">
          {faviconError ? (
            <div
              className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--color-surface-hover)]"
              aria-hidden
            >
              <DefaultFavicon />
            </div>
          ) : (
            <Image
              src={faviconUrl}
              alt=""
              width={56}
              height={56}
              className="h-14 w-14 rounded-xl object-cover"
              onError={() => setFaviconError(true)}
            />
          )}
        </div>

        <h2
          className="text-xl sm:text-2xl lg:text-3xl font-bold text-[var(--text)] break-all"
          title={url}
        >
          {displayUrl}
        </h2>

        {typeof durationSeconds === "number" && (
          <p className="text-xs sm:text-sm text-muted-theme mt-2">
            {t("scanner.duration")} {durationSeconds.toFixed(1)}
            {t("scanner.seconds")}
          </p>
        )}

        <div className="mt-6 flex flex-col items-center gap-2">
          <div
            className="relative flex h-20 w-20 flex-shrink-0 sm:h-24 sm:w-24"
            aria-hidden
          >
            <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="42"
                fill="none"
                stroke="var(--color-surface-hover)"
                strokeWidth="8"
              />
              <circle
                cx="50"
                cy="50"
                r="42"
                fill="none"
                stroke={badge.ringColor}
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={2 * Math.PI * 42}
                strokeDashoffset={2 * Math.PI * 42 * (1 - gaugeScore / 100)}
                style={{
                  transition: "stroke-dashoffset 0.8s ease-out",
                }}
              />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-2xl font-bold text-[var(--text)] sm:text-3xl">
              {score}
            </span>
          </div>
          <p className="text-base font-medium text-[var(--muted)]">
            {t(badge.labelKey)}
          </p>
        </div>

        <div className="mt-8 flex flex-col items-center gap-2">
          <span className="text-2xl font-bold text-[var(--text)] sm:text-3xl">
            {findings.length}
          </span>
          <p className="text-center text-sm font-semibold uppercase tracking-wider text-[var(--muted)]">
            {t("scanner.findings")}
          </p>
        </div>

        {Object.keys(byCategory).length > 0 && (
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {Object.entries(byCategory).map(([cat, count]) => (
              <Badge key={cat} variant="default" className="text-sm">
                {t(getCategoryKey(cat))}: {count}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}
