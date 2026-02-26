"use client";

import { useLanguage } from "../LanguageProvider";
import { Check } from "lucide-react";

interface ScanLoaderProps {
  steps: { step: string; message: string; done?: boolean }[];
}

export default function ScanLoader({ steps }: ScanLoaderProps) {
  const { t } = useLanguage();

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--color-surface-input)] p-6">
      <p className="mb-4 text-sm font-medium text-[var(--text)]">
        {t("scanner.loading")}
      </p>
      <ul className="space-y-2">
        {steps.map((s, i) => (
          <li
            key={`${s.step}-${i}`}
            className="flex items-center gap-3 text-sm text-[var(--muted)]"
          >
            {s.done ? (
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-green-500/20 text-green-600 dark:text-green-400">
                <Check className="h-3 w-3" strokeWidth={3} />
              </span>
            ) : (
              <span className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--border)] border-t-[var(--primary)]" />
            )}
            <span className={s.done ? "text-[var(--text)]" : ""}>
              {s.message}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
