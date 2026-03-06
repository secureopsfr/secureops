"use client";

import { useState, useMemo } from "react";
import { Mail, Bell } from "lucide-react";
import EmailManagement from "./EmailManagement";
import adminService from "../../services/admin";
import { useLanguage } from "../LanguageProvider";

/* ─────────────────────── Types ─────────────────────── */

type MailMode = "newsletter" | "notifications";

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

interface ModeConfig {
  label: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  subscribersLabel: string;
  emailLabel: string;
  getEmailsMethod: () => Promise<EmailRecord[]>;
  getSubscribersMethod: () => Promise<SubscriberRecord[]>;
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
}

/* ─────────────────────── Composant ─────────────────────── */

export default function MailManagement() {
  const { t } = useLanguage();
  const [mode, setMode] = useState<MailMode>("newsletter");

  const configs = useMemo<Record<MailMode, ModeConfig>>(
    () => ({
      newsletter: {
        label: t("admin.emails.newsletter"),
        icon: <Mail className="w-4 h-4" />,
        title: t("admin.emails.newsletterTitle"),
        description: t("admin.emails.newsletterDescription"),
        subscribersLabel: t("admin.emails.subscribersLabel"),
        emailLabel: t("admin.emails.emailNewsletter"),
        getEmailsMethod: () => adminService.getNewsletterEmails(),
        getSubscribersMethod: async () => {
          const data = await adminService.getMailingList();
          return data;
        },
        createEmailMethod: (data) => adminService.createNewsletterEmail(data),
        updateEmailMethod: (id, data) =>
          adminService.updateNewsletterEmail(id, data),
        deleteEmailMethod: (id) => adminService.deleteNewsletterEmail(id),
        sendEmailMethod: (id) => adminService.sendNewsletterEmail(id),
        scheduleEmailMethod: (id, date) =>
          adminService.scheduleNewsletterEmail(id, date),
        cancelScheduleMethod: (id) => adminService.cancelScheduledEmail(id),
        deleteSubscriberMethod: (email) => adminService.deleteSubscriber(email),
      },
      notifications: {
        label: t("admin.emails.notifications"),
        icon: <Bell className="w-4 h-4" />,
        title: t("admin.emails.notificationsTitle"),
        description: t("admin.emails.notificationsDescription"),
        subscribersLabel: t("admin.emails.notificationSubscribers"),
        emailLabel: t("admin.emails.emailNotification"),
        getEmailsMethod: () => adminService.getNotificationEmails(),
        getSubscribersMethod: async () => {
          const data = await adminService.getNotificationSubscribers();
          return data;
        },
        createEmailMethod: (data) => adminService.createNotificationEmail(data),
        updateEmailMethod: (id, data) =>
          adminService.updateNotificationEmail(id, data),
        deleteEmailMethod: (id) => adminService.deleteNotificationEmail(id),
        sendEmailMethod: (id) => adminService.sendNotificationEmail(id),
        scheduleEmailMethod: (id, date) =>
          adminService.scheduleNotificationEmail(id, date),
        cancelScheduleMethod: (id) =>
          adminService.cancelScheduledNotification(id),
        deleteSubscriberMethod: (email) => adminService.deleteSubscriber(email),
      },
    }),
    [t],
  );

  const current = configs[mode];
  const modeOptions = (["newsletter", "notifications"] as MailMode[]).map(
    (m) => ({
      id: m,
      label: configs[m].label,
      icon: configs[m].icon,
    }),
  );

  return (
    <div className="space-y-6">
      <EmailManagement
        key={mode}
        emailType={mode === "notifications" ? "notification" : "newsletter"}
        mode={mode}
        onModeChange={(m) => setMode(m as MailMode)}
        modeOptions={modeOptions}
        title={current.title}
        description={current.description}
        getEmailsMethod={current.getEmailsMethod}
        getSubscribersMethod={current.getSubscribersMethod}
        createEmailMethod={current.createEmailMethod}
        updateEmailMethod={current.updateEmailMethod}
        deleteEmailMethod={current.deleteEmailMethod}
        sendEmailMethod={current.sendEmailMethod}
        scheduleEmailMethod={current.scheduleEmailMethod}
        cancelScheduleMethod={current.cancelScheduleMethod}
        deleteSubscriberMethod={current.deleteSubscriberMethod}
        subscribersLabel={current.subscribersLabel}
        emailLabel={current.emailLabel}
      />
    </div>
  );
}
