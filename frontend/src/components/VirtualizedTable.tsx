"use client";

import React, { ReactElement } from "react";
import { List } from "react-window";
import { useLanguage } from "./LanguageProvider";

interface Column<T = Record<string, unknown>> {
  key: string;
  header: string;
  render: (item: T) => React.ReactNode;
  align?: "left" | "center" | "right";
  width?: string | number;
  sticky?: boolean;
}

interface VirtualizedTableProps<T = Record<string, unknown>> {
  data: T[];
  columns: Column<T>[];
  rowHeight?: number;
  height?: number;
  emptyMessage?: string;
  cellClassName?: string;
}

// Props custom passées à chaque ligne via rowProps
interface RowExtraProps<T> {
  data: T[];
  columns: Column<T>[];
  cellClassName: string;
}

// Composant de ligne compatible avec react-window v2
// List injecte automatiquement ariaAttributes, index et style
function TableRow<T>({
  index,
  style,
  data,
  columns,
  cellClassName,
}: {
  ariaAttributes: {
    "aria-posinset": number;
    "aria-setsize": number;
    role: "listitem";
  };
  index: number;
  style: React.CSSProperties;
} & RowExtraProps<T>): ReactElement | null {
  const item = data[index];

  return (
    <div
      style={{
        ...style,
        display: "flex",
        alignItems: "center",
        borderBottom: "1px solid var(--border)",
        backgroundColor:
          index % 2 === 0 ? "transparent" : "var(--color-surface-subtle)",
      }}
      className="hover:bg-[var(--color-surface-hover)] transition-colors"
    >
      {columns.map((column, colIndex) => {
        const width =
          typeof column.width === "number"
            ? column.width
            : typeof column.width === "string"
              ? parseInt(column.width)
              : 150;

        return (
          <div
            key={`${index}-${colIndex}`}
            style={{
              width: `${width}px`,
              minWidth: `${width}px`,
              maxWidth: `${width}px`,
              padding: "0.75rem",
              textAlign: column.align || "left",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
            className={cellClassName}
          >
            {column.render(item)}
          </div>
        );
      })}
    </div>
  );
}

/**
 * Composant de tableau virtualisé pour afficher de grandes listes de données.
 * Utilise react-window pour n'afficher que les lignes visibles, améliorant les performances.
 *
 * @example
 * <VirtualizedTable
 *   data={users}
 *   columns={columns}
 *   rowHeight={50}
 *   height={600}
 * />
 */
export default function VirtualizedTable<T = Record<string, unknown>>({
  data,
  columns,
  rowHeight = 50,
  height = 600,
  emptyMessage,
  cellClassName = "",
}: VirtualizedTableProps<T>) {
  const { t } = useLanguage();
  const displayEmptyMessage = emptyMessage ?? t("common.noData");
  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--color-surface)] overflow-hidden">
        <div className="py-12 text-center">
          <p className="text-[var(--muted)]">{displayEmptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--color-surface)] overflow-hidden">
      {/* En-tête du tableau */}
      <div
        style={{
          display: "flex",
          borderBottom: "2px solid var(--border)",
          backgroundColor: "var(--color-surface-subtle)",
          fontWeight: "600",
        }}
      >
        {columns.map((column, index) => {
          const width =
            typeof column.width === "number"
              ? column.width
              : typeof column.width === "string"
                ? parseInt(column.width)
                : 150;

          return (
            <div
              key={index}
              style={{
                width: `${width}px`,
                minWidth: `${width}px`,
                maxWidth: `${width}px`,
                padding: "0.75rem",
                textAlign: column.align || "left",
                position: column.sticky ? "sticky" : "static",
                left: column.sticky ? 0 : "auto",
                backgroundColor: column.sticky
                  ? "var(--color-surface-subtle)"
                  : "transparent",
                zIndex: column.sticky ? 10 : 1,
              }}
              className="text-sm text-[var(--text)]"
            >
              {column.header}
            </div>
          );
        })}
      </div>

      {/* Corps du tableau virtualisé */}
      <List
        style={{ height }}
        rowComponent={TableRow as typeof TableRow<T>}
        rowCount={data.length}
        rowHeight={rowHeight}
        rowProps={{ data, columns, cellClassName } as RowExtraProps<T>}
        overscanCount={5}
      />
    </div>
  );
}

/**
 * Hook pour calculer automatiquement la hauteur optimale du tableau.
 * Basé sur la hauteur de la fenêtre et l'espace disponible.
 */
export function useTableHeight(
  defaultHeight: number = 600,
  offsetPx: number = 300,
): number {
  const [height, setHeight] = React.useState(defaultHeight);

  React.useEffect(() => {
    const calculateHeight = () => {
      const windowHeight = window.innerHeight;
      const calculatedHeight = Math.max(400, windowHeight - offsetPx);
      setHeight(calculatedHeight);
    };

    calculateHeight();
    window.addEventListener("resize", calculateHeight);

    return () => window.removeEventListener("resize", calculateHeight);
  }, [offsetPx]);

  return height;
}
