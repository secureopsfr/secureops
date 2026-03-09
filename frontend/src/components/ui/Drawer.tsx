"use client";

import { useState, useEffect, useCallback } from "react";
import { X } from "lucide-react";

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  /** Largeur du panneau (défaut: 320px) */
  width?: string;
}

const DRAWER_CLOSE_DURATION_MS = 250;

/**
 * Volet latéral coulissant (comme le menu mobile du Header).
 * Overlay + panneau à droite.
 */
export default function Drawer({
  isOpen,
  onClose,
  title,
  children,
  width = "min(320px,85vw)",
}: DrawerProps) {
  const [closing, setClosing] = useState(false);

  const handleClose = useCallback(() => {
    if (closing) return;
    setClosing(true);
    setTimeout(() => {
      onClose();
      setClosing(false);
    }, DRAWER_CLOSE_DURATION_MS);
  }, [closing, onClose]);

  useEffect(() => {
    if (!isOpen) return;
    const onEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleClose();
    };
    document.addEventListener("keydown", onEscape);
    return () => document.removeEventListener("keydown", onEscape);
  }, [isOpen, handleClose]);

  if (!isOpen && !closing) return null;

  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-black/50 backdrop-blur-sm transition-opacity duration-[250ms] ${
          closing ? "opacity-0" : "opacity-100"
        }`}
        aria-hidden
        onClick={handleClose}
      />
      <div
        className={`drawer-panel fixed top-0 right-0 bottom-0 z-40 flex flex-col bg-[var(--bg)] border-l border-[var(--color-border)] shadow-xl ${
          closing ? "drawer-panel--closing" : ""
        }`}
        style={{ width }}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)] shrink-0">
          <span className="font-semibold text-[var(--color-text)]">
            {title}
          </span>
          <button
            type="button"
            onClick={handleClose}
            className="p-2 rounded-full hover:bg-[var(--color-surface)] transition-colors"
            aria-label="Fermer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4">{children}</div>
      </div>
    </>
  );
}
