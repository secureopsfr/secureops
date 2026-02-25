"use client";

import React, { useState, useEffect } from "react";
import { AlertTriangle } from "lucide-react";
import Modal from "./Modal";
import { GenericButton } from "./buttons";

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "default" | "danger";
  confirmationText?: string;
  icon?: React.ComponentType<{ className?: string }>;
}

/**
 * Composant de modal de confirmation réutilisable basé sur Modal.
 * Supporte la confirmation par texte pour les actions dangereuses.
 */
export default function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = "Confirmer",
  cancelText = "Annuler",
  variant = "default",
  confirmationText,
  icon: Icon,
}: ConfirmModalProps) {
  const [confirmationInput, setConfirmationInput] = useState("");

  // Réinitialiser l'input quand le modal s'ouvre
  useEffect(() => {
    if (isOpen) {
      setConfirmationInput("");
    }
  }, [isOpen]);

  const handleConfirm = () => {
    if (
      confirmationText &&
      confirmationInput.toLowerCase().trim() !==
        confirmationText.toLowerCase().trim()
    ) {
      return;
    }
    onConfirm();
    onClose();
  };

  const isDanger = variant === "danger";
  const isConfirmDisabled =
    !!confirmationText &&
    confirmationInput.toLowerCase().trim() !==
      confirmationText.toLowerCase().trim();

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-3">
          {Icon && (
            <Icon
              className={`w-6 h-6 ${isDanger ? "text-[rgb(var(--danger))]" : "text-[rgb(var(--primary))]"}`}
            />
          )}
          {isDanger && !Icon && (
            <AlertTriangle className="w-6 h-6 text-[rgb(var(--danger))]" />
          )}
          <span>{title}</span>
        </div>
      }
      maxWidth="500px"
      closeOnBackdropClick={true}
    >
      <div className="space-y-6">
        {/* Message */}
        <div>
          <p className="text-[var(--text)] leading-relaxed whitespace-pre-line">
            {message}
          </p>
        </div>

        {/* Champ de confirmation si nécessaire */}
        {confirmationText && (
          <div>
            <label className="block text-sm font-medium text-[var(--text)] mb-2">
              Tapez{" "}
              <span className="font-semibold text-[rgb(var(--primary))]">
                &quot;{confirmationText}&quot;
              </span>{" "}
              pour confirmer
            </label>
            <input
              type="text"
              value={confirmationInput}
              onChange={(e) => setConfirmationInput(e.target.value)}
              className="auth-input w-full"
              placeholder={confirmationText}
              autoComplete="off"
            />
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--border)]">
          <GenericButton
            label={cancelText}
            onClick={onClose}
            variant="secondary"
          />
          <GenericButton
            label={confirmText}
            onClick={handleConfirm}
            disabled={isConfirmDisabled}
            variant={isDanger ? "danger" : "primary"}
          />
        </div>
      </div>
    </Modal>
  );
}
