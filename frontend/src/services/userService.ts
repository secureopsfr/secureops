/**
 * Service pour la gestion du profil utilisateur.
 * Adapté pour Next.js TypeScript
 */

import { fetchAuthSession } from "aws-amplify/auth";
import { fetchWithAuth, getApiBaseUrl } from "../utils/apiClient";
import { showErrorToast } from "../utils/toastNotifications";
import { log, error } from "../utils/logger";

/* ─── Types ─────────────────────────────────────────────── */

interface SubscriptionData {
  plan?: string;
  status?: string;
  newsletter_enabled?: boolean;
  new_features_notifications_enabled?: boolean;
  [key: string]: unknown;
}

interface ApiResponse<T = unknown> {
  success: boolean;
  error?: string;
  message?: string;
  data?: T;
  subscription?: SubscriptionData | null;
  deletedCount?: number;
  is_new_user?: boolean;
  [key: string]: unknown;
}

/* ─── Service ───────────────────────────────────────────── */

class UserService {
  /* ── Generic API call helper ────────────────────────────
   * Handles the common pattern:
   *   fetchWithAuth → response.json → success / error mapping
   * Replaces ~30 lines of boilerplate per method.
   * ──────────────────────────────────────────────────────── */
  private async apiCall<T = unknown>(
    path: string,
    opts: {
      method: string;
      body?: unknown;
      fallbackError: string;
      showToast?: boolean;
      logLabel: string;
      /** Map successful response data to extra fields in the ApiResponse. */
      mapSuccess?: (data: Record<string, unknown>) => Partial<ApiResponse<T>>;
    },
  ): Promise<ApiResponse<T>> {
    try {
      const fetchOpts: RequestInit = { method: opts.method };
      if (opts.body !== undefined) {
        fetchOpts.body = JSON.stringify(opts.body);
      }

      const response = await fetchWithAuth(
        `${getApiBaseUrl()}${path}`,
        fetchOpts,
      );

      // 204 No Content — nothing to parse
      if (response.status === 204) return { success: true };

      const data = await response.json();

      // Success: response.ok AND data.success is not explicitly false
      if (response.ok && data.success !== false) {
        return { success: true, ...(opts.mapSuccess?.(data) ?? {}) };
      }

      // API-level error
      const errorMessage = data.detail || data.error || opts.fallbackError;
      if (opts.showToast) showErrorToast(errorMessage);
      return { success: false, error: errorMessage };
    } catch (err: unknown) {
      error(`[UserService] ${opts.logLabel}:`, err);
      const errorMessage =
        (err instanceof Error ? err.message : null) || opts.fallbackError;
      if (opts.showToast) showErrorToast(errorMessage);
      return { success: false, error: errorMessage };
    }
  }

  /* ── Profile ──────────────────────────────────────────── */

  async updateProfile(profileData: {
    given_name?: string;
    family_name?: string;
  }): Promise<ApiResponse> {
    return this.apiCall("/user/api/user/profile", {
      method: "PUT",
      body: profileData,
      fallbackError: "Erreur lors de la mise à jour du profil",
      showToast: true,
      logLabel: "Erreur lors de la mise à jour du profil",
      mapSuccess: (d) => ({ message: d.message as string }),
    });
  }

  /* ── Init user (lazy creation, with deduplication) ───── */

  private _initUserPromise: Promise<ApiResponse> | null = null;

  async initUser(): Promise<ApiResponse & { is_new_user?: boolean }> {
    if (this._initUserPromise) {
      log(
        "[UserService] initUser déjà en cours, réutilisation de la Promise existante",
      );
      return this._initUserPromise as Promise<
        ApiResponse & { is_new_user?: boolean }
      >;
    }

    this._initUserPromise = (async () => {
      try {
        // Extract email from the ID token (access token doesn't carry email)
        let email: string | undefined;
        try {
          const session = await fetchAuthSession();
          const payload = session.tokens?.idToken?.payload;
          email = (payload?.email as string) ?? undefined;
        } catch {
          // Non-blocking — user creation will fall back to Cognito AdminGetUser
        }

        const response = await fetchWithAuth(
          `${getApiBaseUrl()}/user/api/user/init`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(email ? { email } : {}),
          },
        );
        const data = await response.json();

        if (response.ok && data.success) {
          return {
            success: true,
            message: "Utilisateur initialisé avec succès",
            is_new_user: data.is_new_user || false,
            dark_mode: data.dark_mode !== undefined ? data.dark_mode : true,
            language: data.language || "fr",
          };
        }
        // User already exists — still considered success
        return {
          success: true,
          message: "Utilisateur déjà initialisé",
          is_new_user: false,
          dark_mode: true,
          language: "fr",
        };
      } catch (err: unknown) {
        log(
          "[UserService] Erreur lors de l'initialisation (non bloquant):",
          err,
        );
        return {
          success: false,
          error:
            (err instanceof Error ? err.message : null) ||
            "Erreur lors de l'initialisation",
          is_new_user: false,
        };
      } finally {
        this._initUserPromise = null;
      }
    })();

    return this._initUserPromise as Promise<
      ApiResponse & { is_new_user?: boolean }
    >;
  }

  /* ── Subscription ─────────────────────────────────────── */

  async getSubscription(): Promise<ApiResponse<SubscriptionData>> {
    return this.apiCall<SubscriptionData>("/user/api/user/subscription", {
      method: "GET",
      fallbackError: "Erreur lors de la récupération de l'abonnement",
      logLabel: "Erreur lors de la récupération de l'abonnement",
      mapSuccess: (data) => ({ subscription: data as SubscriptionData }),
    });
  }

  /* ── Password ─────────────────────────────────────────── */

  async changePassword(passwordData: {
    current_password: string;
    new_password: string;
  }): Promise<ApiResponse> {
    return this.apiCall("/user/api/user/change-password", {
      method: "POST",
      body: passwordData,
      fallbackError: "Erreur lors du changement de mot de passe",
      showToast: true,
      logLabel: "Erreur lors du changement de mot de passe",
      mapSuccess: (d) => ({ message: d.message as string }),
    });
  }

  /* ── Export data (text response — special case) ───────── */

  async exportUserData(): Promise<ApiResponse<string>> {
    try {
      const response = await fetchWithAuth(
        `${getApiBaseUrl()}/user/api/user/export`,
        { method: "GET" },
      );

      if (response.ok) {
        return { success: true, data: await response.text() };
      }

      const errorText = await response.text();
      let errorMessage = errorText;
      try {
        const parsed = JSON.parse(errorText);
        errorMessage = parsed.detail || parsed.error || errorText;
      } catch {
        /* not JSON */
      }
      return {
        success: false,
        error: errorMessage || "Erreur lors de l'export des données",
      };
    } catch (err: unknown) {
      error("[UserService] Erreur lors de l'export des données:", err);
      return {
        success: false,
        error:
          (err instanceof Error ? err.message : null) ||
          "Erreur lors de l'export des données",
      };
    }
  }

  /* ── Favorites ────────────────────────────────────────── */

  async deleteAllFavorites(): Promise<ApiResponse<{ deleted_count?: number }>> {
    return this.apiCall<{ deleted_count?: number }>(
      "/user/api/user/favorites",
      {
        method: "DELETE",
        fallbackError: "Erreur lors de la suppression des favoris",
        logLabel: "Erreur lors de la suppression des favoris",
        mapSuccess: (d) => ({ deletedCount: (d.deleted_count as number) || 0 }),
      },
    );
  }

  /* ── Account ──────────────────────────────────────────── */

  async deleteAccount(): Promise<ApiResponse> {
    return this.apiCall("/user/api/user/account", {
      method: "DELETE",
      fallbackError: "Erreur lors de la suppression du compte",
      logLabel: "Erreur lors de la suppression du compte",
    });
  }

  /* ── Subscription preferences ─────────────────────────── */

  async updateSubscriptionPreferences(preferences: {
    newsletter_enabled?: boolean;
    new_features_notifications_enabled?: boolean;
    history_retention?: string;
  }): Promise<ApiResponse> {
    return this.apiCall("/user/api/user/subscription/preferences", {
      method: "PATCH",
      body: preferences,
      fallbackError: "Erreur lors de la mise à jour des préférences",
      showToast: true,
      logLabel: "Erreur lors de la mise à jour des préférences",
      mapSuccess: (d) => ({ subscription: d as SubscriptionData }),
    });
  }

  /* ── Theme preference ─────────────────────────────────── */

  async updateThemePreference(darkMode: boolean): Promise<ApiResponse> {
    return this.apiCall("/user/api/user/preferences/theme", {
      method: "PATCH",
      body: { dark_mode: darkMode },
      fallbackError: "Erreur lors de la mise à jour du thème",
      logLabel: "Erreur lors de la mise à jour du thème",
      mapSuccess: (d) => ({ dark_mode: d.dark_mode }),
    });
  }

  /* ── Language preference ──────────────────────────────── */

  async updateLanguagePreference(language: "fr" | "en"): Promise<ApiResponse> {
    return this.apiCall("/user/api/user/preferences/language", {
      method: "PATCH",
      body: { language },
      fallbackError: "Erreur lors de la mise à jour de la langue",
      logLabel: "Erreur lors de la mise à jour de la langue",
      mapSuccess: (d) => ({ language: d.language }),
    });
  }

  /* ── Logout all devices ───────────────────────────────── */

  async logoutAllDevices(): Promise<ApiResponse> {
    return this.apiCall("/user/api/user/logout-all-devices", {
      method: "POST",
      fallbackError: "Erreur lors de la déconnexion de tous les appareils",
      logLabel: "Erreur lors de la déconnexion de tous les appareils",
      mapSuccess: () => ({
        message: "Déconnexion de tous les appareils réussie",
      }),
    });
  }
}

const userService = new UserService();
export default userService;
