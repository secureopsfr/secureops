"use client";

import { useMemo } from "react";
import { useLanguage } from "../../LanguageProvider";
import { updateApiKey } from "../../../services/apiKeysService";
import { getApiKeyErrorMessage } from "../../../utils/apiKeyUtils";
import {
  showSuccessToast,
  showErrorToast,
} from "../../../utils/toastNotifications";
import ApiKeyFormDrawer, {
  getEmptyFormValues,
  keyItemToFormValues,
  type ApiKeyFormSubmitData,
} from "./ApiKeyFormDrawer";
import type { ApiKeyItem } from "../../../services/apiKeysService";

interface EditKeyDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  keyItem: ApiKeyItem | null;
  loadKeys: () => Promise<void>;
}

export default function EditKeyDrawer({
  isOpen,
  onClose,
  keyItem,
  loadKeys,
}: EditKeyDrawerProps) {
  const { t } = useLanguage();

  const initialValues = useMemo(
    () => (keyItem ? keyItemToFormValues(keyItem) : getEmptyFormValues()),
    [keyItem],
  );

  const handleSubmit = async (data: ApiKeyFormSubmitData) => {
    if (!keyItem) return;
    const options: {
      name: string;
      tags: string[];
      description: string | null;
      expiresAt?: string;
      ttlDays?: number;
    } = {
      name: data.name,
      tags: data.tags,
      description: data.description || null,
    };
    if (data.expiryMode === "date" && data.expiryDate) {
      options.expiresAt = data.expiryDate;
    } else {
      options.ttlDays = data.ttlDays === "0" ? 0 : parseInt(data.ttlDays, 10);
    }
    await updateApiKey(keyItem.id, options);
    showSuccessToast(t("scanner.clesApi.editKeySuccess"));
    await loadKeys();
  };

  return (
    <ApiKeyFormDrawer
      isOpen={isOpen && !!keyItem}
      onClose={onClose}
      title={t("scanner.clesApi.editKeyTitle")}
      submitLabel={t("common.save")}
      initialValues={initialValues}
      onSubmit={async (data) => {
        try {
          await handleSubmit(data);
        } catch (e) {
          showErrorToast(getApiKeyErrorMessage(e, t, "update"));
          throw e;
        }
      }}
    />
  );
}
