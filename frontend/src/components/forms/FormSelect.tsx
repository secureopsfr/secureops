"use client";

import React, { useEffect, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useDropdown } from "../../hooks/useDropdown";

interface Option {
  value: string;
  label: string;
}

interface FormSelectProps {
  value: string;
  onChange: (value: string) => void;
  options: Option[];
  /** Si true, le volet s'ouvre uniquement au clic (pas au survol). */
  clickOnly?: boolean;
}

/**
 * Composant de sélection pour les formulaires (sans shadow).
 * Basé sur SortSelect mais adapté pour les formulaires.
 */
export default function FormSelect({
  value,
  onChange,
  options,
  clickOnly = false,
}: FormSelectProps) {
  const {
    isOpen,
    isClosing,
    dropdownRef,
    mouseHandlers,
    buttonHandlers,
    close,
  } = useDropdown({
    closeDelay: 250,
    clickOnly,
  });

  const selectedOption =
    options.find((opt) => opt.value === value) ?? options[0];

  // Animation : montage avec style fermé, puis transition vers ouvert
  const [isAnimatedIn, setIsAnimatedIn] = useState(false);
  useEffect(() => {
    if (isOpen && !isClosing) {
      const raf = requestAnimationFrame(() => setIsAnimatedIn(true));
      return () => cancelAnimationFrame(raf);
    }
    setIsAnimatedIn(false);
  }, [isOpen, isClosing]);

  const showPanel = isOpen || isClosing;
  const panelVisible = !isClosing && isAnimatedIn;

  return (
    <div
      ref={dropdownRef}
      className="flex items-center gap-2 relative z-[60] w-full"
      {...mouseHandlers}
    >
      <div className="relative inline-block text-left w-full">
        <button
          type="button"
          className="w-full flex items-center justify-between bg-[var(--color-surface-input)] border border-[var(--border)] text-[var(--text)] rounded-lg px-4 py-2.5 text-base hover:bg-[var(--color-surface-input-hover)] focus:outline-none transition-colors focus:border-[rgba(var(--primary),0.5)]"
          {...buttonHandlers}
        >
          <span className="truncate text-[var(--text)]">
            {selectedOption.label}
          </span>
          {isOpen ? (
            <ChevronUp className="w-4 h-4 text-[var(--muted)] flex-shrink-0" />
          ) : (
            <ChevronDown className="w-4 h-4 text-[var(--muted)] flex-shrink-0" />
          )}
        </button>

        {/* Zone invisible pour éviter la fermeture du menu */}
        {showPanel && <div className="absolute top-full left-0 h-2 w-full" />}

        {/* Menu déroulant : animation apparition / disparition */}
        {showPanel && (
          <ul
            className="absolute left-0 mt-1 w-full max-h-60 overflow-auto bg-[var(--color-overlay-panel)] backdrop-blur-sm border border-[var(--border)] rounded-lg z-[70] text-base origin-top transition-all duration-200 ease-out"
            style={{
              opacity: panelVisible ? 1 : 0,
              transform: panelVisible
                ? "translateY(0) scale(1)"
                : "translateY(-6px) scale(0.97)",
            }}
          >
            {options.map((opt) => (
              <li key={opt.value}>
                <button
                  className={`block w-full text-left px-6 py-2 transition-colors ${
                    opt.value === value
                      ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))] font-medium"
                      : "text-[var(--text)] hover:bg-[var(--color-surface-input)]"
                  }`}
                  onClick={() => {
                    onChange(opt.value);
                    close();
                  }}
                >
                  {opt.label}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
