"use client";

import React, { useState, useEffect } from "react";
import { Shield, ShieldCheck, ShieldAlert } from "lucide-react";
import type { UserRecord } from "../../services/admin";
import { GenericButton } from "../buttons";
import Modal from "../Modal";
import { useLanguage } from "../LanguageProvider";

/* ─────────── Constantes ─────────── */

const GROUP_OPTIONS = [
  {
    value: "user",
    labelKey: "admin.userGroup.user" as const,
    descKey: "admin.userGroup.userDesc" as const,
    icon: <Shield className="w-5 h-5" />,
  },
  {
    value: "beta",
    labelKey: "admin.userGroup.betaTester" as const,
    descKey: "admin.userGroup.betaDesc" as const,
    icon: <ShieldCheck className="w-5 h-5" />,
  },
  {
    value: "admin",
    labelKey: "admin.userGroup.admin" as const,
    descKey: "admin.userGroup.adminDesc" as const,
    icon: <ShieldAlert className="w-5 h-5" />,
  },
] as const;

function getCurrentGroup(user: UserRecord): string {
  const groups = user.cognito_groups || [];
  if (groups.includes("admin")) return "admin";
  if (groups.includes("beta")) return "beta";
  return "user";
}

/* ─────────── Composant ─────────── */

interface UserGroupModalProps {
  isOpen: boolean;
  user: UserRecord | null;
  loading: boolean;
  onClose: () => void;
  onConfirm: (group: string) => void;
}

export default function UserGroupModal({
  isOpen,
  user,
  loading,
  onClose,
  onConfirm,
}: UserGroupModalProps) {
  const { t } = useLanguage();
  const [selectedGroup, setSelectedGroup] = useState("user");

  // Synchroniser le groupe sélectionné quand l'utilisateur change
  useEffect(() => {
    if (user) setSelectedGroup(getCurrentGroup(user));
  }, [user]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t("admin.userGroup.title")}
      maxWidth="450px"
    >
      {user && (
        <div className="space-y-5">
          <p className="text-sm text-[var(--muted)]">
            {t("admin.userGroup.description")}{" "}
            <strong className="text-[var(--text)]">{user.email}</strong>
          </p>

          <div className="space-y-3">
            {GROUP_OPTIONS.map((option) => {
              const isSelected = selectedGroup === option.value;
              return (
                <button
                  key={option.value}
                  onClick={() => setSelectedGroup(option.value)}
                  className={`w-full flex items-center gap-4 p-4 rounded-lg border transition-all ${
                    isSelected
                      ? "border-[rgb(var(--primary))] bg-[rgba(var(--primary),0.1)]"
                      : "border-[var(--border)] bg-transparent hover:bg-[var(--color-surface-hover)]"
                  }`}
                >
                  <div
                    className={`p-2 rounded-lg ${
                      isSelected
                        ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                        : "bg-[var(--color-surface-subtle)] text-[var(--muted)]"
                    }`}
                  >
                    {option.icon}
                  </div>
                  <div className="text-left flex-1">
                    <p
                      className={`text-sm font-medium ${isSelected ? "text-[rgb(var(--primary))]" : "text-[var(--text)]"}`}
                    >
                      {t(option.labelKey)}
                    </p>
                    <p className="text-xs text-[var(--muted)]">
                      {t(option.descKey)}
                    </p>
                  </div>
                  {isSelected && (
                    <div className="w-2 h-2 rounded-full bg-[rgb(var(--primary))]" />
                  )}
                </button>
              );
            })}
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--border)]">
            <GenericButton
              label={t("admin.userGroup.cancel")}
              onClick={onClose}
              variant="secondary"
            />
            <GenericButton
              label={t("admin.userGroup.confirm")}
              onClick={() => onConfirm(selectedGroup)}
              loading={loading}
              loadingLabel={t("admin.userGroup.updating")}
              variant="primary"
            />
          </div>
        </div>
      )}
    </Modal>
  );
}
