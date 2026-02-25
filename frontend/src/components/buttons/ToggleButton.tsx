"use client";

import React from "react";

interface ToggleButtonProps {
  isSelected: boolean;
  onClick: () => void;
  icon?: React.ComponentType<{ className?: string }>;
  label: string;
}

/**
 * Button component styled for navigation buttons
 */
const ToggleButton = React.forwardRef<HTMLButtonElement, ToggleButtonProps>(
  ({ isSelected, onClick, icon: Icon, label }, ref) => (
    <button
      ref={ref}
      onClick={onClick}
      className={`relative flex items-center gap-3 px-4 py-2 text-sm font-medium transition-all duration-300 whitespace-nowrap group hover:bg-[var(--color-surface-input)] rounded-full ${
        isSelected
          ? "text-[rgb(var(--primary))]"
          : "text-[var(--muted)] hover:text-[var(--text)]"
      }`}
    >
      {Icon && (
        <Icon
          className={`w-5 h-5 transition-all duration-300 ${
            isSelected
              ? "text-[rgb(var(--primary))]"
              : "text-[var(--muted)] group-hover:text-[var(--text)]"
          }`}
        />
      )}
      <span className="font-semibold">{label}</span>
      <div
        className={`absolute bottom-0 left-1/2 transform -translate-x-1/2 w-12 h-0.5 rounded-full transition-all duration-300 ${
          isSelected
            ? "scale-x-100 bg-[rgb(var(--primary))] shadow-sm"
            : "scale-x-0 group-hover:scale-x-100 bg-[var(--muted)]"
        }`}
      />
    </button>
  ),
);

ToggleButton.displayName = "ToggleButton";

export default ToggleButton;
