import { ChevronLeft, ChevronRight } from "lucide-react";
import { GenericButton } from "../buttons";

/* ─────────────────────── Types ─────────────────────── */

interface PaginationBaseProps {
  /** Désactiver les boutons (ex: pendant un chargement) */
  disabled?: boolean;
}

interface OffsetPaginationProps extends PaginationBaseProps {
  mode: "offset";
  offset: number;
  limit: number;
  total: number;
  onPrevious: () => void;
  onNext: () => void;
}

interface PagePaginationProps extends PaginationBaseProps {
  mode: "page";
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  /** Label pour le total (défaut : "entrées") */
  totalLabel?: string;
}

type PaginationProps = OffsetPaginationProps | PagePaginationProps;

/* ─────────────────────── Composant ─────────────────────── */

export default function Pagination(props: PaginationProps) {
  if (props.mode === "offset") {
    const { offset, limit, total, onPrevious, onNext, disabled } = props;
    if (total <= limit) return null;

    return (
      <div className="mt-6 pt-4 border-t border-[var(--border)] flex items-center justify-between">
        <div className="text-sm text-[var(--muted)]">
          Affichage de {offset + 1} à {Math.min(offset + limit, total)} sur{" "}
          {total}
        </div>
        <div className="flex items-center gap-2">
          <GenericButton
            label="Précédent"
            onClick={onPrevious}
            disabled={offset === 0 || disabled}
            variant="secondary"
          />
          <GenericButton
            label="Suivant"
            onClick={onNext}
            disabled={offset + limit >= total || disabled}
            variant="secondary"
          />
        </div>
      </div>
    );
  }

  // mode === "page"
  const {
    page,
    pageSize,
    total,
    onPageChange,
    disabled,
    totalLabel = "entrées",
  } = props;
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--border)]">
      <span className="text-xs text-[var(--muted)]">
        {total} {totalLabel} — Page {page + 1} / {totalPages}
      </span>
      <div className="flex gap-2">
        <button
          onClick={() => onPageChange(Math.max(0, page - 1))}
          disabled={page === 0 || disabled}
          className="p-2 rounded-lg border border-[var(--border)] hover:bg-[var(--color-surface-input)] disabled:opacity-30 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <button
          onClick={() => onPageChange(Math.min(totalPages - 1, page + 1))}
          disabled={page >= totalPages - 1 || disabled}
          className="p-2 rounded-lg border border-[var(--border)] hover:bg-[var(--color-surface-input)] disabled:opacity-30 transition-colors"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
