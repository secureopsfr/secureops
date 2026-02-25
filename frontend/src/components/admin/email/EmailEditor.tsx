"use client";

import { useMemo, useCallback } from "react";
import useSWR from "swr";
import { Eye, X, Plus, FileCode2 } from "lucide-react";
import Card from "../../cards/Card";
import { GenericButton } from "../../buttons";
import DropdownSelector from "../../buttons/DropdownSelector";
import StructuredContentEditor from "../../StructuredContentEditor";
import { useLanguage } from "../../LanguageProvider";
import adminService from "../../../services/admin";
import type { TemplateRecord } from "../../../services/admin";

export interface EmailFormData {
  subject: string;
  content: string;
  template_name: string;
}

interface EmailEditorProps {
  mode: "create" | "edit";
  formData: EmailFormData;
  onFormDataChange: (data: EmailFormData) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  isLoading: boolean;
  error: string | null;
  availableTemplates: TemplateRecord[];
  emailLabel: string;
  title: string;
}

export default function EmailEditor({
  mode,
  formData,
  onFormDataChange,
  onSubmit,
  onCancel,
  isLoading,
  error,
  availableTemplates,
  emailLabel,
  title,
}: EmailEditorProps) {
  const { t } = useLanguage();
  const isEdit = mode === "edit";

  /* ── Preview : charge le HTML du template et remplace les placeholders ── */
  const { data: templateData } = useSWR(
    formData.template_name
      ? ["template-content", formData.template_name]
      : null,
    () => adminService.getTemplateContent(formData.template_name),
  );

  const renderPreview = useCallback(
    (rawTemplate: string | undefined, subject: string, content: string) => {
      if (!rawTemplate) return "";
      return rawTemplate
        .replace(/\{\{subject\}\}/g, subject || "…")
        .replace(/\{\{content\}\}/g, content || "")
        .replace(/\{\{frontend_url\}\}/g, "#")
        .replace(/\{\{unsubscribe_url\}\}/g, "#");
    },
    [],
  );

  const previewHtml = useMemo(
    () =>
      renderPreview(templateData?.content, formData.subject, formData.content),
    [renderPreview, templateData?.content, formData.subject, formData.content],
  );

  /* ── Labels ── */
  const headingText = isEdit
    ? t("admin.emails.editEmail", { label: emailLabel })
    : t("admin.emails.createNew", { label: emailLabel });

  const submitLabel = isEdit
    ? isLoading
      ? t("admin.emails.saving")
      : t("admin.emails.saveChanges")
    : isLoading
      ? t("admin.emails.creating")
      : t("admin.common.create");

  return (
    <Card disableHover>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[var(--text)] flex items-center gap-2">
            {!isEdit && <Plus className="w-5 h-5" />}
            {headingText}
          </h2>
          {isEdit && (
            <p className="text-sm text-[var(--muted)] mt-1">
              {t("admin.emails.editDescription", { label: emailLabel })}
            </p>
          )}
        </div>
        {isEdit ? (
          <GenericButton
            label={t("admin.emails.backToList")}
            onClick={onCancel}
            variant="secondary"
          />
        ) : (
          <button
            onClick={onCancel}
            className="text-[var(--muted)] hover:text-[var(--text)] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 p-4 rounded-lg border border-[rgba(var(--danger),0.3)] bg-[rgba(var(--danger),0.1)]">
          <p className="text-sm text-[rgb(var(--danger))]">{error}</p>
        </div>
      )}

      <form onSubmit={onSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-[var(--text)] mb-2">
            {t("admin.emails.emailSubject", { label: emailLabel })}
          </label>
          <input
            type="text"
            value={formData.subject}
            onChange={(e) =>
              onFormDataChange({ ...formData, subject: e.target.value })
            }
            required
            className="auth-input"
            placeholder={`Ex: ${title} - Janvier 2024`}
          />
        </div>

        {/* Sélecteur de template */}
        <div>
          <label className="block text-sm font-medium text-[var(--text)] mb-2 flex items-center gap-2">
            <FileCode2 className="w-4 h-4" />
            {t("admin.emails.selectTemplate")}
          </label>
          <DropdownSelector
            selectedValue={formData.template_name}
            onChange={(value) =>
              onFormDataChange({ ...formData, template_name: value })
            }
            options={
              availableTemplates.length === 0
                ? [{ value: "newsletter.html", label: "newsletter.html" }]
                : availableTemplates.map((tpl) => ({
                    value: tpl.filename,
                    label: tpl.filename,
                  }))
            }
            width="100%"
          />
          <p className="text-xs text-[var(--muted)] mt-1">
            {t("admin.emails.selectTemplateHint")}
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text)] mb-2">
            {t("admin.emails.emailContent", { label: emailLabel })}
          </label>
          <StructuredContentEditor
            value={formData.content}
            onChange={(html) =>
              onFormDataChange({ ...formData, content: html })
            }
          />
        </div>

        {/* Prévisualisation temps réel */}
        <div>
          <label className="text-sm font-medium text-[var(--text)] flex items-center gap-2 mb-2">
            <Eye className="w-4 h-4" />
            {t("admin.emails.preview")}
          </label>
          <div className="rounded-lg border border-[var(--border)] bg-white overflow-hidden">
            {previewHtml ? (
              <iframe
                srcDoc={previewHtml}
                title={t("admin.emails.preview")}
                className="w-full border-0"
                style={{ minHeight: "400px" }}
                sandbox="allow-same-origin"
              />
            ) : (
              <div className="p-8 text-center text-[var(--muted)] text-sm italic">
                {t("admin.emails.previewPlaceholder", {
                  label: emailLabel,
                })}
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <GenericButton
            label={t("admin.common.cancel")}
            onClick={onCancel}
            disabled={isLoading}
            variant="secondary"
          />
          <GenericButton
            label={submitLabel}
            type="submit"
            disabled={isLoading}
            variant="primary"
          />
        </div>
      </form>
    </Card>
  );
}
