/**
 * Composant de chargement unifié pour toutes les sections admin.
 * Assure une cohérence visuelle à travers tout le panneau d'administration.
 */

import React from "react";
import Card from "../cards/Card";
import LoadingScreen from "../LoadingScreen";

interface AdminSectionLoadingProps {
  /**
   * Message de chargement personnalisé
   * Par défaut : "Chargement..."
   */
  message?: string;
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
  error = null,
  onRetry,
  retryLabel,
  errorTitle,
}: AdminSectionLoadingProps & { retryLabel?: string; errorTitle?: string }) {
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
            {errorTitle ?? "Erreur de chargement"}
          </p>
          <p className="text-[var(--muted)] text-sm mb-4">{error}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-4 py-2 bg-[rgb(var(--primary))] text-white rounded-lg hover:bg-[rgba(var(--primary),0.8)] transition-colors text-sm"
            >
              {retryLabel ?? "Réessayer"}
            </button>
          )}
        </div>
      </Card>
    );
  }

  return (
    <Card disableHover>
      <LoadingScreen variant="section" message={message} />
    </Card>
  );
}

/**
 * Variante inline pour les chargements dans des sections déjà chargées
 */
export function AdminInlineLoading({
  message = "Chargement...",
}: {
  message?: string;
}) {
  return (
    <div className="flex items-center justify-center py-8">
      <div className="flex items-center gap-3">
        <div className="animate-spin rounded-full h-5 w-5 border-2 border-[rgb(var(--primary))] border-t-transparent"></div>
        <span className="text-sm text-[var(--muted)]">{message}</span>
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
