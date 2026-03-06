"use client";

import { Mail, RefreshCw, LayoutGrid, List, Trash2 } from "lucide-react";
import { useContactManagement } from "./hooks/useContactManagement";
import { useContactColumns } from "./ContactColumns";
import ContactReplyModal from "./ContactReplyModal";
import Card from "../../ui/cards/Card";
import { DropdownSelector } from "../../buttons";
import Pagination from "../Pagination";
import ContactKanban from "../ContactKanban";
import Table from "../../Table";
import ConfirmModal from "../../ConfirmModal";
import { AdminInlineLoading } from "../AdminSectionLoading";

export default function ContactManagement() {
  const {
    contactMessages,
    total,
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
    // Reply
    replyModalOpen,
    replyTarget,
    replyBody,
    setReplyBody,
    replySending,
    openReplyModal,
    closeReplyModal,
    handleSendReply,
    // Delete
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
    t,
  } = useContactManagement();

  const listColumns = useContactColumns({
    updatingStatusId,
    handleUpdateStatus,
    openReplyModal,
    openDeleteModal,
  });

  return (
    <div className="space-y-6">
      {/* En-tête : titre, description, total, toggle, filtre statut, refresh (même bulle que les autres sections) */}
      <Card disableHover>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-[var(--text)]">
              {t("admin.contact.title")}
            </h2>
            <p className="text-[var(--muted)] mt-1">
              {t("admin.contact.description")} ({total}{" "}
              {t("admin.common.total")})
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            {viewMode === "list" && (
              <DropdownSelector
                selectedValue={statusFilter || ""}
                onChange={(value) => {
                  setStatusFilter(value || null);
                  setOffset(0);
                }}
                options={[
                  { value: "", label: t("admin.contact.allStatuses") },
                  { value: "pending", label: t("admin.contact.pending") },
                  {
                    value: "in_progress",
                    label: t("admin.contact.inProgress"),
                  },
                  { value: "processed", label: t("admin.contact.processed") },
                ]}
                width="13rem"
                triggerClassName="h-9"
              />
            )}
            <div className="flex h-9 items-stretch gap-0.5 rounded-lg border border-[var(--border)] p-0.5 bg-[var(--color-surface-subtle)]">
              <button
                onClick={() => {
                  setViewMode("kanban");
                  setStatusFilter(null);
                }}
                className={`h-full min-h-0 flex items-center gap-2 px-4 rounded-md text-sm font-medium transition-all ${
                  viewMode === "kanban"
                    ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                    : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
                }`}
                title={t("admin.contact.kanbanView")}
              >
                <LayoutGrid className="w-4 h-4 shrink-0" />
                {t("admin.contact.kanban")}
              </button>
              <button
                onClick={() => setViewMode("list")}
                className={`h-full min-h-0 flex items-center gap-2 px-4 rounded-md text-sm font-medium transition-all ${
                  viewMode === "list"
                    ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                    : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
                }`}
                title={t("admin.contact.listView")}
              >
                <List className="w-4 h-4 shrink-0" />
                {t("admin.contact.list")}
              </button>
            </div>
            <button
              onClick={loadContactMessages}
              disabled={loading}
              className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))] text-sm hover:bg-[rgba(var(--primary),0.3)] transition-colors disabled:opacity-50"
            >
              <RefreshCw
                className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
              />
              {t("admin.common.refresh")}
            </button>
          </div>
        </div>
      </Card>

      {error && (
        <div className="p-4 rounded-lg border border-[rgba(var(--danger),0.3)] bg-[rgba(var(--danger),0.1)]">
          <p className="text-sm text-[rgb(var(--danger))]">{error}</p>
          <button
            onClick={loadContactMessages}
            className="mt-2 text-sm text-[rgba(var(--danger),0.8)] hover:text-[rgba(var(--danger),0.6)] underline"
          >
            {t("admin.common.retry")}
          </button>
        </div>
      )}

      {/* Contenu : Kanban ou liste */}
      <Card disableHover style={{ overflow: "visible" }}>
        {loading && contactMessages.length === 0 ? (
          <AdminInlineLoading message={t("admin.contact.loadingContacts")} />
        ) : contactMessages.length === 0 ? (
          <div className="py-12 text-center">
            <Mail className="h-12 w-12 text-[var(--muted)] mx-auto mb-4 opacity-50" />
            <p className="text-[var(--muted)]">
              {t("admin.contact.noMessages")}
            </p>
          </div>
        ) : viewMode === "kanban" ? (
          <div className="p-6">
            <ContactKanban
              messages={contactMessages}
              onStatusChange={handleUpdateStatus}
              updatingStatusId={updatingStatusId}
              onReply={openReplyModal}
              onDelete={openDeleteModal}
            />
          </div>
        ) : (
          <>
            <Table
              data={contactMessages}
              columns={listColumns}
              emptyMessage={t("admin.contact.noMessages")}
            />

            <Pagination
              mode="offset"
              offset={offset}
              limit={limit}
              total={total}
              onPrevious={handlePrevious}
              onNext={handleNext}
              disabled={loading}
            />
          </>
        )}
      </Card>

      {/* ═══════════ Modale Répondre ═══════════ */}
      <ContactReplyModal
        isOpen={replyModalOpen}
        target={replyTarget}
        replyBody={replyBody}
        onReplyBodyChange={setReplyBody}
        sending={replySending}
        onSend={handleSendReply}
        onClose={closeReplyModal}
      />

      {/* ═══════════ Modale Confirmer Suppression ═══════════ */}
      <ConfirmModal
        isOpen={deleteModalOpen}
        onClose={closeDeleteModal}
        onConfirm={handleConfirmDelete}
        title={t("admin.contact.deleteTitle")}
        message={
          deleteTarget
            ? t("admin.contact.deleteMessage", {
                name: `${deleteTarget.first_name} ${deleteTarget.last_name}`,
                email: deleteTarget.email,
                subject: deleteTarget.subject,
              })
            : ""
        }
        confirmText={t("admin.common.delete")}
        cancelText={t("admin.common.cancel")}
        variant="danger"
        icon={Trash2}
      />
    </div>
  );
}
