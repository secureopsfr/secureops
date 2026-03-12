"use client";

import { User, FileText, Send } from "lucide-react";
import { GenericButton } from "../../buttons";
import Modal from "../../ui/Modal";
import type { ContactMessage } from "./hooks/useContactManagement";
import { useLanguage } from "../../LanguageProvider";

interface ContactReplyModalProps {
  isOpen: boolean;
  target: ContactMessage | null;
  replyBody: string;
  onReplyBodyChange: (value: string) => void;
  sending: boolean;
  onSend: () => void;
  onClose: () => void;
}

export default function ContactReplyModal({
  isOpen,
  target,
  replyBody,
  onReplyBodyChange,
  sending,
  onSend,
  onClose,
}: ContactReplyModalProps) {
  const { t } = useLanguage();
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t("admin.contact.replyModalTitle")}
      maxWidth="600px"
    >
      {target && (
        <div className="space-y-4 py-2">
          {/* Résumé du message original */}
          <div className="p-4 rounded-lg bg-[var(--color-surface-subtle)] border border-[var(--border)]">
            <div className="flex items-center gap-2 mb-2">
              <User className="w-4 h-4 text-[var(--muted)]" />
              <span className="text-sm font-medium text-[var(--text)]">
                {target.first_name} {target.last_name}
              </span>
              <span className="text-xs text-[var(--muted)]">
                ({target.email})
              </span>
            </div>
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-4 h-4 text-[var(--muted)]" />
              <span className="text-sm font-medium text-[var(--text)]">
                {target.subject}
              </span>
            </div>
            <p className="text-sm text-[var(--muted)] line-clamp-3 ml-6">
              {target.message}
            </p>
          </div>

          {/* Champ de réponse */}
          <div>
            <label className="block text-xs text-[var(--muted)] uppercase tracking-wider mb-2">
              {t("admin.contact.yourReply")}
            </label>
            <textarea
              value={replyBody}
              onChange={(e) => onReplyBodyChange(e.target.value)}
              placeholder={t("admin.contact.replyPlaceholder")}
              rows={6}
              className="input-field w-full resize-y"
              style={{ minHeight: "120px" }}
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-4 border-t border-[var(--border)]">
            <p className="text-xs text-[var(--muted)]">
              {t("admin.contact.emailSentTo", { email: target.email })}
            </p>
            <GenericButton
              label={
                sending
                  ? t("admin.contact.sending")
                  : t("admin.contact.sendReply")
              }
              onClick={onSend}
              disabled={sending || !replyBody.trim()}
              variant="primary"
              icon={<Send className="w-4 h-4" />}
              iconPosition="left"
            />
          </div>
        </div>
      )}
    </Modal>
  );
}
