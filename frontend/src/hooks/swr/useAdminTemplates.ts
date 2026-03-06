"use client";

import useSWR from "swr";
import * as adminMediaService from "../../services/admin/adminMediaService";
import type {
  TemplateListResponse,
  TemplateContent,
} from "../../services/admin/adminMediaService";
import { ADMIN_TEMPLATES_KEY, adminTemplateContentKey } from "./keys";

/**
 * Hook SWR pour la liste des templates email admin.
 */
export function useAdminTemplates() {
  const { data, isLoading, mutate } = useSWR(ADMIN_TEMPLATES_KEY, () =>
    adminMediaService.getTemplates(),
  );
  return {
    data: data as TemplateListResponse | undefined,
    templates: data?.templates ?? [],
    total: data?.total ?? 0,
    isLoading,
    mutate,
  };
}

/**
 * Hook SWR pour le contenu d'un template (clé par filename).
 * Passer null pour désactiver la requête.
 */
export function useAdminTemplateContent(filename: string | null) {
  const key = filename ? adminTemplateContentKey(filename) : null;
  const { data, isLoading, mutate } = useSWR(key, () =>
    filename
      ? adminMediaService.getTemplateContent(filename)
      : Promise.resolve(null),
  );
  return {
    data: data as TemplateContent | null | undefined,
    isLoading,
    mutate,
  };
}
