"use client";

import type { FormEvent } from "react";
import { Globe } from "lucide-react";
import Card from "../ui/cards/Card";
import { DropdownSelector, GenericButton } from "../buttons";
import { useLanguage } from "../LanguageProvider";

interface ScanLaunchBubbleProps {
  url: string;
  onUrlChange: (value: string) => void;
  scanTarget: "frontend" | "backend" | "both";
  onScanTargetChange: (value: "frontend" | "backend" | "both") => void;
  showTargetSelector?: boolean;
  onSubmit: (e: FormEvent) => void;
  loading?: boolean;
}

export default function ScanLaunchBubble({
  url,
  onUrlChange,
  scanTarget,
  onScanTargetChange,
  showTargetSelector = true,
  onSubmit,
  loading = false,
}: ScanLaunchBubbleProps) {
  const { t } = useLanguage();

  return (
    <Card disableHover>
      <form
        onSubmit={onSubmit}
        className="space-y-4"
        aria-label={t("scanner.ariaForm")}
      >
        <div className="flex items-center gap-3 mb-4 -mt-2">
          <Globe className="w-6 h-6 text-[rgb(var(--primary))]" />
          <h2 className="section-title !text-left !mb-0">
            {t("scheduledScans.newScheduledScanTitle")}
          </h2>
        </div>

        <div>
          <label
            htmlFor="scan-type-url"
            className="block text-sm font-medium text-[var(--text)] mb-1"
          >
            {t("scheduledScans.urlLabel")}
          </label>
          <input
            id="scan-type-url"
            type="text"
            inputMode="url"
            value={url}
            onChange={(e) => onUrlChange(e.target.value)}
            placeholder={t("scheduledScans.urlPlaceholder")}
            required
            className="auth-input w-full"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-[var(--text)] mb-2">
            {t("scanner.targetLabel")}
          </label>
          {showTargetSelector ? (
            <DropdownSelector
              selectedValue={scanTarget}
              onChange={(value) =>
                onScanTargetChange(value as "frontend" | "backend" | "both")
              }
              options={[
                { value: "frontend", label: t("scanner.targetFrontend") },
                { value: "backend", label: t("scanner.targetBackend") },
                { value: "both", label: t("scanner.targetBoth") },
              ]}
              width="100%"
            />
          ) : (
            <div className="auth-input w-full">
              {scanTarget === "backend"
                ? t("scanner.targetBackend")
                : scanTarget === "both"
                  ? t("scanner.targetBoth")
                  : t("scanner.targetFrontend")}
            </div>
          )}
        </div>

        <GenericButton
          type="submit"
          label={t("scanner.cta")}
          variant="primary"
          disabled={!url.trim()}
          loading={loading}
        />
      </form>
    </Card>
  );
}
