"use client";

import { useState, useEffect } from "react";
import { X } from "lucide-react";
import Drawer from "../../ui/Drawer";
import { GenericButton } from "../../buttons";
import { useLanguage } from "../../LanguageProvider";
import { MAX_TAGS, MAX_TAG_LENGTH } from "../../../utils/apiKeyUtils";
import ExpiryFormSection from "./ExpiryFormSection";

export interface ApiKeyFormValues {
  name: string;
  tags: string[];
  description: string;
  expiryMode: "preset" | "date";
  ttlDays: string;
  expiryDate: string;
}

/** Données prêtes pour l'API (onSubmit reçoit ce format). */
export interface ApiKeyFormSubmitData {
  name: string;
  tags: string[];
  description: string;
  expiryMode: "preset" | "date";
  ttlDays: string;
  expiryDate: string;
}

export const getEmptyFormValues = (): ApiKeyFormValues => ({
  name: "",
  tags: [],
  description: "",
  expiryMode: "preset",
  ttlDays: "30",
  expiryDate: "",
});

function toDateOnly(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toISOString().split("T")[0];
}

export function keyItemToFormValues(item: {
  name: string;
  tags: string[] | null;
  description: string | null;
  expires_at: string | null;
}): ApiKeyFormValues {
  return {
    name: item.name,
    tags: item.tags ?? [],
    description: item.description ?? "",
    expiryMode: !item.expires_at ? "preset" : "date",
    ttlDays: !item.expires_at ? "0" : "30",
    expiryDate: toDateOnly(item.expires_at),
  };
}

export interface ApiKeyFormDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  submitLabel: string;
  initialValues: ApiKeyFormValues;
  onSubmit: (data: ApiKeyFormSubmitData) => Promise<void>;
}

export default function ApiKeyFormDrawer({
  isOpen,
  onClose,
  title,
  submitLabel,
  initialValues,
  onSubmit,
}: ApiKeyFormDrawerProps) {
  const { t } = useLanguage();
  const [name, setName] = useState(initialValues.name);
  const [tags, setTags] = useState<string[]>(initialValues.tags);
  const [tagsInput, setTagsInput] = useState("");
  const [description, setDescription] = useState(initialValues.description);
  const [expiryMode, setExpiryMode] = useState<"preset" | "date">(
    initialValues.expiryMode,
  );
  const [ttlDays, setTtlDays] = useState(initialValues.ttlDays);
  const [expiryDate, setExpiryDate] = useState(initialValues.expiryDate);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setName(initialValues.name);
      setTags(initialValues.tags);
      setTagsInput("");
      setDescription(initialValues.description);
      setExpiryMode(initialValues.expiryMode);
      setTtlDays(initialValues.ttlDays);
      setExpiryDate(initialValues.expiryDate);
    }
  }, [
    isOpen,
    initialValues.name,
    initialValues.tags,
    initialValues.description,
    initialValues.expiryMode,
    initialValues.ttlDays,
    initialValues.expiryDate,
  ]);

  const handleClose = () => {
    setName(initialValues.name);
    setTags(initialValues.tags);
    setTagsInput("");
    setDescription(initialValues.description);
    setExpiryMode(initialValues.expiryMode);
    setTtlDays(initialValues.ttlDays);
    setExpiryDate(initialValues.expiryDate);
    onClose();
  };

  const handleSubmit = async () => {
    const trimmedName = name.trim();
    if (!trimmedName) return;
    if (expiryMode === "date" && !expiryDate) return;
    setLoading(true);
    try {
      await onSubmit({
        name: trimmedName,
        tags: [...tags],
        description: description.trim(),
        expiryMode,
        ttlDays,
        expiryDate,
      });
      handleClose();
    } catch {
      // Parent handles error toast
    } finally {
      setLoading(false);
    }
  };

  const handleTagsKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const parts = tagsInput
        .split(",")
        .map((s) => s.trim().slice(0, MAX_TAG_LENGTH))
        .filter(Boolean);
      if (parts.length > 0) {
        setTags((prev) => {
          const next = [...prev, ...parts].filter(
            (tag, i, a) => a.indexOf(tag) === i,
          );
          return next.slice(0, MAX_TAGS);
        });
        setTagsInput("");
      }
    }
  };

  const isDisabled =
    !name.trim() || loading || (expiryMode === "date" && !expiryDate);

  return (
    <Drawer
      isOpen={isOpen}
      onClose={handleClose}
      title={title}
      width="min(420px,90vw)"
    >
      <div className="flex flex-col h-full min-h-0">
        <div className="flex-1 overflow-y-auto min-h-0 space-y-4 pr-1 -mr-1">
          <div>
            <label className="block text-sm font-medium text-[var(--text)] mb-2">
              {t("scanner.clesApi.createNameLabel")}
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("scanner.clesApi.createNamePlaceholder")}
              className="auth-input w-full"
              maxLength={100}
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text)] mb-2">
              {t("scanner.clesApi.createTtlLabel")}
            </label>
            <ExpiryFormSection
              mode={expiryMode}
              onModeChange={setExpiryMode}
              ttlDays={ttlDays}
              onTtlDaysChange={setTtlDays}
              expiryDate={expiryDate}
              onExpiryDateChange={setExpiryDate}
              t={t}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text)] mb-2">
              {t("scanner.clesApi.tagsLabel")}
            </label>
            <input
              type="text"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              onKeyDown={handleTagsKeyDown}
              placeholder={t("scanner.clesApi.tagsPlaceholder")}
              className="auth-input w-full"
            />
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-[var(--color-surface)] border border-[var(--color-border)] text-sm text-[var(--text)]"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() =>
                        setTags((prev) => prev.filter((x) => x !== tag))
                      }
                      className="p-0.5 rounded hover:bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] hover:text-[var(--text)] transition-colors"
                      aria-label={t("common.remove")}
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-[var(--text)] mb-2">
              {t("scanner.clesApi.descriptionLabel")}
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t("scanner.clesApi.descriptionPlaceholder")}
              className="auth-input w-full min-h-[80px] resize-y"
              maxLength={500}
              rows={3}
            />
          </div>
        </div>
        <div className="shrink-0 flex justify-end gap-3 pt-4 mt-4 bg-transparent">
          <GenericButton
            label={t("common.cancel")}
            onClick={handleClose}
            variant="secondary"
          />
          <GenericButton
            label={submitLabel}
            onClick={handleSubmit}
            variant="primary"
            disabled={isDisabled}
          />
        </div>
      </div>
    </Drawer>
  );
}
