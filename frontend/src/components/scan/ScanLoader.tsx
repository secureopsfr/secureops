"use client";

import { useLanguage } from "../LanguageProvider";
import { LoadingSpinner } from "../LoadingScreen";
import Card from "../cards/Card";
import { Check } from "lucide-react";
import type { ScanStepDisplay } from "../../services/scanService";

interface ScanLoaderProps {
  steps: ScanStepDisplay[];
}

export default function ScanLoader({ steps }: ScanLoaderProps) {
  const { t } = useLanguage();

  return (
    <Card disableHover className="p-6">
      <h3 className="section-title !text-left -mt-2 mb-4">
        {t("scanner.loading")}
      </h3>
      {steps.length === 0 ? (
        <div className="flex items-center gap-3 text-sm text-muted-theme">
          <LoadingSpinner size="sm" />
          <span>{t("scanner.loading")}</span>
        </div>
      ) : (
        <ul className="space-y-2">
          {steps.map((s, i) => (
            <li
              key={`${s.step}-${i}`}
              className="flex items-center gap-3 text-sm"
            >
              {s.done ? (
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[rgba(var(--success),0.2)] text-[rgb(var(--success))]">
                  <Check className="h-3 w-3" strokeWidth={3} />
                </span>
              ) : (
                <LoadingSpinner size="sm" />
              )}
              <span className={s.done ? "" : "text-muted-theme"}>
                {s.message}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
