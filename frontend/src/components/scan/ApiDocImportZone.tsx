"use client";

import { useState, useRef } from "react";
import { FileUp } from "lucide-react";
import { parseApiDoc } from "../../utils/parseApiDoc";
import { showErrorToast } from "../../utils/toastNotifications";
import type { CrawlUrlEntry } from "../../services/crawlService";
import EditableUrlList from "./EditableUrlList";

const ACCEPTED_TYPES = ".json,.yaml,.yml";

interface ApiDocImportZoneProps {
  baseUrl: string;
  urls: CrawlUrlEntry[];
  onUrlsChange: (urls: CrawlUrlEntry[]) => void;
  t: (key: string) => string;
}

function processFile(
  file: File,
  baseWithScheme: string,
  onExtract: (urls: CrawlUrlEntry[]) => void,
  onError: (msg: string) => void,
  onFileName: (name: string) => void,
) {
  const reader = new FileReader();
  reader.onload = () => {
    const text = String(reader.result ?? "");
    const result = parseApiDoc(text, baseWithScheme || undefined);
    if (result.ok) {
      onFileName(file.name);
      onExtract(result.urls);
    } else {
      onError(result.error);
    }
  };
  reader.readAsText(file);
}

export default function ApiDocImportZone({
  baseUrl,
  urls,
  onUrlsChange,
  t,
}: ApiDocImportZoneProps) {
  const [fileName, setFileName] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const baseTrimmed = baseUrl.trim();
  const baseWithScheme = baseTrimmed
    ? /^https?:\/\//i.test(baseTrimmed)
      ? baseTrimmed
      : `https://${baseTrimmed}`
    : "";

  const hasBaseUrl = baseTrimmed.length > 0;
  const showDropZone = urls.length === 0;

  const handleFile = (file: File | null) => {
    if (!file) return;
    processFile(
      file,
      baseWithScheme,
      onUrlsChange,
      showErrorToast,
      setFileName,
    );
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFile(e.target.files?.[0] ?? null);
    e.target.value = "";
  };

  const handleChangeFile = () => {
    if (!hasBaseUrl) return;
    fileInputRef.current?.click();
  };

  const handleDropZoneClick = () => {
    if (!hasBaseUrl) {
      showErrorToast(t("scanner.apiDocUrlRequiredFirst"));
      return;
    }
    fileInputRef.current?.click();
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    if (!hasBaseUrl) {
      showErrorToast(t("scanner.apiDocUrlRequiredFirst"));
      return;
    }
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
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

      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        onChange={handleFileInputChange}
        className="hidden"
        aria-hidden
      />

      {showDropZone ? (
        <div
          role="button"
          tabIndex={hasBaseUrl ? 0 : -1}
          onClick={handleDropZoneClick}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              handleDropZoneClick();
            }
          }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed py-8 px-4 transition-colors ${
            hasBaseUrl
              ? `cursor-pointer ${
                  dragOver
                    ? "border-[rgb(var(--primary))] bg-[rgba(var(--primary),0.08)]"
                    : "border-[var(--border)] hover:border-[rgb(var(--primary))] hover:bg-[var(--surface-secondary)]/60"
                }`
              : "cursor-not-allowed opacity-60 border-[var(--border)] bg-[var(--surface-secondary)]/20"
          }`}
          aria-label={t("scanner.apiDocDragDrop")}
          aria-disabled={!hasBaseUrl}
        >
          <FileUp
            className={`w-10 h-10 transition-colors ${
              hasBaseUrl && dragOver
                ? "text-[rgb(var(--primary))]"
                : "text-[var(--muted)]"
            }`}
          />
          <p className="text-sm text-[var(--text)]">
            {t("scanner.apiDocDragDrop")}
          </p>
          <p className="text-xs text-[var(--muted)]">
            {hasBaseUrl
              ? ".json, .yaml, .yml — OpenAPI, Postman"
              : t("scanner.apiDocUrlRequiredFirst")}
          </p>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between gap-3 rounded-lg border border-[var(--border)] bg-[var(--color-surface)] px-3 py-2.5">
            <span className="min-w-0 truncate text-sm text-[var(--text)]">
              {fileName ?? t("scanner.apiDocEndpointsExtracted")}
            </span>
            <button
              type="button"
              onClick={handleChangeFile}
              disabled={!hasBaseUrl}
              className="shrink-0 text-sm text-[rgb(var(--primary))] hover:underline disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:no-underline"
            >
              {t("scanner.apiDocChangeFile")}
            </button>
          </div>

          <EditableUrlList
            urls={urls}
            onUrlsChange={onUrlsChange}
            startUrl={baseUrl || baseWithScheme}
            allowFullUrlAdd
            allowUrlRemoval
            allowManualAdd
            compact={false}
            showOverLimitAlert
            t={t}
          />
        </>
      )}
    </div>
  );
}
