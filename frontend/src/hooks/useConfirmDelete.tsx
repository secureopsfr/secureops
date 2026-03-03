"use client";

import React, { useCallback, useState } from "react";
import { Trash2 } from "lucide-react";
import ConfirmModal from "../components/ConfirmModal";

export interface UseConfirmDeleteOptions {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
}

export interface UseConfirmDeleteReturn {
  deleteTargetId: string | null;
  openDeleteModal: (id: string) => void;
  closeDeleteModal: () => void;
  handleDeleteConfirm: () => Promise<void>;
  ConfirmDeleteModal: React.ReactNode;
}

/**
 * Hook pour gérer la logique de suppression avec modal de confirmation.
 *
 * @param onConfirm - Callback appelé avec l'id à supprimer (peut être async)
 * @param options - Titre, message et textes des boutons du modal
 * @returns État et handlers pour le modal de suppression
 */
export function useConfirmDelete(
  onConfirm: (id: string) => void | Promise<void>,
  options: UseConfirmDeleteOptions,
): UseConfirmDeleteReturn {
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  const openDeleteModal = useCallback((id: string) => {
    setDeleteTargetId(id);
  }, []);

  const closeDeleteModal = useCallback(() => {
    setDeleteTargetId(null);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    const id = deleteTargetId;
    if (!id) return;
    setDeleteTargetId(null);
    await onConfirm(id);
  }, [deleteTargetId, onConfirm]);

  const ConfirmDeleteModal = (
    <ConfirmModal
      isOpen={deleteTargetId !== null}
      onClose={closeDeleteModal}
      onConfirm={handleDeleteConfirm}
      title={options.title}
      message={options.message}
      confirmText={options.confirmText}
      cancelText={options.cancelText}
      variant="danger"
      icon={Trash2}
    />
  );

  return {
    deleteTargetId,
    openDeleteModal,
    closeDeleteModal,
    handleDeleteConfirm,
    ConfirmDeleteModal,
  };
}
