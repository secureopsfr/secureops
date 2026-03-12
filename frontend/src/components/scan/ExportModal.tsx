"use client";

import Modal from "../ui/Modal";
import { LoadingSpinner } from "../LoadingScreen";

export interface ExportFormatOption {
  value: string;
  labelKey: string;
  icon: React.ReactNode;
  disabled?: boolean;
  disabledHintKey?: string;
  isLoading?: boolean;
  loadingLabelKey?: string;
}

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  formats: ExportFormatOption[];
  onExport: (format: string) => void;
  t: (key: string) => string;
}

/**
 * Modal d'export réutilisable pour scan simple et multi-scan.
 * Délègue la logique d'export et les états disabled/loading au parent.
 */
export default function ExportModal({
  isOpen,
  onClose,
  formats,
  onExport,
  t,
}: ExportModalProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t("scanner.export")}
      maxWidth="420px"
    >
      <p className="text-sm text-muted-theme mb-4">{t("scanner.exportDesc")}</p>
      <div className="flex flex-col gap-2">
        {formats.map(
          ({
            value,
            labelKey,
            icon,
            disabled,
            disabledHintKey,
            isLoading,
            loadingLabelKey,
          }) => (
            <button
              key={value}
              type="button"
              onClick={() => !disabled && !isLoading && onExport(value)}
              disabled={disabled || isLoading}
              title={
                disabled && disabledHintKey ? t(disabledHintKey) : undefined
              }
              className="flex items-center gap-3 w-full p-3 rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)] hover:bg-[var(--color-surface-hover)] transition-colors text-left disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-[var(--color-surface-input)]"
            >
              {isLoading ? <LoadingSpinner size="sm" /> : icon}
              <span className="font-medium">
                {isLoading && loadingLabelKey
                  ? t(loadingLabelKey)
                  : t(labelKey)}
              </span>
              {disabled && !isLoading && disabledHintKey && (
                <span className="text-xs text-muted-theme ml-auto">
                  {t(disabledHintKey)}
                </span>
              )}
            </button>
          ),
        )}
      </div>
    </Modal>
  );
}
