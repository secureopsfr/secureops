"use client";

import React from "react";
import { GenericButton } from "./buttons";
import { useLanguage } from "./LanguageProvider";

interface PaginationBarProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  translationKey?: string;
}

/**
 * Barre de pagination réutilisable (Page X / Y, boutons ← →).
 */
export default function PaginationBar({
  page,
  totalPages,
  onPageChange,
  translationKey = "scanner.historyPageOf",
}: PaginationBarProps) {
  const { t } = useLanguage();

  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between pt-2">
      <span className="text-sm text-[var(--muted)]">
        {t(translationKey, { page, total: totalPages })}
      </span>
      <div className="flex gap-2">
        <GenericButton
          label="←"
          variant="outline"
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page <= 1}
        />
        <GenericButton
          label="→"
          variant="outline"
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={page >= totalPages}
        />
      </div>
    </div>
  );
}
