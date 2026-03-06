"use client";

import { useState } from "react";
import Modal from "../../ui/Modal";
import { GenericButton } from "../../buttons";
import { ScheduleFormPanel, ScheduleDateFields } from "../../schedule";
import { useLanguage } from "../../LanguageProvider";

interface SendEmailRecord {
  id: number;
  subject: string;
  [key: string]: unknown;
}

interface SendEmailModalProps {
  isOpen: boolean;
  email: SendEmailRecord | null;
  onClose: () => void;
  onSend: (
    emailId: number,
    scheduleType: "now" | "scheduled",
    scheduledDate?: string,
    scheduledTime?: string,
  ) => void;
  sending: number | string | null;
  emailLabel: string;
}

export default function SendEmailModal({
  isOpen,
  email,
  onClose,
  onSend,
  sending,
  emailLabel,
}: SendEmailModalProps) {
  const { t } = useLanguage();
  const [scheduleType, setScheduleType] = useState<"now" | "scheduled">("now");
  const [scheduledDate, setScheduledDate] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");

  const handleClose = () => {
    setScheduleType("now");
    setScheduledDate("");
    setScheduledTime("");
    onClose();
  };

  if (!email) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t("admin.emails.sendEmail", { label: emailLabel })}
      maxWidth="500px"
    >
      <div className="space-y-6 min-w-0">
        <div className="space-y-3">
          <label className="radio-option-card flex items-center gap-3 p-3 rounded-lg border border-[var(--border)] bg-[var(--color-surface-subtle)] hover:bg-[var(--color-surface-input)] cursor-pointer">
            <input
              type="radio"
              name="scheduleType"
              value="now"
              checked={scheduleType === "now"}
              onChange={(e) =>
                setScheduleType(e.target.value as "now" | "scheduled")
              }
              className="flex-shrink-0"
            />
            <span className="text-sm font-medium text-[var(--text)]">
              {t("admin.emails.sendNow")}
            </span>
          </label>
          <label className="radio-option-card flex items-center gap-3 p-3 rounded-lg border border-[var(--border)] bg-[var(--color-surface-subtle)] hover:bg-[var(--color-surface-input)] cursor-pointer">
            <input
              type="radio"
              name="scheduleType"
              value="scheduled"
              checked={scheduleType === "scheduled"}
              onChange={(e) =>
                setScheduleType(e.target.value as "now" | "scheduled")
              }
              className="flex-shrink-0"
            />
            <span className="text-sm font-medium text-[var(--text)]">
              {t("admin.emails.scheduleSend")}
            </span>
          </label>
        </div>
        {scheduleType === "scheduled" && (
          <ScheduleFormPanel>
            <ScheduleDateFields
              dateLabelKey="admin.emails.sendDate"
              timeLabelKey="admin.emails.sendTime"
              timeHintKey="admin.emails.optionalDefaultMidnight"
              scheduledDate={scheduledDate}
              scheduledTime={scheduledTime}
              onDateChange={setScheduledDate}
              onTimeChange={setScheduledTime}
              minDate={new Date().toISOString().split("T")[0]}
            />
          </ScheduleFormPanel>
        )}
        <div className="flex justify-end gap-3 pt-4 border-t border-[var(--border)]">
          <GenericButton
            label={t("admin.common.cancel")}
            onClick={handleClose}
            variant="secondary"
          />
          <GenericButton
            label={
              sending === email.id
                ? t("admin.emails.sending")
                : scheduleType === "scheduled"
                  ? t("admin.emails.schedule")
                  : t("admin.common.send")
            }
            onClick={() =>
              onSend(
                email.id,
                scheduleType,
                scheduledDate,
                scheduleType === "scheduled"
                  ? scheduledTime || "00:00"
                  : undefined,
              )
            }
            disabled={
              sending === email.id ||
              (scheduleType === "scheduled" && !scheduledDate)
            }
            variant="primary"
          />
        </div>
      </div>
    </Modal>
  );
}
