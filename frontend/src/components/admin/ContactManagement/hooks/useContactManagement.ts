"use client";

import { useState, useCallback } from "react";
import useSWR from "swr";
import adminService from "../../../../services/admin";
import { error as logError } from "../../../../utils/logger";
import {
  showSuccessToast,
  showErrorToast,
} from "../../../../utils/toastNotifications";
import { useLanguage } from "../../../LanguageProvider";
import { adminContactsKey } from "../../../../hooks/swr/keys";

export interface ContactMessage {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  subject: string;
  message: string;
  status: string;
  created_at: string;
  updated_at: string;
  [key: string]: unknown;
}

export function useContactManagement() {
  const { t } = useLanguage();
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [updatingStatusId, setUpdatingStatusId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<"kanban" | "list">("kanban");

  /* ── état modale réponse ── */
  const [replyModalOpen, setReplyModalOpen] = useState(false);
  const [replyTarget, setReplyTarget] = useState<ContactMessage | null>(null);
  const [replyBody, setReplyBody] = useState("");
  const [replySending, setReplySending] = useState(false);

  /* ── état modale suppression ── */
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<ContactMessage | null>(null);

  /* ── SWR : messages de contact ── */
  const swrKey = adminContactsKey({
    status: viewMode === "kanban" ? null : statusFilter,
    limit: viewMode === "kanban" ? 1000 : limit,
    offset: viewMode === "kanban" ? 0 : offset,
  });

  const {
    data: result,
    isLoading: loading,
    error: swrError,
    mutate,
  } = useSWR(swrKey, () =>
    adminService.getContactMessages(
      viewMode === "kanban" ? null : statusFilter,
      viewMode === "kanban" ? 1000 : limit,
      viewMode === "kanban" ? 0 : offset,
    ),
  );

  const contactMessages = (result?.data || []) as ContactMessage[];
  const total = result?.total || 0;
  const error = swrError ? t("admin.errorLoadingContacts") : null;

  /* ── pagination ── */
  const handlePrevious = () => setOffset(Math.max(0, offset - limit));
  const handleNext = () => setOffset(offset + limit);

  /* ── mise à jour statut ── */
  const handleUpdateStatus = useCallback(
    async (messageId: number, newStatus: string) => {
      setUpdatingStatusId(messageId);
      try {
        await adminService.updateContactMessageStatus(messageId, newStatus);
        showSuccessToast(t("admin.toast.contactStatusUpdated"));
        await mutate();
      } catch (err) {
        logError("Error updating contact message status:", err);
        showErrorToast(t("admin.toast.updateContactStatus"));
      } finally {
        setUpdatingStatusId(null);
      }
    },
    [mutate, t],
  );

  /* ── modale réponse ── */
  const openReplyModal = useCallback((message: ContactMessage) => {
    setReplyTarget(message);
    setReplyBody("");
    setReplyModalOpen(true);
  }, []);

  const closeReplyModal = useCallback(() => {
    setReplyModalOpen(false);
    setReplyTarget(null);
    setReplyBody("");
  }, []);

  const handleSendReply = useCallback(async () => {
    if (!replyTarget || !replyBody.trim()) return;
    setReplySending(true);
    try {
      await adminService.replyToContactMessage(replyTarget.id, replyBody);
      showSuccessToast(
        t("admin.toast.replySent", { email: replyTarget.email }),
      );
      closeReplyModal();
      await mutate();
    } catch (err) {
      logError("Error sending reply:", err);
      showErrorToast(t("admin.toast.replyError"));
    } finally {
      setReplySending(false);
    }
  }, [replyTarget, replyBody, closeReplyModal, mutate, t]);

  /* ── modale suppression ── */
  const openDeleteModal = useCallback((message: ContactMessage) => {
    setDeleteTarget(message);
    setDeleteModalOpen(true);
  }, []);

  const closeDeleteModal = useCallback(() => {
    setDeleteModalOpen(false);
    setDeleteTarget(null);
  }, []);

  const handleConfirmDelete = useCallback(async () => {
    if (!deleteTarget) return;
    try {
      await adminService.deleteContactMessage(deleteTarget.id);
      showSuccessToast(t("admin.toast.contactDeleted"));
      closeDeleteModal();
      await mutate();
    } catch (err) {
      logError("Error deleting contact message:", err);
      showErrorToast(t("admin.toast.deleteContactError"));
    }
  }, [deleteTarget, closeDeleteModal, mutate, t]);

  // Backward compat
  const loadContactMessages = () => mutate();

  return {
    // Data
    contactMessages,
    total,
    // UI state
    loading,
    error,
    limit,
    offset,
    statusFilter,
    setStatusFilter,
    setOffset,
    updatingStatusId,
    viewMode,
    setViewMode,
    // Reply modal
    replyModalOpen,
    replyTarget,
    replyBody,
    setReplyBody,
    replySending,
    openReplyModal,
    closeReplyModal,
    handleSendReply,
    // Delete modal
    deleteModalOpen,
    deleteTarget,
    openDeleteModal,
    closeDeleteModal,
    handleConfirmDelete,
    // Actions
    loadContactMessages,
    handlePrevious,
    handleNext,
    handleUpdateStatus,
    // i18n
    t,
  };
}
