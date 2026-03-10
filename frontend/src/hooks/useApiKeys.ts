"use client";

import { useState, useEffect, useCallback } from "react";
import {
  listApiKeys,
  type ApiKeyItem,
  type ApiKeyCreateResult,
} from "../services/apiKeysService";
import { showErrorToast } from "../utils/toastNotifications";
import { getApiKeyErrorMessage } from "../utils/apiKeyUtils";
import type { ApiKeyErrorContext } from "../utils/apiKeyUtils";

interface UseApiKeysOptions {
  t: (key: string) => string;
}

export function useApiKeys({ t }: UseApiKeysOptions) {
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadKeys = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listApiKeys();
      setKeys(res.items);
    } catch (e) {
      showErrorToast(
        e instanceof Error ? e.message : t("scanner.clesApi.loadError"),
      );
      setKeys([]);
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    loadKeys();
  }, [loadKeys]);

  const handleError = useCallback(
    (e: unknown, context: ApiKeyErrorContext) => {
      showErrorToast(getApiKeyErrorMessage(e, t, context));
    },
    [t],
  );

  return {
    keys,
    loading,
    loadKeys,
    handleError,
  };
}

export type { ApiKeyItem, ApiKeyCreateResult };
