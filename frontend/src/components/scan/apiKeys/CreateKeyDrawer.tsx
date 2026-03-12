"use client";

import { useLanguage } from "../../LanguageProvider";
import {
  createApiKey,
  type ApiKeyCreateResult,
} from "../../../services/apiKeysService";
import { getApiKeyErrorMessage } from "../../../utils/apiKeyUtils";
import { showErrorToast } from "../../../utils/toastNotifications";
import ApiKeyFormDrawer, {
  getEmptyFormValues,
  type ApiKeyFormSubmitData,
} from "./ApiKeyFormDrawer";

interface CreateKeyDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (result: ApiKeyCreateResult) => void;
  loadKeys: () => Promise<void>;
}

export default function CreateKeyDrawer({
  isOpen,
  onClose,
  onSuccess,
  loadKeys,
}: CreateKeyDrawerProps) {
  const { t } = useLanguage();

  const handleSubmit = async (data: ApiKeyFormSubmitData) => {
    const options: {
      tags?: string[];
      description?: string | null;
      expiresAt?: string;
      ttlDays?: number;
    } = {
      tags: data.tags.length ? data.tags : undefined,
      description: data.description || undefined,
    };
    if (data.expiryMode === "date" && data.expiryDate) {
      options.expiresAt = data.expiryDate;
    } else {
      options.ttlDays = data.ttlDays === "0" ? 0 : parseInt(data.ttlDays, 10);
    }
    const result = await createApiKey(data.name, options);
    onSuccess(result);
    await loadKeys();
  };

  return (
    <ApiKeyFormDrawer
      isOpen={isOpen}
      onClose={onClose}
      title={t("scanner.clesApi.createTitle")}
      submitLabel={t("scanner.clesApi.createBtn")}
      initialValues={getEmptyFormValues()}
      onSubmit={async (data) => {
        try {
          await handleSubmit(data);
        } catch (e) {
          showErrorToast(getApiKeyErrorMessage(e, t, "create"));
          throw e;
        }
      }}
    />
  );
}
