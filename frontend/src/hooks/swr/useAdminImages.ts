"use client";

import useSWR from "swr";
import * as adminMediaService from "../../services/admin/adminMediaService";
import type {
  ImageGalleryResponse,
  ImageGalleryStats,
} from "../../services/admin/adminMediaService";
import { adminImagesKey, ADMIN_IMAGE_STATS_KEY } from "./keys";

/**
 * Hook SWR pour la liste des images admin (galerie).
 */
export function useAdminImages(sortBy: string, sortOrder: string) {
  const key = adminImagesKey(sortBy, sortOrder);
  const { data, isLoading, mutate } = useSWR(key, () =>
    adminMediaService.getImages({ sortBy, sortOrder }),
  );
  return {
    data: data as ImageGalleryResponse | undefined,
    images: data?.images ?? [],
    total: data?.total ?? 0,
    isLoading,
    mutate,
  };
}

/**
 * Hook SWR pour les statistiques des images admin.
 */
export function useAdminImageStats() {
  const { data, isLoading, mutate } = useSWR(
    ADMIN_IMAGE_STATS_KEY,
    () => adminMediaService.getImageStats(),
    { dedupingInterval: 60_000 },
  );
  return {
    data: data as ImageGalleryStats | undefined,
    isLoading,
    mutate,
  };
}
