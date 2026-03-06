"use client";

import { useLanguage } from "../LanguageProvider";
import { LoadingSpinner } from "../LoadingScreen";
import Card from "../ui/cards/Card";
import { Check } from "lucide-react";
import type { ScanStepDisplay } from "../../services/scanService";

interface ScanLoaderProps {
  steps: ScanStepDisplay[];
}

export default function ScanLoader({ steps }: ScanLoaderProps) {
  const { t } = useLanguage();

  return (
    <Card disableHover className="mx-auto max-w-4xl p-14 text-center">
      <h3 className="section-title -mt-2 mb-8 text-center text-2xl">
        {t("scanner.loading")}
      </h3>
      {steps.length === 0 ? (
        <div className="flex items-center justify-center gap-4 text-base text-muted-theme">
          <LoadingSpinner size="md" />
          <span>{t("scanner.loading")}</span>
        </div>
      ) : (
        <ul className="mx-auto flex w-full max-w-md flex-col items-stretch space-y-4">
          {steps.map((s, i) => (
            <li
              key={`${s.step}-${i}`}
              className="flex items-center gap-4 text-base"
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center">
                {s.done ? (
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[rgba(var(--success),0.2)] text-[rgb(var(--success))]">
                    <Check className="h-4 w-4" strokeWidth={3} />
                  </span>
                ) : (
                  <LoadingSpinner size="md" />
                )}
              </span>
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
