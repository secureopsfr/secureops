"use client";

import React, { Component, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { error as logError } from "../utils/logger";
import Card from "./cards/Card";
import { GenericButton } from "./buttons";

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Message personnalisé à afficher */
  fallbackMessage?: string;
  /** Fonction callback appelée lors d'une erreur */
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  /** Afficher les détails de l'erreur (dev mode) */
  showDetails?: boolean;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

/**
 * Error Boundary pour capturer et gérer les erreurs React.
 * Empêche le crash complet de l'application et affiche une UI de secours.
 *
 * @example
 * <ErrorBoundary>
 *   <MyComponent />
 * </ErrorBoundary>
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Mettre à jour l'état pour afficher l'UI de secours
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Logger l'erreur
    logError("[ErrorBoundary] Uncaught error:", error, errorInfo);

    // Mettre à jour l'état avec les infos complètes
    this.setState({
      error,
      errorInfo,
    });

    // Callback personnalisé
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      const { fallbackMessage, showDetails } = this.props;
      const { error, errorInfo } = this.state;

      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-[var(--color-background)]">
          <Card disableHover>
            <div className="max-w-2xl mx-auto text-center space-y-6 p-6">
              {/* Icône d'erreur */}
              <div className="flex justify-center">
                <div
                  className="rounded-full p-4"
                  style={{ backgroundColor: "rgba(var(--danger),0.1)" }}
                >
                  <AlertTriangle className="w-12 h-12 text-[rgb(var(--danger))]" />
                </div>
              </div>

              {/* Titre */}
              <div>
                <h1 className="text-2xl font-bold text-[var(--text)] mb-2">
                  Une erreur est survenue
                </h1>
                <p className="text-[var(--muted)]">
                  {fallbackMessage ||
                    "Désolé, quelque chose s'est mal passé. Veuillez réessayer."}
                </p>
              </div>

              {/* Détails de l'erreur (mode dev) */}
              {showDetails && error && (
                <div className="text-left space-y-3">
                  <div
                    className="p-4 rounded-lg border"
                    style={{
                      backgroundColor: "rgba(var(--danger),0.05)",
                      borderColor: "rgba(var(--danger),0.2)",
                    }}
                  >
                    <p className="text-xs font-mono font-semibold mb-2 text-[rgb(var(--danger))]">
                      Error Message:
                    </p>
                    <p
                      className="text-xs font-mono"
                      style={{ color: "rgba(var(--danger),0.8)" }}
                    >
                      {error.toString()}
                    </p>
                  </div>

                  {errorInfo && (
                    <details className="p-4 rounded-lg bg-[var(--color-surface-input)] border border-[var(--border)]">
                      <summary className="cursor-pointer text-xs font-semibold text-[var(--muted)] mb-2">
                        Stack Trace (cliquer pour afficher)
                      </summary>
                      <pre className="text-xs text-[var(--muted)] overflow-auto max-h-48 mt-2">
                        {errorInfo.componentStack}
                      </pre>
                    </details>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center justify-center gap-3 pt-4">
                <GenericButton
                  label="Réessayer"
                  onClick={this.handleReset}
                  variant="secondary"
                  icon={<RefreshCw className="w-4 h-4" />}
                  iconPosition="left"
                />
                <GenericButton
                  label="Recharger la page"
                  onClick={this.handleReload}
                  variant="primary"
                />
              </div>

              {/* Info */}
              <p className="text-xs text-[var(--muted)] pt-4 border-t border-[var(--border)]">
                Si le problème persiste, veuillez contacter le support
                technique.
              </p>
            </div>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

/**
 * Hook pour utiliser l'Error Boundary de manière programmatique.
 * Permet de déclencher manuellement l'error boundary.
 */
export function useErrorHandler(): (error: Error) => never {
  return (error: Error) => {
    throw error;
  };
}
