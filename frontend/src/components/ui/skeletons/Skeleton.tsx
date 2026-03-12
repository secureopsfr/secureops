"use client";

import React from "react";

interface SkeletonProps {
  /** Width class or inline style */
  width?: string;
  /** Height class or inline style */
  height?: string;
  /** Border radius */
  rounded?: "none" | "sm" | "md" | "lg" | "full";
  /** Additional className */
  className?: string;
}

const roundedClasses = {
  none: "",
  sm: "rounded-sm",
  md: "rounded-md",
  lg: "rounded-lg",
  full: "rounded-full",
};

/**
 * Primitive skeleton block with pulse animation.
 * Building block for more complex skeleton layouts.
 */
const Skeleton: React.FC<SkeletonProps> = ({
  width = "w-full",
  height = "h-4",
  rounded = "md",
  className = "",
}) => {
  return (
    <div
      className={`animate-pulse bg-[var(--color-surface-hover)] ${roundedClasses[rounded]} ${width} ${height} ${className}`}
    />
  );
};

/**
 * Skeleton for a text line
 */
export const SkeletonText: React.FC<{
  lines?: number;
  className?: string;
}> = ({ lines = 1, className = "" }) => (
  <div className={`space-y-2 ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        width={i === lines - 1 && lines > 1 ? "w-3/4" : "w-full"}
        height="h-3"
      />
    ))}
  </div>
);

/**
 * Skeleton for an input field
 */
export const SkeletonInput: React.FC<{ className?: string }> = ({
  className = "",
}) => (
  <div className={`space-y-1.5 ${className}`}>
    <Skeleton width="w-24" height="h-3" />
    <Skeleton width="w-full" height="h-10" rounded="lg" />
  </div>
);

/**
 * Skeleton for a button
 */
export const SkeletonButton: React.FC<{
  width?: string;
  className?: string;
}> = ({ width = "w-32", className = "" }) => (
  <Skeleton width={width} height="h-10" rounded="full" className={className} />
);

/**
 * Skeleton for a toggle switch row (icon + text + toggle)
 */
export const SkeletonToggleRow: React.FC<{ className?: string }> = ({
  className = "",
}) => (
  <div
    className={`flex items-center justify-between p-4 bg-[var(--color-surface-input)] border border-[var(--border)] rounded-lg ${className}`}
  >
    <div className="flex items-center gap-3">
      <Skeleton width="w-5" height="h-5" rounded="md" />
      <div className="space-y-1.5">
        <Skeleton width="w-28" height="h-3.5" />
        <Skeleton width="w-48" height="h-3" />
      </div>
    </div>
    <Skeleton width="w-11" height="h-6" rounded="full" />
  </div>
);

/**
 * Skeleton for a table row
 */
export const SkeletonTableRow: React.FC<{
  columns?: number;
  className?: string;
}> = ({ columns = 5, className = "" }) => (
  <div
    className={`flex items-center gap-4 p-4 border-b border-[var(--border)] ${className}`}
  >
    {Array.from({ length: columns }).map((_, i) => (
      <Skeleton
        key={i}
        width={i === 0 ? "w-32" : "w-24"}
        height="h-4"
        className="flex-shrink-0"
      />
    ))}
  </div>
);

export default Skeleton;
