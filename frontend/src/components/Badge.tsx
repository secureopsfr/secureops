"use client";

import React from "react";

export type BadgeVariant =
  | "default"
  | "success"
  | "warning"
  | "error"
  | "info"
  | "pending"
  | "in_progress"
  | "processed"
  | "verified"
  | "unverified";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
  style?: React.CSSProperties;
}

const variantStyles: Record<BadgeVariant, { bg: string; text: string }> = {
  default: { bg: "var(--color-surface-hover)", text: "var(--muted)" },
  success: { bg: "rgba(var(--success),0.2)", text: "rgb(var(--success))" },
  warning: { bg: "rgba(var(--warning),0.2)", text: "rgb(var(--warning))" },
  error: { bg: "rgba(var(--danger),0.2)", text: "rgb(var(--danger))" },
  info: { bg: "rgba(var(--info),0.2)", text: "rgb(var(--info))" },
  pending: { bg: "rgba(var(--warning),0.2)", text: "rgb(var(--warning))" },
  in_progress: { bg: "rgba(var(--info),0.2)", text: "rgb(var(--info))" },
  processed: { bg: "rgba(var(--success),0.2)", text: "rgb(var(--success))" },
  verified: { bg: "rgba(var(--success),0.2)", text: "rgb(var(--success))" },
  unverified: { bg: "rgba(var(--warning),0.2)", text: "rgb(var(--warning))" },
};

export default function Badge({
  children,
  variant = "default",
  className = "",
  style,
}: BadgeProps) {
  const variantStyle = variantStyles[variant];

  return (
    <span
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "0.4rem 1rem",
        borderRadius: "9999px",
        fontSize: "0.75rem",
        fontWeight: 500,
        backgroundColor: variantStyle.bg,
        color: variantStyle.text,
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {children}
    </span>
  );
}
