"use client";

import { useEffect, useState, useRef } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import Card from "./cards/Card";
import { useLanguage } from "../LanguageProvider";

const DURATION_MS = 250;

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Appelé après la fin de l'animation de fermeture. */
  onExited?: () => void;
  title?: string | React.ReactNode;
  children: React.ReactNode;
  maxWidth?: string;
  showCloseButton?: boolean;
  closeOnBackdropClick?: boolean;
}

/**
 * Composant Modal réutilisable pour afficher des popups centrées.
 * Animation d'apparition (scale + fade) et de disparition.
 *
 * @param isOpen - Contrôle l'affichage de la modal
 * @param onClose - Fonction appelée lors de la fermeture
 * @param title - Titre optionnel affiché en haut de la modal
 * @param children - Contenu de la modal
 * @param maxWidth - Largeur maximale (défaut: '500px')
 * @param showCloseButton - Afficher le bouton de fermeture (défaut: true)
 * @param closeOnBackdropClick - Fermer au clic sur le backdrop (défaut: true)
 */
export default function Modal({
  isOpen,
  onClose,
  onExited,
  title,
  children,
  maxWidth = "500px",
  showCloseButton = true,
  closeOnBackdropClick = true,
}: ModalProps) {
  const { t } = useLanguage();
  const [mounted, setMounted] = useState(false);
  const [visible, setVisible] = useState(false);
  const [phase, setPhase] = useState<"enter" | "entered" | "exit" | "exited">(
    "enter",
  );
  const exitTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Ouverture : afficher puis lancer l'animation d'entrée
  useEffect(() => {
    if (!mounted) return;
    if (isOpen) {
      setVisible(true);
      setPhase("enter");
      const raf = requestAnimationFrame(() => {
        requestAnimationFrame(() => setPhase("entered"));
      });
      return () => cancelAnimationFrame(raf);
    }
  }, [mounted, isOpen]);

  // Fermeture : lancer l'animation de sortie puis masquer
  useEffect(() => {
    if (!mounted || !visible) return;
    if (!isOpen) {
      setPhase("exit");
      exitTimeoutRef.current = setTimeout(() => {
        setPhase("exited");
        setVisible(false);
        exitTimeoutRef.current = null;
        onExited?.();
      }, DURATION_MS);
      return () => {
        if (exitTimeoutRef.current) {
          clearTimeout(exitTimeoutRef.current);
          exitTimeoutRef.current = null;
        }
      };
    }
  }, [mounted, isOpen, visible, onExited]);

  // Bloquer le scroll du body quand la modal est affichée
  useEffect(() => {
    if (visible) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [visible]);

  if (!mounted || !visible) {
    return null;
  }

  const backdropEnter = phase === "enter";
  const backdropExit = phase === "exit";
  const contentEnter = phase === "enter";
  const contentExit = phase === "exit";

  const backdropClasses = [
    "modal-backdrop",
    backdropEnter && "modal-backdrop-enter",
    phase === "entered" && "modal-backdrop-enter-active",
    backdropExit && "modal-backdrop-exit",
    backdropExit && "modal-backdrop-exit-active",
  ]
    .filter(Boolean)
    .join(" ");

  const contentClasses = [
    "modal-content",
    contentEnter && "modal-content-enter",
    phase === "entered" && "modal-content-enter-active",
    contentExit && "modal-content-exit",
    contentExit && "modal-content-exit-active",
  ]
    .filter(Boolean)
    .join(" ");

  return createPortal(
    <div
      className={backdropClasses}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "var(--color-overlay)",
        backdropFilter: "blur(4px)",
        WebkitBackdropFilter: "blur(4px)",
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
      }}
      onClick={(e) => {
        if (closeOnBackdropClick && e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        className={contentClasses}
        style={{
          padding: "2rem",
          maxWidth: maxWidth,
          width: "100%",
          maxHeight: "90vh",
          overflowY: "auto",
          position: "relative",
          margin: 0,
        }}
        onClick={(e) => {
          e.stopPropagation();
        }}
      >
        <Card disableHover>
          {(title || showCloseButton) && (
            <div className="flex justify-between items-center mb-6">
              {title && (
                <div className="flex-1">
                  {typeof title === "string" ? (
                    <h3 className="text-xl font-bold text-[var(--text)]">
                      {title}
                    </h3>
                  ) : (
                    title
                  )}
                </div>
              )}
              {showCloseButton && (
                <button
                  onClick={onClose}
                  className="p-1 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors text-[var(--muted)] hover:text-[var(--text)]"
                  aria-label={t("modal.ariaClose")}
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          )}
          <div>{children}</div>
        </Card>
      </div>
    </div>,
    document.body,
  );
}
