"use client";

import React from "react";

interface LoadingScreenProps {
  /** Variant of the loading screen */
  variant?: "fullPage" | "section" | "inline";
  /** Optional message to display */
  message?: string;
  /** Optional className */
  className?: string;
}

/**
 * Spinner de chargement réutilisable avec animation
 * Utilise les variables CSS du thème pour s'adapter au mode clair/sombre
 */
const LoadingSpinner: React.FC<{ size?: "sm" | "md" | "lg" }> = ({
  size = "md",
}) => {
  const sizeClasses = {
    sm: "h-5 w-5 border-2",
    md: "h-8 w-8 border-[3px]",
    lg: "h-12 w-12 border-4",
  };

  return (
    <div
      className={`animate-spin rounded-full ${sizeClasses[size]} border-[rgba(var(--primary),0.2)] border-t-[rgb(var(--primary))]`}
    />
  );
};

/**
 * Composant de chargement réutilisable pour toute l'application
 *
 * Variantes :
 * - `fullPage` : Plein écran centré (pour les pages entières)
 * - `section` : Au sein d'une section/card (pour les composants admin, etc.)
 * - `inline` : Compact, en ligne (pour les petits éléments)
 */
const LoadingScreen: React.FC<LoadingScreenProps> = ({
  variant = "section",
  message,
  className = "",
}) => {
  if (variant === "fullPage") {
    return (
      <div
        className={`min-h-screen bg-[var(--bg)] flex items-center justify-center ${className}`}
      >
        <div className="flex flex-col items-center gap-4">
          <LoadingSpinner size="lg" />
          {message && (
            <p className="text-[var(--muted)] text-sm animate-pulse">
              {message}
            </p>
          )}
        </div>
      </div>
    );
  }

  if (variant === "inline") {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <LoadingSpinner size="sm" />
        {message && (
          <span className="text-[var(--muted)] text-sm">{message}</span>
        )}
      </div>
    );
  }

  // variant === "section"
  return (
    <div className={`flex items-center justify-center py-12 ${className}`}>
      <div className="flex flex-col items-center gap-3">
        <LoadingSpinner size="md" />
        {message && <p className="text-[var(--muted)] text-sm">{message}</p>}
      </div>
    </div>
  );
};

export { LoadingSpinner };
export default LoadingScreen;
