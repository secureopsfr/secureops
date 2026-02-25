"use client";

import React, { useState, useMemo, useCallback } from "react";
import { ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";

interface Column<T> {
  key: keyof T | string;
  header: string;
  render?: (item: T, index: number) => React.ReactNode;
  align?: "left" | "center" | "right";
  className?: string;
  sticky?: boolean; // Colonne fixe à gauche lors du scroll horizontal
  sortable?: boolean; // Activer le tri pour cette colonne (true par défaut)
  sortValue?: (item: T) => unknown; // Valeur explicite utilisée pour le tri (prioritaire sur key)
}

type SortDirection = "asc" | "desc" | null;

interface SortState {
  key: string;
  direction: SortDirection;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  emptyMessage?: string;
  className?: string;
  headerClassName?: string;
  rowClassName?: string;
  cellClassName?: string;
  defaultSort?: { key: string; direction: "asc" | "desc" };
}

/** Détecte un pattern de date ISO-like : YYYY-MM-DD... */
const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}/;

/**
 * Parse une chaîne date de manière fiable (gère le format PostgreSQL
 * avec espace au lieu de T, et les offsets +00, +00:00, etc.).
 */
function parseDate(str: string): number {
  // Normaliser : remplacer l'espace entre date et heure par un T
  const normalized = str.replace(/^(\d{4}-\d{2}-\d{2})\s+/, "$1T");
  return new Date(normalized).getTime();
}

/**
 * Compare deux valeurs de manière générique (string, number, boolean, Date, null/undefined).
 * Retourne -1, 0 ou 1.
 */
function compareValues(a: unknown, b: unknown): number {
  // Null/undefined toujours en dernier
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;

  // Booleans
  if (typeof a === "boolean" && typeof b === "boolean") {
    return a === b ? 0 : a ? -1 : 1;
  }

  // Numbers
  if (typeof a === "number" && typeof b === "number") {
    return a - b;
  }

  // Dates (objets Date natifs)
  if (a instanceof Date && b instanceof Date) {
    return a.getTime() - b.getTime();
  }

  // Strings
  const strA = String(a);
  const strB = String(b);

  // Dates ISO-like en priorité (YYYY-MM-DD…) — détection explicite par regex
  // pour éviter les faux positifs de Date.parse sur des chaînes arbitraires
  if (ISO_DATE_RE.test(strA) && ISO_DATE_RE.test(strB)) {
    const dateA = parseDate(strA);
    const dateB = parseDate(strB);
    if (!isNaN(dateA) && !isNaN(dateB)) {
      return dateA - dateB;
    }
  }

  // Tenter une comparaison numérique
  const numA = Number(strA);
  const numB = Number(strB);
  if (
    !isNaN(numA) &&
    !isNaN(numB) &&
    strA.trim() !== "" &&
    strB.trim() !== ""
  ) {
    return numA - numB;
  }

  // Comparaison texte insensible à la casse
  return strA.localeCompare(strB, undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

/**
 * Composant Table réutilisable avec grilles pour délimiter les valeurs.
 * Tri par clic sur les en-têtes de colonnes.
 */
export default function Table<T extends Record<string, unknown>>({
  data,
  columns,
  emptyMessage = "Aucune donnée disponible",
  className = "",
  headerClassName = "",
  rowClassName = "",
  cellClassName = "",
  defaultSort,
}: TableProps<T>) {
  const [sort, setSort] = useState<SortState>({
    key: defaultSort?.key ?? "",
    direction: defaultSort?.direction ?? null,
  });

  const getValue = useCallback((item: T, key: keyof T | string): unknown => {
    if (typeof key === "string" && key.includes(".")) {
      const keys = key.split(".");
      let value: unknown = item;
      for (const k of keys) {
        if (value == null || typeof value !== "object") break;
        value = (value as Record<string, unknown>)[k];
      }
      return value;
    }
    return item[key as keyof T];
  }, []);

  const handleSort = useCallback((columnKey: string) => {
    setSort((prev) => {
      if (prev.key !== columnKey) {
        return { key: columnKey, direction: "asc" };
      }
      // Cycle : asc → desc → null (pas de tri)
      if (prev.direction === "asc")
        return { key: columnKey, direction: "desc" };
      if (prev.direction === "desc") return { key: "", direction: null };
      return { key: columnKey, direction: "asc" };
    });
  }, []);

  const sortedData = useMemo(() => {
    if (!sort.key || !sort.direction) return data;

    // Trouver la colonne active pour vérifier si elle a un sortValue
    const activeColumn = columns.find((c) => String(c.key) === sort.key);
    const sortValueFn = activeColumn?.sortValue;

    return [...data].sort((a, b) => {
      const valA = sortValueFn ? sortValueFn(a) : getValue(a, sort.key);
      const valB = sortValueFn ? sortValueFn(b) : getValue(b, sort.key);
      const result = compareValues(valA, valB);
      return sort.direction === "desc" ? -result : result;
    });
  }, [data, columns, sort, getValue]);

  if (!data || data.length === 0) {
    return (
      <div className="py-12 text-center">
        <p className="text-[var(--muted)]">{emptyMessage}</p>
      </div>
    );
  }

  const stickyClasses =
    "sticky left-0 z-10 bg-[var(--color-overlay-panel-solid)] shadow-[2px_0_4px_var(--color-shadow-light)]";

  return (
    <div className={`overflow-x-auto overflow-y-visible w-full ${className}`}>
      <table className="border-separate border-spacing-0 w-full min-w-max">
        <thead>
          <tr>
            {columns.map((column, index) => {
              const isSortable = column.sortable !== false;
              const columnKey = String(column.key);
              const isActive =
                sort.key === columnKey && sort.direction !== null;
              const isLast = index === columns.length - 1;

              return (
                <th
                  key={index}
                  className={`
                    px-6 py-4
                    text-xs font-semibold text-[var(--muted)] uppercase tracking-wider
                    border-b-2 border-[var(--border)]
                    ${!isLast ? "border-r" : ""}
                    ${column.align === "right" ? "text-right" : "text-center"}
                    ${column.sticky ? stickyClasses : "relative z-[1] bg-[var(--color-surface-subtle)]"}
                    ${isSortable ? "cursor-pointer select-none" : ""}
                    ${headerClassName}
                    ${column.className || ""}
                  `}
                  onClick={isSortable ? () => handleSort(columnKey) : undefined}
                >
                  <span className="inline-flex items-center gap-1.5">
                    {column.header}
                    {isSortable && (
                      <span
                        className={`inline-flex transition-colors ${isActive ? "text-[rgb(var(--primary))]" : "text-[var(--muted)] opacity-40"}`}
                      >
                        {isActive && sort.direction === "asc" ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : isActive && sort.direction === "desc" ? (
                          <ChevronDown className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronsUpDown className="w-3.5 h-3.5" />
                        )}
                      </span>
                    )}
                  </span>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((item, rowIndex) => (
            <tr
              key={rowIndex}
              className={`hover:bg-[var(--color-surface-subtle)] transition-colors ${rowClassName}`}
            >
              {columns.map((column, colIndex) => {
                const value = getValue(item, column.key);
                const content = column.render
                  ? column.render(item, rowIndex)
                  : value != null
                    ? String(value)
                    : "—";
                const isLast = colIndex === columns.length - 1;

                return (
                  <td
                    key={colIndex}
                    className={`
                      px-6 py-3.5
                      text-sm text-[var(--text)]
                      border-b border-[var(--border)]
                      ${!isLast ? "border-r" : ""}
                      ${column.align === "right" ? "text-right" : "text-center"}
                      ${column.sticky ? stickyClasses : "relative z-[1] bg-transparent"}
                      ${cellClassName}
                      ${column.className || ""}
                    `}
                  >
                    {content}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
