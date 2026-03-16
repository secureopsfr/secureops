"use client";

import { useState, useRef } from "react";
import { FileUp, Link2, Loader2 } from "lucide-react";
import { GenericButton } from "../buttons";
import { parseApiDoc, type ParseApiDocResult } from "../../utils/parseApiDoc";
import { showErrorToast } from "../../utils/toastNotifications";
import type { CrawlUrlEntry } from "../../services/crawlService";

interface ApiDocImportZoneProps {
  baseUrl: string;
  onExtract: (urls: CrawlUrlEntry[]) => void;
  t: (key: string) => string;
}

export default function ApiDocImportZone({
  baseUrl,
  onExtract,
  t,
}: ApiDocImportZoneProps) {
  const [specUrl, setSpecUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const baseTrimmed = baseUrl.trim();
  const baseWithScheme = baseTrimmed
    ? /^https?:\/\//i.test(baseTrimmed)
      ? baseTrimmed
      : `https://${baseTrimmed}`
    : "";

  const handleFetchSpec = async () => {
    const url = specUrl.trim();
    if (!url) {
      showErrorToast(t("scanner.apiDocUrlRequired"));
      return;
    }
    let resolved = url;
    if (!/^https?:\/\//i.test(url)) {
      resolved = baseWithScheme
        ? `${baseWithScheme.replace(/\/+$/, "")}/${url.replace(/^\//, "")}`
        : `https://${url}`;
    }
    setLoading(true);
    try {
      const res = await fetch(resolved, { method: "GET" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      const result = parseApiDoc(text, baseWithScheme || undefined);
      if (result.ok) {
        onExtract(result.urls);
      } else {
        showErrorToast(result.error);
      }
    } catch (err) {
      showErrorToast(
        err instanceof Error ? err.message : t("scanner.apiDocFetchError"),
      );
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result ?? "");
      const result = parseApiDoc(text, baseWithScheme || undefined);
      if (result.ok) {
        onExtract(result.urls);
      } else {
        showErrorToast(result.error);
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-secondary)]/40 p-4 space-y-4">
      <div>
        <h4 className="text-sm font-medium text-[var(--text)] mb-1">
          {t("scanner.apiDocImportTitle")}
        </h4>
        <p className="text-xs text-[var(--muted)]">
          {t("scanner.apiDocImportDesc")}
        </p>
      </div>
      <div className="flex flex-col gap-2">
        <div className="flex gap-2">
          <input
            type="url"
            inputMode="url"
            value={specUrl}
            onChange={(e) => setSpecUrl(e.target.value)}
            placeholder={t("scanner.apiDocUrlPlaceholder")}
            className="auth-input flex-1"
            disabled={loading}
            aria-label={t("scanner.apiDocUrlPlaceholder")}
          />
          <GenericButton
            type="button"
            label={t("scanner.apiDocExtractEndpoints")}
            icon={
              loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Link2 className="w-4 h-4" />
              )
            }
            variant="primary"
            onClick={handleFetchSpec}
            disabled={loading || !baseTrimmed}
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[var(--muted)]">{t("common.or")}</span>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,.yaml,.yml"
            onChange={handleFileUpload}
            className="hidden"
            aria-hidden
          />
          <GenericButton
            type="button"
            label={t("scanner.apiDocUploadFile")}
            icon={<FileUp className="h-4 w-4" />}
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
          />
        </div>
      </div>
    </div>
  );
}
