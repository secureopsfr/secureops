"use client";

import React, { type ReactNode } from "react";
import { Search, X, SortAsc, SortDesc, Grid, List } from "lucide-react";
import Card from "../cards/Card";
import { useDebounce } from "../../hooks/useDebounce";

/* ─────────────────────── Types ─────────────────────── */

export interface SortOption {
  /** Valeur interne du champ de tri */
  value: string;
  /** Libellé affiché */
  label: string;
}

export interface SearchToolbarProps {
  /* ── recherche ── */
  /** Valeur actuelle de la recherche */
  searchValue?: string;
  /** Callback quand la valeur change (mode instant) */
  onSearchChange?: (value: string) => void;
  /** Callback quand l'utilisateur soumet la recherche (Entrée / bouton) */
  onSearchSubmit?: () => void;
  /** Placeholder du champ de recherche */
  searchPlaceholder?: string;
  /** Callback pour vider la recherche */
  onSearchClear?: () => void;
  /** Masquer complètement le champ de recherche (par défaut false) */
  hideSearch?: boolean;
  /** Activer le debouncing pour la recherche (par défaut false) */
  enableDebounce?: boolean;
  /** Délai du debounce en millisecondes (par défaut 500ms) */
  debounceDelay?: number;

  /* ── tri ── */
  /** Options de tri affichées comme des boutons segmentés */
  sortOptions?: SortOption[];
  /** Valeur du champ de tri actuellement sélectionné */
  sortValue?: string;
  /** Callback quand un bouton de tri est cliqué */
  onSortChange?: (value: string) => void;
  /** Ordre de tri actuel */
  sortOrder?: "asc" | "desc";
  /** Callback pour basculer l'ordre de tri */
  onSortOrderToggle?: () => void;

  /* ── vue (grille / liste) ── */
  /** Mode de vue actuel */
  viewMode?: "grid" | "list";
  /** Callback quand le mode de vue change */
  onViewModeChange?: (mode: "grid" | "list") => void;

  /* ── contenu additionnel ── */
  /** Éléments supplémentaires à afficher (filtres, boutons, etc.) */
  children?: ReactNode;
}

/* ─────────────────────── Composant ─────────────────────── */

export default function SearchToolbar({
  searchValue,
  onSearchChange,
  onSearchSubmit,
  searchPlaceholder = "Rechercher…",
  onSearchClear,
  hideSearch = false,
  enableDebounce = false,
  debounceDelay = 500,
  sortOptions,
  sortValue,
  onSortChange,
  sortOrder,
  onSortOrderToggle,
  viewMode,
  onViewModeChange,
  children,
}: SearchToolbarProps) {
  const hasSort = sortOptions && sortOptions.length > 0;
  const hasViewToggle =
    viewMode !== undefined && onViewModeChange !== undefined;
  const hasSearch =
    !hideSearch &&
    (onSearchChange !== undefined || onSearchSubmit !== undefined);

  // Appliquer le debounce si activé
  const debouncedSearchValue = useDebounce(
    enableDebounce ? (searchValue ?? "") : "",
    debounceDelay,
  );

  // Déclencher onSearchSubmit automatiquement quand la valeur débouncée change
  React.useEffect(() => {
    if (
      enableDebounce &&
      debouncedSearchValue !== undefined &&
      onSearchSubmit
    ) {
      onSearchSubmit();
    }
  }, [debouncedSearchValue, enableDebounce, onSearchSubmit]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && onSearchSubmit) {
      onSearchSubmit();
    }
  };

  const handleClear = () => {
    if (onSearchClear) {
      onSearchClear();
    } else if (onSearchChange) {
      onSearchChange("");
    }
  };

  return (
    <Card disableHover>
      <div className="flex flex-wrap items-center gap-3">
        {/* ── Recherche ── */}
        {hasSearch && (
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--muted)]" />
            <input
              type="text"
              value={searchValue ?? ""}
              onChange={(e) => onSearchChange?.(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={searchPlaceholder}
              className="w-full pl-9 pr-9 py-2 rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)] text-sm text-[var(--text)]"
            />
            {searchValue && (
              <button
                onClick={handleClear}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)] hover:text-[var(--text)] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        )}

        {/* ── Enfants (filtres personnalisés, boutons, etc.) ── */}
        {children}

        {/* ── Tri ── */}
        {hasSort && (
          <div className="flex items-center gap-1 border border-[var(--border)] rounded-lg p-1">
            {sortOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => onSortChange?.(opt.value)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
                  sortValue === opt.value
                    ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                    : "text-[var(--muted)] hover:text-[var(--text)]"
                }`}
              >
                {opt.label}
              </button>
            ))}
            {sortOrder !== undefined && onSortOrderToggle && (
              <button
                onClick={onSortOrderToggle}
                className="p-1.5 rounded text-[var(--muted)] hover:text-[var(--text)] transition-colors"
                title={sortOrder === "asc" ? "Ascendant" : "Descendant"}
              >
                {sortOrder === "asc" ? (
                  <SortAsc className="w-4 h-4" />
                ) : (
                  <SortDesc className="w-4 h-4" />
                )}
              </button>
            )}
          </div>
        )}

        {/* ── Bascule Vue ── */}
        {hasViewToggle && (
          <div className="flex items-center gap-1 border border-[var(--border)] rounded-lg p-1">
            <button
              onClick={() => onViewModeChange("grid")}
              className={`p-1.5 rounded transition-all ${
                viewMode === "grid"
                  ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                  : "text-[var(--muted)] hover:text-[var(--text)]"
              }`}
              title="Vue grille"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => onViewModeChange("list")}
              className={`p-1.5 rounded transition-all ${
                viewMode === "list"
                  ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                  : "text-[var(--muted)] hover:text-[var(--text)]"
              }`}
              title="Vue liste"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </Card>
  );
}
