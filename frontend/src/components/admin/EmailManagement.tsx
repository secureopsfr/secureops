"use client";

import { useState, lazy, Suspense } from "react";
import type { ReactNode } from "react";
import useSWR from "swr";
import { Plus, RefreshCw } from "lucide-react";
import { error } from "../../utils/logger";
import { showSuccessToast } from "../../utils/toastNotifications";
import EmailList from "./email/EmailList";
import SubscribersList from "./email/SubscribersList";
import SendEmailModal from "./email/SendEmailModal";
import { AdminInlineLoading } from "./AdminSectionLoading";
import { useLanguage } from "../LanguageProvider";
import {
  useAdminTemplates,
  useAdminEmails,
  useAdminSubscribers,
} from "../../hooks/swr";
import type { AdminEmailType } from "../../hooks/swr";
import type { EmailFormData } from "./email/EmailEditor";

/* ── Lazy-load de l'éditeur (StructuredContentEditor + TipTap) ── */
const EmailEditor = lazy(() => import("./email/EmailEditor"));

/* ── Types ── */

interface EmailRecord {
  id: number;
  subject: string;
  content: string;
  status?: string;
  created_at?: string;
  sent_at?: string;
  scheduled_at?: string;
  recipients_count?: number;
  template_name?: string;
  [key: string]: unknown;
}

interface SubscriberRecord {
  email: string;
  is_verified?: boolean;
  created_at?: string;
  [key: string]: unknown;
}

interface EmailManagementProps {
  title: string;
  description: string;
  /** Type email (newsletter | notification) : si fourni, utilise les hooks SWR dédiés. */
  emailType?: AdminEmailType;
  getEmailsMethod?: () => Promise<EmailRecord[]>;
  getSubscribersMethod?: () => Promise<SubscriberRecord[]>;
  createEmailMethod: (data: {
    subject: string;
    content: string;
    template_name?: string;
  }) => Promise<EmailRecord>;
  updateEmailMethod: (
    id: number,
    data: { subject: string; content: string; template_name?: string },
  ) => Promise<EmailRecord>;
  deleteEmailMethod: (id: number) => Promise<Record<string, unknown>>;
  sendEmailMethod: (id: number) => Promise<Record<string, unknown>>;
  scheduleEmailMethod: (
    id: number,
    date: Date,
  ) => Promise<Record<string, unknown>>;
  cancelScheduleMethod: (id: number) => Promise<Record<string, unknown>>;
  deleteSubscriberMethod: (email: string) => Promise<Record<string, unknown>>;
  subscribersLabel?: string;
  emailLabel?: string;
  /** Mode actuel (newsletter / notifications) pour le toggle */
  mode?: string;
  onModeChange?: (mode: string) => void;
  /** Options du toggle (label + icon par mode) */
  modeOptions?: { id: string; label: string; icon: ReactNode }[];
}

const DEFAULT_FORM: EmailFormData = {
  subject: "",
  content: "",
  template_name: "newsletter.html",
};

export default function EmailManagement({
  title,
  description,
  emailType,
  getEmailsMethod,
  getSubscribersMethod,
  createEmailMethod,
  updateEmailMethod,
  deleteEmailMethod,
  sendEmailMethod,
  scheduleEmailMethod,
  cancelScheduleMethod,
  deleteSubscriberMethod,
  subscribersLabel = "subscribers",
  emailLabel = "email",
  mode,
  onModeChange,
  modeOptions,
}: EmailManagementProps) {
  const { t } = useLanguage();

  /* ── State ── */
  const [mutating, setMutating] = useState(false);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [sending, setSending] = useState<number | string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<EmailFormData>({ ...DEFAULT_FORM });
  const [editingEmail, setEditingEmail] = useState<EmailRecord | null>(null);
  const [editFormData, setEditFormData] = useState<EmailFormData>({
    ...DEFAULT_FORM,
  });
  const [isSavingEdit, setIsSavingEdit] = useState(false);
  const [showSendModal, setShowSendModal] = useState(false);
  const [emailToSend, setEmailToSend] = useState<EmailRecord | null>(null);

  /* ── SWR : templates ── */
  const { templates: availableTemplates } = useAdminTemplates();

  /* ── SWR : emails et abonnés (hooks dédiés si emailType, sinon legacy) ── */
  const emailsFromHook = useAdminEmails(emailType ?? "newsletter");
  const subscribersFromHook = useAdminSubscribers(emailType ?? "newsletter");
  const useHooks = emailType !== undefined;

  const legacyEmailsSWR = useSWR(
    useHooks ? null : ["admin-emails", title],
    async () => {
      const data = await (getEmailsMethod ?? (() => Promise.resolve([])))();
      return Array.isArray(data) ? data : [];
    },
  );
  const legacySubscribersSWR = useSWR(
    useHooks ? null : ["admin-subscribers", title],
    async () => {
      const data = await (
        getSubscribersMethod ?? (() => Promise.resolve([]))
      )();
      return Array.isArray(data) ? data : [];
    },
  );

  const emails = useHooks
    ? emailsFromHook.emails
    : (legacyEmailsSWR.data ?? []);
  const loading = useHooks
    ? emailsFromHook.isLoading
    : legacyEmailsSWR.isLoading;
  const errorMessage = useHooks
    ? emailsFromHook.error instanceof Error
      ? emailsFromHook.error.message
      : emailsFromHook.error
        ? t("admin.emails.errorLoadingEmails")
        : null
    : legacyEmailsSWR.error instanceof Error
      ? legacyEmailsSWR.error.message
      : legacyEmailsSWR.error
        ? t("admin.emails.errorLoadingEmails")
        : null;
  const mutateEmails = useHooks
    ? emailsFromHook.mutate
    : legacyEmailsSWR.mutate;

  const subscribers = useHooks
    ? subscribersFromHook.subscribers
    : (legacySubscribersSWR.data ?? []);
  const subscribersLoading = useHooks
    ? subscribersFromHook.isLoading
    : legacySubscribersSWR.isLoading;
  const subscribersError = useHooks
    ? subscribersFromHook.error instanceof Error
      ? subscribersFromHook.error.message
      : subscribersFromHook.error
        ? t("admin.emails.loadingSubscribers")
        : null
    : legacySubscribersSWR.error instanceof Error
      ? legacySubscribersSWR.error.message
      : legacySubscribersSWR.error
        ? t("admin.emails.loadingSubscribers")
        : null;
  const mutateSubscribers = useHooks
    ? subscribersFromHook.mutate
    : legacySubscribersSWR.mutate;

  const effectiveLoading = loading || mutating;
  const effectiveError = errorMessage || mutationError;

  const loadEmails = () => mutateEmails();
  const loadSubscribers = () => mutateSubscribers();

  /* ── Handlers ── */

  const handleCreateEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setMutating(true);
      await createEmailMethod(formData);
      setFormData({ ...DEFAULT_FORM });
      setShowCreateForm(false);
      showSuccessToast(
        t("admin.emails.created", {
          label: emailLabel.charAt(0).toUpperCase() + emailLabel.slice(1),
        }),
      );
      await loadEmails();
    } catch (err) {
      error(`[EmailManagement] Error creating ${emailLabel}:`, err);
      setMutationError(
        err instanceof Error
          ? err.message
          : t("admin.emails.created", { label: emailLabel }),
      );
    } finally {
      setMutating(false);
    }
  };

  const handleSendEmail = async (
    emailId: number,
    scheduleType: "now" | "scheduled",
    scheduledDate?: string,
    scheduledTime?: string,
  ) => {
    try {
      setSending(emailId);
      if (scheduleType === "scheduled" && scheduledDate && scheduledTime) {
        const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}`);
        await scheduleEmailMethod(emailId, scheduledDateTime);
        showSuccessToast(t("admin.emails.emailScheduled"));
      } else {
        await sendEmailMethod(emailId);
        showSuccessToast(t("admin.emails.emailSent"));
      }
      await loadEmails();
      setShowSendModal(false);
      setEmailToSend(null);
    } catch (err) {
      error(`[EmailManagement] Error sending ${emailLabel}:`, err);
      setMutationError(
        err instanceof Error
          ? err.message
          : t("admin.emails.sendEmail", { label: emailLabel }),
      );
    } finally {
      setSending(null);
    }
  };

  const handleCancelSchedule = async (emailId: number) => {
    try {
      setSending(emailId);
      await cancelScheduleMethod(emailId);
      showSuccessToast(t("admin.emails.scheduleCancel"));
      await loadEmails();
    } catch (err) {
      error(`[EmailManagement] Error canceling schedule:`, err);
      setMutationError(
        err instanceof Error ? err.message : t("admin.emails.cancelSchedule"),
      );
    } finally {
      setSending(null);
    }
  };

  const handleDeleteEmail = async (emailId: number) => {
    if (
      !window.confirm(
        t("admin.emails.confirmDeleteEmail", { label: emailLabel }),
      )
    ) {
      return;
    }
    try {
      setSending(emailId);
      await deleteEmailMethod(emailId);
      showSuccessToast(
        t("admin.emails.deleted", {
          label: emailLabel.charAt(0).toUpperCase() + emailLabel.slice(1),
        }),
      );
      await loadEmails();
    } catch (err) {
      error(`[EmailManagement] Error deleting ${emailLabel}:`, err);
      setMutationError(
        err instanceof Error
          ? err.message
          : t("admin.emails.deleteTooltip", { label: emailLabel }),
      );
    } finally {
      setSending(null);
    }
  };

  const handleEditEmail = (email: EmailRecord) => {
    setEditingEmail(email);
    setEditFormData({
      subject: email.subject || "",
      content: email.content || "",
      template_name: email.template_name || "newsletter.html",
    });
  };

  const handleCancelEdit = () => {
    setEditingEmail(null);
    setEditFormData({ ...DEFAULT_FORM });
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingEmail || !editingEmail.id) return;
    try {
      setIsSavingEdit(true);
      setMutationError(null);
      await updateEmailMethod(editingEmail.id, editFormData);
      showSuccessToast(
        t("admin.emails.updated", {
          label: emailLabel.charAt(0).toUpperCase() + emailLabel.slice(1),
        }),
      );
      await loadEmails();
      setEditingEmail(null);
      setEditFormData({ ...DEFAULT_FORM });
    } catch (err) {
      error(`[EmailManagement] Error updating ${emailLabel}:`, err);
      setMutationError(
        err instanceof Error
          ? err.message
          : t("admin.emails.editEmail", { label: emailLabel }),
      );
    } finally {
      setIsSavingEdit(false);
    }
  };

  const handleDeleteSubscriber = async (email: string) => {
    if (!window.confirm(t("admin.emails.confirmDeleteSubscriber", { email }))) {
      return;
    }
    try {
      setSending(email);
      await deleteSubscriberMethod(email);
      showSuccessToast(t("admin.emails.subscriberDeleted"));
      await loadSubscribers();
    } catch (err) {
      error(`[EmailManagement] Error deleting subscriber:`, err);
      setMutationError(
        err instanceof Error
          ? err.message
          : t("admin.emails.deleteSubscriberTooltip"),
      );
    } finally {
      setSending(null);
    }
  };

  const editorFallback = (
    <AdminInlineLoading message={t("admin.emails.loadingEmails")} />
  );

  /* ── Rendu : mode édition ── */
  if (editingEmail) {
    return (
      <div className="space-y-6">
        <Suspense fallback={editorFallback}>
          <EmailEditor
            mode="edit"
            formData={editFormData}
            onFormDataChange={setEditFormData}
            onSubmit={handleSaveEdit}
            onCancel={handleCancelEdit}
            isLoading={isSavingEdit}
            error={effectiveError}
            availableTemplates={availableTemplates}
            emailLabel={emailLabel}
            title={title}
          />
        </Suspense>
      </div>
    );
  }

  /* ── En-tête pour la carte « email history » : titre, description, toggle, refresh, new email ── */
  const emailHistoryHeaderSlot = (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div>
        <h2 className="text-2xl font-bold text-[var(--text)]">{title}</h2>
        <p className="text-[var(--muted)] mt-1">{description}</p>
      </div>
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        {modeOptions && onModeChange && mode !== undefined && (
          <div className="flex h-9 items-stretch gap-0.5 rounded-lg border border-[var(--border)] p-0.5 bg-[var(--color-surface-subtle)]">
            {modeOptions.map((opt) => (
              <button
                key={opt.id}
                onClick={() => onModeChange(opt.id)}
                className={`h-full min-h-0 flex items-center gap-2 px-4 rounded-md text-sm font-medium transition-all ${
                  mode === opt.id
                    ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                    : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
                }`}
              >
                {opt.icon}
                {opt.label}
              </button>
            ))}
          </div>
        )}
        <button
          onClick={() => {
            loadEmails();
            loadSubscribers();
          }}
          className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))] text-sm hover:bg-[rgba(var(--primary),0.3)] transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          {t("admin.common.refresh")}
        </button>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg bg-[rgb(var(--primary))] text-white text-sm hover:opacity-90 transition-opacity"
        >
          <Plus className="w-4 h-4" />
          {t("admin.emails.newEmail", {
            label: emailLabel.charAt(0).toUpperCase() + emailLabel.slice(1),
          })}
        </button>
      </div>
    </div>
  );

  /* ── Rendu : vue principale ── */
  return (
    <div className="space-y-6">
      {effectiveError && (
        <div className="p-4 rounded-lg border border-[rgba(var(--danger),0.3)] bg-[rgba(var(--danger),0.1)]">
          <p className="text-sm text-[rgb(var(--danger))]">{effectiveError}</p>
        </div>
      )}

      {/* Formulaire de création (lazy-loaded) */}
      {showCreateForm && (
        <Suspense fallback={editorFallback}>
          <EmailEditor
            mode="create"
            formData={formData}
            onFormDataChange={setFormData}
            onSubmit={handleCreateEmail}
            onCancel={() => setShowCreateForm(false)}
            isLoading={effectiveLoading}
            error={null}
            availableTemplates={availableTemplates}
            emailLabel={emailLabel}
            title={title}
          />
        </Suspense>
      )}

      {/* Historique des emails (titre, description, toggle, refresh, new email dans la même carte) */}
      <EmailList
        emails={emails}
        loading={effectiveLoading}
        onEdit={handleEditEmail}
        onDelete={handleDeleteEmail}
        onSend={(email) => {
          setEmailToSend(email);
          setShowSendModal(true);
        }}
        onCancelSchedule={handleCancelSchedule}
        sending={sending}
        subscribersLabel={subscribersLabel}
        emailLabel={emailLabel}
        headerSlot={emailHistoryHeaderSlot}
      />

      {/* Liste des abonnés */}
      <SubscribersList
        subscribers={subscribers}
        loading={subscribersLoading}
        error={subscribersError}
        onDelete={handleDeleteSubscriber}
        onRetry={loadSubscribers}
        sending={sending}
        subscribersLabel={subscribersLabel}
      />

      {/* Modal d'envoi */}
      <SendEmailModal
        isOpen={showSendModal}
        email={emailToSend}
        onClose={() => {
          setShowSendModal(false);
          setEmailToSend(null);
        }}
        onSend={handleSendEmail}
        sending={sending}
        emailLabel={emailLabel}
      />
    </div>
  );
}
