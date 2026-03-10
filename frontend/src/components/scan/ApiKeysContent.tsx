"use client";

import { useState } from "react";
import { Key, Plus, Trash2, Pencil } from "lucide-react";
import { SectionCard } from "../ui/cards";
import Table from "../Table";
import LoadingScreen from "../LoadingScreen";
import ConfirmModal from "../ConfirmModal";
import { GenericButton } from "../buttons";
import { useLanguage } from "../LanguageProvider";
import { revokeApiKey, type ApiKeyItem } from "../../services/apiKeysService";
import { showSuccessToast } from "../../utils/toastNotifications";
import { formatDateTimeShort } from "../../utils/dateFormat";
import { useApiKeys } from "../../hooks/useApiKeys";
import CreateKeyDrawer from "./apiKeys/CreateKeyDrawer";
import EditKeyDrawer from "./apiKeys/EditKeyDrawer";
import KeyDisplayModal from "./apiKeys/KeyDisplayModal";

export default function ApiKeysContent() {
  const { t } = useLanguage();
  const { keys, loading, loadKeys, handleError } = useApiKeys({ t });

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [showKeyModalOpen, setShowKeyModalOpen] = useState(false);
  const [createdKey, setCreatedKey] = useState<{
    id: string;
    key: string;
    name: string;
    created_at: string;
    expires_at: string | null;
  } | null>(null);
  const [revokeModalOpen, setRevokeModalOpen] = useState(false);
  const [keyToRevoke, setKeyToRevoke] = useState<ApiKeyItem | null>(null);
  const [revokeLoading, setRevokeLoading] = useState(false);
  const [editDrawerOpen, setEditDrawerOpen] = useState(false);
  const [keyToEdit, setKeyToEdit] = useState<ApiKeyItem | null>(null);

  const openRevokeModal = (item: ApiKeyItem) => {
    setKeyToRevoke(item);
    setRevokeModalOpen(true);
  };

  const openEditDrawer = (item: ApiKeyItem) => {
    setKeyToEdit(item);
    setEditDrawerOpen(true);
  };

  const handleRevoke = async () => {
    if (!keyToRevoke) return;
    setRevokeLoading(true);
    try {
      await revokeApiKey(keyToRevoke.id);
      showSuccessToast(t("scanner.clesApi.revokeSuccess"));
      setRevokeModalOpen(false);
      setKeyToRevoke(null);
      await loadKeys();
    } catch (e) {
      handleError(e, "revoke");
    } finally {
      setRevokeLoading(false);
    }
  };

  return (
    <>
      <SectionCard
        icon={Key}
        title={t("scanner.clesApi.sectionTitle")}
        compact
        headerAction={
          <GenericButton
            label={t("scanner.clesApi.createBtn")}
            onClick={() => setCreateModalOpen(true)}
            variant="primary"
            icon={<Plus className="w-4 h-4" />}
          />
        }
      >
        <div className="flex flex-col gap-3">
          <p className="text-[var(--color-text-muted)] text-sm">
            {t("scanner.clesApi.sectionIntro")}
          </p>
          {loading ? (
            <LoadingScreen
              variant="section"
              message={t("scanner.clesApi.loading")}
            />
          ) : keys.length === 0 ? (
            <div className="rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center">
              <Key className="w-12 h-12 text-[var(--color-text-muted)] mx-auto mb-3 opacity-40" />
              <p className="text-[var(--color-text-muted)] mb-4">
                {t("scanner.clesApi.empty")}
              </p>
              <GenericButton
                label={t("scanner.clesApi.createBtn")}
                onClick={() => setCreateModalOpen(true)}
                variant="primary"
              />
            </div>
          ) : (
            <Table<ApiKeyItem & Record<string, unknown>>
              data={keys as (ApiKeyItem & Record<string, unknown>)[]}
              columns={[
                {
                  key: "name",
                  header: t("scanner.clesApi.colName"),
                  render: (item) => (
                    <span className="font-medium text-[var(--text)]">
                      {item.name}
                    </span>
                  ),
                  sortable: true,
                  align: "left",
                },
                {
                  key: "prefix",
                  header: t("scanner.clesApi.colKey"),
                  render: (item) => (
                    <span className="font-mono text-sm text-[var(--color-text-muted)]">
                      {item.prefix}…
                    </span>
                  ),
                  sortable: true,
                  align: "left",
                },
                {
                  key: "created_at",
                  header: t("scanner.clesApi.colCreatedAt"),
                  render: (item) => (
                    <span className="text-[var(--color-text-muted)]">
                      {formatDateTimeShort(item.created_at)}
                    </span>
                  ),
                  sortable: true,
                },
                {
                  key: "expires_at",
                  header: t("scanner.clesApi.colExpiresAt"),
                  render: (item) =>
                    item.expires_at ? (
                      <span className="text-[var(--color-text-muted)]">
                        {formatDateTimeShort(item.expires_at)}
                      </span>
                    ) : (
                      <span className="text-[var(--color-text-muted)]">—</span>
                    ),
                  sortable: true,
                },
                {
                  key: "tags",
                  header: t("scanner.clesApi.colTags"),
                  align: "center",
                  render: (item) =>
                    item.tags?.length ? (
                      <div className="flex flex-wrap gap-1 justify-center">
                        {item.tags.map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex px-1.5 py-0.5 rounded bg-[var(--color-surface)] text-[var(--color-text-muted)] text-xs"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-[var(--color-text-muted)]">—</span>
                    ),
                  sortable: false,
                },
                {
                  key: "description",
                  header: t("scanner.clesApi.colDescription"),
                  render: (item) =>
                    item.description ? (
                      <span
                        className="text-sm text-[var(--color-text-muted)] line-clamp-2 max-w-[200px]"
                        title={item.description}
                      >
                        {item.description}
                      </span>
                    ) : (
                      <span className="text-[var(--color-text-muted)]">—</span>
                    ),
                  sortable: false,
                  align: "left",
                },
                {
                  key: "actions",
                  header: t("scanner.clesApi.colActions"),
                  render: (item) => (
                    <div className="flex items-center justify-center gap-1">
                      <button
                        type="button"
                        onClick={() => openEditDrawer(item)}
                        className="p-2 rounded hover:bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] hover:text-[rgb(var(--primary))] transition-colors"
                        aria-label={t("scanner.clesApi.editKey")}
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => openRevokeModal(item)}
                        className="p-2 rounded hover:bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] hover:text-red-500 transition-colors"
                        aria-label={t("scanner.clesApi.revoke")}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ),
                  sortable: false,
                  align: "center",
                },
              ]}
              defaultSort={{ key: "created_at", direction: "desc" }}
              emptyMessage={t("scanner.clesApi.empty")}
            />
          )}
        </div>
      </SectionCard>

      <EditKeyDrawer
        isOpen={editDrawerOpen}
        onClose={() => {
          setEditDrawerOpen(false);
          setKeyToEdit(null);
        }}
        keyItem={keyToEdit}
        loadKeys={loadKeys}
      />

      <CreateKeyDrawer
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onSuccess={(result) => {
          setCreatedKey(result);
          setShowKeyModalOpen(true);
        }}
        loadKeys={loadKeys}
      />

      <KeyDisplayModal
        isOpen={showKeyModalOpen}
        onClose={() => {
          setShowKeyModalOpen(false);
          setCreatedKey(null);
        }}
        createdKey={createdKey}
      />

      <ConfirmModal
        isOpen={revokeModalOpen}
        onClose={() => {
          setRevokeModalOpen(false);
          setKeyToRevoke(null);
        }}
        onConfirm={handleRevoke}
        title={t("scanner.clesApi.revokeConfirmTitle")}
        message={
          keyToRevoke
            ? t("scanner.clesApi.revokeConfirmMessage", {
                name: keyToRevoke.name,
              })
            : ""
        }
        confirmText={t("scanner.clesApi.revoke")}
        variant="danger"
        icon={Trash2}
        loading={revokeLoading}
      />
    </>
  );
}
