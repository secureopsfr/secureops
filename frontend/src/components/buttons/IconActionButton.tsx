"use client";

import React from "react";
import type { LucideIcon } from "lucide-react";

type IconActionButtonVariant = "default" | "primary" | "danger";

interface IconActionButtonProps {
  icon: LucideIcon;
  ariaLabel: string;
  onClick: (e: React.MouseEvent) => void;
  variant?: IconActionButtonVariant;
  disabled?: boolean;
  title?: string;
  className?: string;
}

const VARIANT_CLASSES: Record<IconActionButtonVariant, string> = {
  default: "text-[var(--muted)] hover:text-[rgb(var(--primary))]",
  primary: "text-[rgb(var(--primary))]",
  danger: "text-[var(--muted)] hover:text-[rgb(var(--danger))]",
};

/**
 * Bouton d'action avec icône (poubelle, PDF, etc.).
 */
export default function IconActionButton({
  icon: Icon,
  ariaLabel,
  onClick,
  variant = "default",
  disabled = false,
  title,
  className = "",
}: IconActionButtonProps) {
  const baseClasses =
    "p-2 shrink-0 cursor-pointer disabled:opacity-50 disabled:cursor-wait";
  const variantClasses = VARIANT_CLASSES[variant];

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses} ${className}`.trim()}
      aria-label={ariaLabel}
      title={title ?? ariaLabel}
    >
      <Icon className="w-4 h-4" />
    </button>
  );
}
