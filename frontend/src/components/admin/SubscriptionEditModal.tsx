"use client";

import React, { useState, useEffect } from "react";
import {
  Mail,
  CreditCard,
  DollarSign,
  Calendar,
  ChevronRight,
  Edit,
} from "lucide-react";
import { formatDate } from "../../utils/dateFormat";
import { getStatusLabel } from "../../utils/adminHelpers";
import { GenericButton } from "../buttons";
import Modal from "../Modal";
import { useLanguage } from "../LanguageProvider";

/* ─────────────── Types ─────────────── */

export interface SubscriptionEditTarget {
  email: string;
  subscription_id: string;
  plan: string;
  status: string;
  stripe_customer_id: string | null;
  current_period_end: string | null;
}

interface SubscriptionEditModalProps {
  isOpen: boolean;
  target: SubscriptionEditTarget | null;
  onClose: () => void;
  /** Appelé avec l'ID d'abonnement et les champs modifiés. Doit throw en cas d'erreur. */
  onSave: (
    subscriptionId: string,
    updates: { plan?: string; status?: string },
  ) => Promise<void>;
}

/* ─────────────── Composant ─────────────── */

export default function SubscriptionEditModal({
  isOpen,
  target,
  onClose,
  onSave,
}: SubscriptionEditModalProps) {
  const { t } = useLanguage();
  const [editPlan, setEditPlan] = useState("");
  const [editStatus, setEditStatus] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (target) {
      setEditPlan(target.plan);
      setEditStatus(target.status);
    }
  }, [target]);

  const handleSave = async () => {
    if (!target) return;
    setSaving(true);
    try {
      const updates: Record<string, string> = {};
      if (editPlan !== target.plan) updates.plan = editPlan;
      if (editStatus !== target.status) updates.status = editStatus;

      if (Object.keys(updates).length === 0) {
        onClose();
        return;
      }

      await onSave(target.subscription_id, updates);
      onClose();
    } catch {
      // L'erreur est gérée par le parent (toast), on garde la modal ouverte
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2">
          <Edit className="w-5 h-5 text-[rgb(var(--primary))]" />
          <span>{t("admin.subscriptionEdit.title")}</span>
        </div>
      }
      maxWidth="450px"
    >
      {target && (
        <div className="space-y-5">
          {/* Email */}
          <div className="flex items-center gap-3">
            <Mail className="w-5 h-5 text-[var(--muted)]" />
            <div>
              <p className="text-xs text-[var(--muted)] uppercase tracking-wider">
                {t("admin.subscriptionEdit.user")}
              </p>
              <p className="text-sm text-[var(--text)] font-medium">
                {target.email}
              </p>
            </div>
          </div>

          {/* ID Abonnement */}
          <div className="flex items-center gap-3">
            <CreditCard className="w-5 h-5 text-[var(--muted)]" />
            <div>
              <p className="text-xs text-[var(--muted)] uppercase tracking-wider">
                {t("admin.subscriptionEdit.subscriptionId")}
              </p>
              <p className="text-xs text-[var(--muted)] font-mono">
                {target.subscription_id}
              </p>
            </div>
          </div>

          {/* Sélecteur Plan */}
          <div>
            <label className="block text-xs text-[var(--muted)] uppercase tracking-wider mb-2">
              {t("admin.subscriptionEdit.plan")}
            </label>
            <div className="flex gap-2">
              {["free", "premium"].map((p) => (
                <button
                  key={p}
                  onClick={() => setEditPlan(p)}
                  className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-all border ${
                    editPlan === p
                      ? "bg-[rgba(var(--primary),0.2)] border-[rgb(var(--primary))] text-[rgb(var(--primary))]"
                      : "border-[var(--border)] text-[var(--muted)] hover:border-[var(--text)] hover:text-[var(--text)]"
                  }`}
                >
                  {p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Sélecteur Statut */}
          <div>
            <label className="block text-xs text-[var(--muted)] uppercase tracking-wider mb-2">
              {t("admin.subscriptionEdit.status")}
            </label>
            <div className="grid grid-cols-2 gap-2">
              {["active", "trial", "canceled", "suspended"].map((s) => (
                <button
                  key={s}
                  onClick={() => setEditStatus(s)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-all border ${
                    editStatus === s
                      ? "bg-[rgba(var(--primary),0.2)] border-[rgb(var(--primary))] text-[rgb(var(--primary))]"
                      : "border-[var(--border)] text-[var(--muted)] hover:border-[var(--text)] hover:text-[var(--text)]"
                  }`}
                >
                  {getStatusLabel(s)}
                </button>
              ))}
            </div>
          </div>

          {/* Stripe info */}
          {target.stripe_customer_id && (
            <div className="flex items-center gap-3">
              <DollarSign className="w-5 h-5 text-[rgb(52,211,153)]" />
              <div>
                <p className="text-xs text-[var(--muted)] uppercase tracking-wider">
                  {t("admin.subscriptionEdit.stripeCustomer")}
                </p>
                <p className="text-xs text-[var(--text)] font-mono">
                  {target.stripe_customer_id}
                </p>
              </div>
            </div>
          )}

          {/* Fin de période */}
          {target.current_period_end && (
            <div className="flex items-center gap-3">
              <Calendar className="w-5 h-5 text-[var(--muted)]" />
              <div>
                <p className="text-xs text-[var(--muted)] uppercase tracking-wider">
                  {t("admin.subscriptionEdit.periodEnd")}
                </p>
                <p className="text-sm text-[var(--text)]">
                  {formatDate(target.current_period_end)}
                </p>
              </div>
            </div>
          )}

          {/* Indicateur de changement */}
          {(editPlan !== target.plan || editStatus !== target.status) && (
            <div className="p-3 rounded-lg bg-[rgba(var(--primary),0.1)] border border-[rgba(var(--primary),0.2)]">
              <div className="flex items-center gap-2 text-sm text-[rgb(var(--primary))]">
                <ChevronRight className="w-4 h-4" />
                <span>
                  {editPlan !== target.plan &&
                    `Plan : ${target.plan} → ${editPlan}`}
                  {editPlan !== target.plan &&
                    editStatus !== target.status &&
                    " | "}
                  {editStatus !== target.status &&
                    `Statut : ${getStatusLabel(target.status)} → ${getStatusLabel(editStatus)}`}
                </span>
              </div>
            </div>
          )}

          {/* Boutons */}
          <div className="flex gap-3 pt-2">
            <GenericButton
              label={t("admin.subscriptionEdit.cancel")}
              onClick={onClose}
              variant="secondary"
              className="flex-1"
            />
            <GenericButton
              label={
                saving
                  ? t("admin.subscriptionEdit.saving")
                  : t("admin.subscriptionEdit.save")
              }
              onClick={handleSave}
              disabled={
                saving ||
                (editPlan === target.plan && editStatus === target.status)
              }
              variant="primary"
              className="flex-1"
            />
          </div>
        </div>
      )}
    </Modal>
  );
}
