/**
 * Service d'administration pour la gestion des médias (images + templates).
 */

import { fetchAuthSession } from "aws-amplify/auth";
import { getApiBaseUrl } from "../../utils/apiClient";
import { error as logError } from "../../utils/logger";
import { showErrorToast, getToastT } from "../../utils/toastNotifications";
import { fetchWithAuth } from "../../utils/apiClient";

export interface ImageRecord {
  filename: string;
  url: string;
  thumbnail_url?: string;
  size: number;
  created_at: string;
}

export interface ImageGalleryResponse {
  images: ImageRecord[];
  total: number;
}

export interface ImageGalleryStats {
  total: number;
  total_size: number;
  by_extension: Record<string, number>;
}

export interface TemplateRecord {
  filename: string;
  size: number;
  updated_at: string;
}

export interface TemplateListResponse {
  templates: TemplateRecord[];
  total: number;
}

export interface TemplateContent {
  filename: string;
  content: string;
  size: number;
  updated_at: string;
}

export async function uploadImage(
  file: File,
): Promise<{ url: string; image_url?: string }> {
  try {
    let token: string | undefined;
    try {
      const session = await fetchAuthSession();
      token = session.tokens?.accessToken?.toString();
    } catch (err) {
      logError(
        "[AdminMediaService] Impossible de récupérer le token pour upload:",
        err,
      );
    }

    const formData = new FormData();
    formData.append("file", file);

    const headers: HeadersInit = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${getApiBaseUrl()}/admin/api/upload-image`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(errorData.detail || "Erreur lors de l'upload de l'image");
    }

    return await response.json();
  } catch (err: unknown) {
    logError("[AdminMediaService] Erreur upload image:", err);
    showErrorToast(getToastT()("admin.toast.uploadImage"));
    throw err;
  }
}

export async function getImages({
  sortBy = "date",
  sortOrder = "desc",
}: {
  sortBy?: string;
  sortOrder?: string;
} = {}): Promise<ImageGalleryResponse> {
  try {
    const url = new URL(`${getApiBaseUrl()}/admin/api/images`);
    url.searchParams.set("sort_by", sortBy);
    url.searchParams.set("sort_order", sortOrder);

    const response = await fetchWithAuth(url.toString(), { method: "GET" });
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail || "Erreur lors de la récupération des images",
      );
    }
    return await response.json();
  } catch (err: unknown) {
    logError("[AdminMediaService] Erreur récupération images:", err);
    showErrorToast(getToastT()("admin.toast.loadImages"));
    throw err;
  }
}

export async function getImageStats(): Promise<ImageGalleryStats> {
  try {
    const response = await fetchWithAuth(
      `${getApiBaseUrl()}/admin/api/images/stats`,
      { method: "GET" },
    );
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail || "Erreur récupération statistiques images",
      );
    }
    return await response.json();
  } catch (err: unknown) {
    logError("[AdminMediaService] Erreur stats images:", err);
    showErrorToast(getToastT()("admin.toast.loadImageStats"));
    throw err;
  }
}

export async function deleteImage(
  filename: string,
): Promise<Record<string, unknown>> {
  try {
    const response = await fetchWithAuth(
      `${getApiBaseUrl()}/admin/api/images/${encodeURIComponent(filename)}`,
      { method: "DELETE" },
    );
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail || "Erreur lors de la suppression de l'image",
      );
    }
    return await response.json();
  } catch (err: unknown) {
    logError("[AdminMediaService] Erreur suppression image:", err);
    showErrorToast(getToastT()("admin.toast.deleteImage"));
    throw err;
  }
}

/* ─────────────── Templates d'emails ─────────────── */

export async function getTemplates(): Promise<TemplateListResponse> {
  try {
    const response = await fetchWithAuth(
      `${getApiBaseUrl()}/admin/api/templates`,
      { method: "GET" },
    );
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail || "Erreur lors de la récupération des templates",
      );
    }
    return await response.json();
  } catch (err: unknown) {
    logError("[AdminMediaService] Erreur récupération templates:", err);
    showErrorToast(getToastT()("admin.toast.loadTemplates"));
    throw err;
  }
}

export async function getTemplateContent(
  filename: string,
): Promise<TemplateContent> {
  try {
    const response = await fetchWithAuth(
      `${getApiBaseUrl()}/admin/api/templates/${encodeURIComponent(filename)}`,
      { method: "GET" },
    );
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail || "Erreur lors de la récupération du template",
      );
    }
    return await response.json();
  } catch (err: unknown) {
    logError("[AdminMediaService] Erreur récupération template:", err);
    showErrorToast(getToastT()("admin.toast.loadTemplate"));
    throw err;
  }
}

export async function updateTemplate(
  filename: string,
  content: string,
): Promise<Record<string, unknown>> {
  try {
    const response = await fetchWithAuth(
      `${getApiBaseUrl()}/admin/api/templates/${encodeURIComponent(filename)}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      },
    );
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail || "Erreur lors de la mise à jour du template",
      );
    }
    return await response.json();
  } catch (err: unknown) {
    logError("[AdminMediaService] Erreur mise à jour template:", err);
    showErrorToast(getToastT()("admin.toast.updateTemplate"));
    throw err;
  }
}

export async function createTemplate(
  filename: string,
  content: string = "",
): Promise<Record<string, unknown>> {
  try {
    const response = await fetchWithAuth(
      `${getApiBaseUrl()}/admin/api/templates`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename, content }),
      },
    );
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail || "Erreur lors de la création du template",
      );
    }
    return await response.json();
  } catch (err: unknown) {
    logError("[AdminMediaService] Erreur création template:", err);
    showErrorToast(getToastT()("admin.toast.createTemplate"));
    throw err;
  }
}

export async function deleteTemplate(
  filename: string,
): Promise<Record<string, unknown>> {
  try {
    const response = await fetchWithAuth(
      `${getApiBaseUrl()}/admin/api/templates/${encodeURIComponent(filename)}`,
      { method: "DELETE" },
    );
    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Erreur inconnue" }));
      throw new Error(
        errorData.detail || "Erreur lors de la suppression du template",
      );
    }
    return await response.json();
  } catch (err: unknown) {
    logError("[AdminMediaService] Erreur suppression template:", err);
    showErrorToast(getToastT()("admin.toast.deleteTemplate"));
    throw err;
  }
}
