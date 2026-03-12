"use client";

/**
 * Composant de chargement unifié pour toutes les sections admin.
 * Assure une cohérence visuelle à travers tout le panneau d'administration.
 */

import React from "react";
import Card from "../ui/cards/Card";
import LoadingScreen from "../LoadingScreen";
import { useLanguage } from "../LanguageProvider";

interface AdminSectionLoadingProps {
  /**
   * Message de chargement personnalisé
   */
  message?: string;
  /**
   * Clé i18n pour le message (prioritaire si fournie)
   */
  messageKey?: string;
  /**
   * Si true, affiche un message d'erreur au lieu du loader
   */
  error?: string | null;
  /**
   * Callback pour réessayer en cas d'erreur
   */
  onRetry?: () => void;
}

/**
 * Composant de chargement standard pour les sections admin.
 * Affiche un spinner centré avec un message personnalisable.
 */
export default function AdminSectionLoading({
  message,
  messageKey,
  error = null,
  onRetry,
  retryLabel,
  errorTitle,
}: AdminSectionLoadingProps & { retryLabel?: string; errorTitle?: string }) {
  const { t } = useLanguage();
  const displayMessage = messageKey
    ? t(messageKey)
    : (message ?? t("common.loading"));
  const displayErrorTitle = errorTitle ?? t("admin.common.loadingError");
  const displayRetryLabel = retryLabel ?? t("admin.common.retry");

  if (error) {
    return (
      <Card disableHover>
        <div className="py-12 text-center">
          <div className="flex justify-center mb-4">
            <svg
              className="w-16 h-16 text-[rgba(var(--danger),0.5)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <p className="text-[var(--text)] font-medium mb-2">
            {displayErrorTitle}
          </p>
          <p className="text-[var(--muted)] text-sm mb-4">{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 bg-[rgb(var(--primary))] text-white rounded-lg hover:bg-[rgba(var(--primary),0.8)] transition-colors text-sm"
            >
              {displayRetryLabel}
            </button>
          )}
        </div>
      </Card>
    );
  }

  return (
    <Card disableHover>
      <LoadingScreen variant="section" message={displayMessage} />
    </Card>
  );
}

/**
 * Variante inline pour les chargements dans des sections déjà chargées.
 * Accepte message (texte) ou messageKey (clé i18n).
 */
export function AdminInlineLoading({
  message,
  messageKey,
}: {
  message?: string;
  messageKey?: string;
}) {
  const { t } = useLanguage();
  const displayMessage = messageKey
    ? t(messageKey)
    : (message ?? t("common.loading"));
  return (
    <div className="flex items-center justify-center py-8">
      <div className="flex items-center gap-3">
        <div className="animate-spin rounded-full h-5 w-5 border-2 border-[rgb(var(--primary))] border-t-transparent"></div>
        <span className="text-sm text-[var(--muted)]">{displayMessage}</span>
      </div>
    </div>
  );
}

/**
 * Message vide state pour les listes sans données
 */
export function AdminEmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="py-12 text-center">
      <div className="flex justify-center mb-4 text-[var(--muted)] opacity-50">
        {icon}
      </div>
      <p className="text-[var(--text)] font-medium mb-2">{title}</p>
      {description && (
        <p className="text-[var(--muted)] text-sm mb-4">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
