"use client";

import useSWR from "swr";
import * as adminDocsService from "../../services/admin/adminDocsService";
import type {
  DocPagesResponse,
  DocPageContent,
} from "../../services/admin/adminDocsService";
import { ADMIN_DOCS_KEY, adminDocContentKey } from "./keys";

/**
 * Hook SWR pour la liste des pages de documentation admin.
 */
export function useAdminDocs() {
  const { data, isLoading, mutate } = useSWR(ADMIN_DOCS_KEY, () =>
    adminDocsService.getDocs(),
  );
  return {
    data: data as DocPagesResponse | undefined,
    docs: data?.docs ?? [],
    total: data?.total ?? 0,
    isLoading,
    mutate,
  };
}

/**
 * Hook SWR pour le contenu d'une page doc (clé par slug).
 * Passer null pour désactiver la requête.
 */
export function useAdminDocContent(slug: string | null) {
  const key = slug ? adminDocContentKey(slug) : null;
  const { data, isLoading, mutate } = useSWR(key, () =>
    slug ? adminDocsService.getDocContent(slug) : Promise.resolve(null),
  );
  return {
    data: data as DocPageContent | null | undefined,
    isLoading,
    mutate,
  };
}
