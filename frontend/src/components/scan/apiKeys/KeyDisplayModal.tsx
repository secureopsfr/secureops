"use client";

import { AlertTriangle, Copy } from "lucide-react";
import Modal from "../../ui/Modal";
import { GenericButton } from "../../buttons";
import { useLanguage } from "../../LanguageProvider";
import { showSuccessToast } from "../../../utils/toastNotifications";
import type { ApiKeyCreateResult } from "../../../services/apiKeysService";

interface KeyDisplayModalProps {
  isOpen: boolean;
  onClose: () => void;
  createdKey: ApiKeyCreateResult | null;
}

export default function KeyDisplayModal({
  isOpen,
  onClose,
  createdKey,
}: KeyDisplayModalProps) {
  const { t } = useLanguage();

  const handleCopy = () => {
    if (!createdKey?.key) return;
    navigator.clipboard.writeText(createdKey.key);
    showSuccessToast(t("scanner.clesApi.copied"));
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t("scanner.clesApi.keyCreatedTitle")}
      maxWidth="640px"
    >
      <div className="space-y-4">
        <div className="flex items-start gap-3 text-sm text-[rgb(var(--warning))] bg-[rgba(var(--warning),0.1)] rounded-lg p-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p>{t("scanner.clesApi.keyWarning")}</p>
        </div>
        {createdKey && (
          <div>
            <label className="block text-sm font-medium text-[var(--text)] mb-2">
              {t("scanner.clesApi.yourKey")}
            </label>
            <div className="flex gap-2">
              <code
                className="flex-1 min-w-0 p-3 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] text-sm font-mono overflow-hidden text-ellipsis whitespace-nowrap"
                title={createdKey.key}
              >
                {createdKey.key}
              </code>
              <GenericButton
                label={t("scanner.clesApi.copy")}
                onClick={handleCopy}
                variant="secondary"
                icon={<Copy className="w-4 h-4" />}
              />
            </div>
          </div>
        )}
        <div className="flex justify-end pt-2">
          <GenericButton
            label={t("common.confirm")}
            onClick={onClose}
            variant="primary"
          />
        </div>
      </div>
    </Modal>
  );
}
