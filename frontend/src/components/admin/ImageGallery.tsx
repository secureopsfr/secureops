"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Upload,
  Trash2,
  Copy,
  Check,
  Image as ImageIcon,
  HardDrive,
  FileImage,
  RefreshCw,
  ZoomIn,
  X,
  FileCode2,
  FileText,
  Save,
  Eye,
  Code,
  Plus,
} from "lucide-react";
import Image from "next/image";
import Card from "../ui/cards/Card";
import KpiGrid from "./KpiGrid";
import SearchToolbar from "./SearchToolbar";
import ConfirmModal from "../ConfirmModal";
import adminService from "../../services/admin";
import type { ImageRecord, TemplateRecord } from "../../services/admin";
import type { DocPageRecord } from "../../services/admin/adminDocsService";
import { error as logError } from "../../utils/logger";
import { formatFileSize } from "../../utils/numberFormatter";
import { showSuccessToast } from "../../utils/toastNotifications";
import { formatDateTime } from "../../utils/dateFormat";
import { AdminInlineLoading } from "./AdminSectionLoading";
import {
  useAdminImages,
  useAdminImageStats,
} from "../../hooks/swr/useAdminImages";
import {
  useAdminTemplates,
  useAdminTemplateContent,
} from "../../hooks/swr/useAdminTemplates";
import { useAdminDocs, useAdminDocContent } from "../../hooks/swr/useAdminDocs";
import { getApiBaseUrl } from "../../utils/apiClient";
import { useLanguage } from "../LanguageProvider";

/* ─────────────────────── Helpers ─────────────────────── */

function getExtension(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  return ext;
}

type ViewMode = "grid" | "list";
type SortField = "date" | "name" | "size";
type GalleryTab = "images" | "templates" | "docs";

export type GalleryImagesActions = {
  refresh: () => void;
  openUpload: () => void;
  uploading: boolean;
  loading: boolean;
};

export type GalleryTemplatesActions = {
  openNewTemplate: () => void;
  refresh: () => void;
  loading: boolean;
};

export type GalleryDocsActions = {
  openNewDoc: () => void;
  refresh: () => void;
  loading: boolean;
};

/** Construit l'URL complète d'une image via le gateway.
 *  Le backend renvoie `/images/uploads/xxx`, le gateway les sert sous `/admin/images/uploads/xxx`. */
function getImageFullUrl(relativeUrl: string): string {
  return `${getApiBaseUrl()}/admin${relativeUrl}`;
}

/* ─────────────────────── Composant ─────────────────────── */

export default function ImageGallery() {
  const { t } = useLanguage();
  const [galleryTab, setGalleryTab] = useState<GalleryTab>("images");
  const [galleryActions, setGalleryActions] =
    useState<GalleryImagesActions | null>(null);
  const [templateActions, setTemplateActions] =
    useState<GalleryTemplatesActions | null>(null);
  const [docsActions, setDocsActions] = useState<GalleryDocsActions | null>(
    null,
  );

  return (
    <div className="space-y-6">
      {/* En-tête : titre, description, onglets Images/Templates, Refresh + Upload (Images) ou Refresh + New template (Templates) */}
      <Card disableHover>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-[var(--text)]">
                {t("admin.gallery.title")}
              </h2>
              <p className="text-[var(--muted)] mt-1">
                {t("admin.gallery.description")}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 sm:gap-3">
              <div className="flex h-9 items-stretch gap-0.5 rounded-lg border border-[var(--border)] p-0.5 bg-[var(--color-surface-subtle)]">
                <button
                  onClick={() => setGalleryTab("images")}
                  className={`h-full min-h-0 flex items-center gap-2 px-4 rounded-md text-sm font-medium transition-all ${
                    galleryTab === "images"
                      ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                      : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
                  }`}
                >
                  <ImageIcon className="w-4 h-4 shrink-0" />
                  {t("admin.gallery.tabImages")}
                </button>
                <button
                  onClick={() => setGalleryTab("templates")}
                  className={`h-full min-h-0 flex items-center gap-2 px-4 rounded-md text-sm font-medium transition-all ${
                    galleryTab === "templates"
                      ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                      : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
                  }`}
                >
                  <FileCode2 className="w-4 h-4 shrink-0" />
                  {t("admin.gallery.tabTemplates")}
                </button>
                <button
                  onClick={() => setGalleryTab("docs")}
                  className={`h-full min-h-0 flex items-center gap-2 px-4 rounded-md text-sm font-medium transition-all ${
                    galleryTab === "docs"
                      ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                      : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
                  }`}
                >
                  <FileText className="w-4 h-4 shrink-0" />
                  {t("admin.gallery.tabDocs")}
                </button>
              </div>
              {galleryTab === "images" && galleryActions && (
                <>
                  <button
                    onClick={galleryActions.refresh}
                    className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg border border-[var(--border)] text-sm hover:bg-[var(--color-surface-input)] transition-colors"
                  >
                    <RefreshCw
                      className={`w-4 h-4 ${galleryActions.loading ? "animate-spin" : ""}`}
                    />
                    {t("admin.common.refresh")}
                  </button>
                  <button
                    onClick={galleryActions.openUpload}
                    disabled={galleryActions.uploading}
                    className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg bg-[rgb(var(--primary))] text-white text-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
                  >
                    <Upload className="w-4 h-4" />
                    {galleryActions.uploading
                      ? t("admin.gallery.uploading")
                      : t("admin.gallery.upload")}
                  </button>
                </>
              )}
              {galleryTab === "templates" && templateActions && (
                <>
                  <button
                    onClick={templateActions.refresh}
                    className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg border border-[var(--border)] text-sm hover:bg-[var(--color-surface-input)] transition-colors"
                  >
                    <RefreshCw
                      className={`w-4 h-4 ${templateActions.loading ? "animate-spin" : ""}`}
                    />
                    {t("admin.common.refresh")}
                  </button>
                  <button
                    onClick={templateActions.openNewTemplate}
                    className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg bg-[rgb(var(--primary))] text-white text-sm hover:opacity-90 transition-opacity"
                  >
                    <Plus className="w-4 h-4" />
                    {t("admin.gallery.newTemplate")}
                  </button>
                </>
              )}
              {galleryTab === "docs" && docsActions && (
                <>
                  <button
                    onClick={docsActions.refresh}
                    className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg border border-[var(--border)] text-sm hover:bg-[var(--color-surface-input)] transition-colors"
                  >
                    <RefreshCw
                      className={`w-4 h-4 ${docsActions.loading ? "animate-spin" : ""}`}
                    />
                    {t("admin.common.refresh")}
                  </button>
                  <button
                    onClick={docsActions.openNewDoc}
                    className="flex h-9 items-center gap-2 px-4 py-2 rounded-lg bg-[rgb(var(--primary))] text-white text-sm hover:opacity-90 transition-opacity"
                  >
                    <Plus className="w-4 h-4" />
                    {t("admin.gallery.newDoc")}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </Card>

      {galleryTab === "images" ? (
        <ImagesSection onRegisterActions={setGalleryActions} />
      ) : galleryTab === "templates" ? (
        <TemplatesSection onRegisterActions={setTemplateActions} />
      ) : (
        <DocsSection onRegisterActions={setDocsActions} />
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   Section Images (code existant refactoré)
   ═══════════════════════════════════════════════════════════ */

function ImagesSection({
  onRegisterActions,
}: {
  onRegisterActions: (actions: GalleryImagesActions) => void;
}) {
  const { t } = useLanguage();
  const [uploading, setUploading] = useState(false);

  /* ── UI state ── */
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [sortField, setSortField] = useState<SortField>("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ImageRecord | null>(null);
  const [previewImage, setPreviewImage] = useState<ImageRecord | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  /* ── SWR : images et stats ── */
  const {
    images,
    isLoading: galleryLoading,
    mutate: mutateImages,
  } = useAdminImages(sortField, sortOrder);
  const { data: stats, mutate: mutateStats } = useAdminImageStats();
  const loading = galleryLoading;

  const loadData = useCallback(() => {
    mutateImages();
    mutateStats();
  }, [mutateImages, mutateStats]);

  useEffect(() => {
    onRegisterActions({
      refresh: loadData,
      openUpload: () => fileInputRef.current?.click(),
      uploading,
      loading,
    });
  }, [onRegisterActions, loadData, uploading, loading]);

  /* ── upload ── */
  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        await adminService.uploadImage(file);
      }
      showSuccessToast(
        files.length === 1
          ? t("admin.gallery.uploadSuccess1")
          : t("admin.gallery.uploadSuccessN", { count: files.length }),
      );
      loadData();
    } catch (err) {
      logError("[ImageGallery] Erreur upload:", err);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  /* ── suppression ── */
  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await adminService.deleteImage(deleteTarget.filename);
      showSuccessToast(
        t("admin.gallery.imageDeleted", { filename: deleteTarget.filename }),
      );
      setDeleteTarget(null);
      loadData();
    } catch (err) {
      logError("[ImageGallery] Erreur suppression:", err);
    }
  };

  /* ── copier URL ── */
  const handleCopyUrl = (image: ImageRecord) => {
    const fullUrl = getImageFullUrl(image.url);
    navigator.clipboard.writeText(fullUrl).then(() => {
      setCopiedUrl(image.filename);
      showSuccessToast(t("admin.gallery.urlCopied"));
      setTimeout(() => setCopiedUrl(null), 2000);
    });
  };

  /* ── tri ── */
  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder((o) => (o === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };

  /* ── filtrage ── */
  const filteredImages = searchQuery
    ? images.filter((img) =>
        img.filename.toLowerCase().includes(searchQuery.toLowerCase()),
      )
    : images;

  /* ── drag & drop ── */
  const [dragOver, setDragOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleUpload(e.dataTransfer.files);
  };

  /* ─────────────────────── Rendu ─────────────────────── */

  return (
    <div className="space-y-6">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/gif,image/webp"
        multiple
        className="hidden"
        onChange={(e) => handleUpload(e.target.files)}
      />

      {/* KPI */}
      {stats && (
        <KpiGrid
          columns={4}
          items={[
            {
              label: t("admin.gallery.images"),
              value: stats.total.toLocaleString(t("locale")),
              icon: (
                <ImageIcon className="w-4 h-4 text-[rgb(var(--primary))]" />
              ),
              bgColor: "rgba(var(--primary),0.15)",
            },
            {
              label: t("admin.gallery.diskSpace"),
              value: formatFileSize(stats.total_size),
              icon: <HardDrive className="w-4 h-4 text-[rgb(96,165,250)]" />,
              bgColor: "rgba(96,165,250,0.15)",
            },
            {
              label: t("admin.gallery.formats"),
              value: Object.keys(stats.by_extension).length,
              icon: <FileImage className="w-4 h-4 text-[rgb(52,211,153)]" />,
              bgColor: "rgba(52,211,153,0.15)",
            },
            {
              label: t("admin.gallery.avgSize"),
              value:
                stats.total > 0
                  ? formatFileSize(Math.round(stats.total_size / stats.total))
                  : "—",
              icon: (
                <HardDrive className="w-4 h-4 text-[rgb(var(--warning))]" />
              ),
              bgColor: "rgba(var(--warning),0.15)",
            },
          ]}
        />
      )}

      {/* Barre d'outils */}
      <SearchToolbar
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder={t("admin.gallery.searchPlaceholder")}
        sortOptions={[
          { value: "date", label: t("admin.gallery.sortDate") },
          { value: "name", label: t("admin.gallery.sortName") },
          { value: "size", label: t("admin.gallery.sortSize") },
        ]}
        sortValue={sortField}
        onSortChange={(v) => toggleSort(v as SortField)}
        sortOrder={sortOrder}
        onSortOrderToggle={() =>
          setSortOrder((o) => (o === "asc" ? "desc" : "asc"))
        }
        viewMode={viewMode}
        onViewModeChange={setViewMode}
      />

      {/* Zone de drop + contenu */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`rounded-xl border-2 border-dashed transition-colors ${
          dragOver
            ? "border-[rgb(var(--primary))] bg-[rgba(var(--primary),0.05)]"
            : "border-transparent"
        }`}
      >
        {loading && images.length === 0 ? (
          <AdminInlineLoading message={t("admin.gallery.loadingGallery")} />
        ) : filteredImages.length === 0 ? (
          <Card disableHover>
            <div className="py-16 text-center">
              <ImageIcon className="w-12 h-12 text-[var(--muted)] mx-auto mb-4 opacity-40" />
              <p className="text-[var(--muted)] mb-2">
                {searchQuery
                  ? t("admin.gallery.noSearchResults")
                  : t("admin.gallery.noImages")}
              </p>
              {!searchQuery && (
                <p className="text-xs text-[var(--muted)]">
                  {t("admin.gallery.dragDrop")}
                </p>
              )}
            </div>
          </Card>
        ) : viewMode === "grid" ? (
          /* ═══════════ Vue Grille ═══════════ */
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {filteredImages.map((image) => (
              <Card key={image.filename} disableHover>
                <div className="group relative">
                  {/* Aperçu image */}
                  <div
                    className="relative aspect-square rounded-lg overflow-hidden bg-[var(--color-surface-subtle)] mb-3 cursor-pointer"
                    onClick={() => setPreviewImage(image)}
                  >
                    <Image
                      src={getImageFullUrl(image.thumbnail_url || image.url)}
                      alt={image.filename}
                      fill
                      sizes="(max-width: 640px) 50vw, (max-width: 768px) 33vw, (max-width: 1024px) 25vw, (max-width: 1280px) 20vw, 16vw"
                      className="object-cover transition-transform group-hover:scale-105"
                      unoptimized
                    />
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                      <ZoomIn className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </div>

                  {/* Infos */}
                  <p
                    className="text-xs font-medium text-[var(--text)] truncate mb-1"
                    title={image.filename}
                  >
                    {image.filename}
                  </p>
                  <p className="text-xs text-[var(--muted)]">
                    {formatFileSize(image.size)}
                    <span className="mx-1">·</span>
                    <span className="uppercase">
                      {getExtension(image.filename)}
                    </span>
                  </p>

                  {/* Actions */}
                  <div className="flex gap-1 mt-2">
                    <button
                      onClick={() => handleCopyUrl(image)}
                      className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded-lg text-xs border border-[var(--border)] hover:bg-[var(--color-surface-input)] transition-colors"
                      title={t("admin.gallery.copyUrl")}
                    >
                      {copiedUrl === image.filename ? (
                        <Check className="w-3 h-3 text-[rgb(var(--success))]" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </button>
                    <button
                      onClick={() => setDeleteTarget(image)}
                      className="flex items-center justify-center px-2 py-1.5 rounded-lg text-xs text-[rgb(var(--danger))] border border-[rgba(var(--danger),0.2)] hover:bg-[rgba(var(--danger),0.1)] transition-colors"
                      title={t("admin.common.delete")}
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          /* ═══════════ Vue Liste ═══════════ */
          <Card disableHover style={{ overflow: "visible" }}>
            <div className="divide-y divide-[var(--border)]">
              {filteredImages.map((image) => (
                <div
                  key={image.filename}
                  className="flex items-center gap-4 py-3 px-2 hover:bg-[var(--color-surface-subtle)] transition-colors rounded-lg"
                >
                  {/* Miniature */}
                  <div
                    className="relative w-12 h-12 rounded-lg overflow-hidden bg-[var(--color-surface-subtle)] flex-shrink-0 cursor-pointer"
                    onClick={() => setPreviewImage(image)}
                  >
                    <Image
                      src={getImageFullUrl(image.thumbnail_url || image.url)}
                      alt={image.filename}
                      fill
                      sizes="48px"
                      className="object-cover"
                      unoptimized
                    />
                  </div>

                  {/* Nom */}
                  <div className="flex-1 min-w-0">
                    <p
                      className="text-sm font-medium text-[var(--text)] truncate"
                      title={image.filename}
                    >
                      {image.filename}
                    </p>
                    <p className="text-xs text-[var(--muted)]">
                      {formatDateTime(image.created_at)}
                    </p>
                  </div>

                  {/* Taille */}
                  <span className="text-xs text-[var(--muted)] flex-shrink-0">
                    {formatFileSize(image.size)}
                  </span>

                  {/* Extension */}
                  <span className="text-xs text-[var(--muted)] uppercase flex-shrink-0 w-10 text-center">
                    {getExtension(image.filename)}
                  </span>

                  {/* Actions */}
                  <div className="flex gap-1 flex-shrink-0">
                    <button
                      onClick={() => handleCopyUrl(image)}
                      className="p-2 rounded-lg border border-[var(--border)] hover:bg-[var(--color-surface-input)] transition-colors"
                      title={t("admin.gallery.copyUrl")}
                    >
                      {copiedUrl === image.filename ? (
                        <Check className="w-3.5 h-3.5 text-[rgb(var(--success))]" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                    <button
                      onClick={() => setDeleteTarget(image)}
                      className="p-2 rounded-lg text-[rgb(var(--danger))] border border-[rgba(var(--danger),0.2)] hover:bg-[rgba(var(--danger),0.1)] transition-colors"
                      title={t("admin.common.delete")}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Nombre de résultats */}
      {filteredImages.length > 0 && (
        <p className="text-xs text-[var(--muted)] text-center">
          {filteredImages.length > 1
            ? t("admin.gallery.imageCountPlural", {
                count: filteredImages.length,
              })
            : t("admin.gallery.imageCount", { count: filteredImages.length })}
          {searchQuery &&
            ` (${t("admin.gallery.ofTotal", { total: images.length })})`}
        </p>
      )}

      {/* Modal aperçu image */}
      {previewImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
          onClick={() => setPreviewImage(null)}
        >
          <div
            className="relative max-w-[90vw] max-h-[90vh] rounded-xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setPreviewImage(null)}
              className="absolute top-3 right-3 z-10 p-2 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={getImageFullUrl(previewImage.url)}
              alt={previewImage.filename}
              className="max-w-[90vw] max-h-[85vh] object-contain"
              decoding="async"
            />

            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4">
              <p className="text-white text-sm font-medium truncate">
                {previewImage.filename}
              </p>
              <p className="text-white/70 text-xs">
                {formatFileSize(previewImage.size)}
                <span className="mx-2">·</span>
                {formatDateTime(previewImage.created_at)}
              </p>
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => handleCopyUrl(previewImage)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/20 text-white text-xs hover:bg-white/30 transition-colors"
                >
                  {copiedUrl === previewImage.filename ? (
                    <Check className="w-3.5 h-3.5" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                  {t("admin.gallery.copyUrl")}
                </button>
                <button
                  onClick={() => {
                    setPreviewImage(null);
                    setDeleteTarget(previewImage);
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[rgba(var(--danger),0.3)] text-[rgba(var(--danger),0.8)] text-xs hover:bg-[rgba(var(--danger),0.5)] transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  {t("admin.common.delete")}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal confirmation suppression */}
      <ConfirmModal
        isOpen={!!deleteTarget}
        title={t("admin.gallery.deleteImage")}
        message={t("admin.gallery.deleteImageConfirm", {
          filename: deleteTarget?.filename ?? "",
        })}
        confirmText={t("admin.common.delete")}
        variant="danger"
        onConfirm={handleDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   Section Templates d'emails
   ═══════════════════════════════════════════════════════════ */

function TemplatesSection({
  onRegisterActions,
}: {
  onRegisterActions: (actions: GalleryTemplatesActions) => void;
}) {
  const { t } = useLanguage();
  const [editingTemplate, setEditingTemplate] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState("");
  const [creating, setCreating] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<TemplateRecord | null>(null);

  /* ── SWR : liste des templates et contenu en édition ── */
  const {
    templates,
    isLoading: templatesLoading,
    mutate: mutateTemplates,
  } = useAdminTemplates();
  const { mutate: mutateContent } = useAdminTemplateContent(
    editingTemplate ?? null,
  );

  useEffect(() => {
    onRegisterActions({
      openNewTemplate: () => setShowCreateForm(true),
      refresh: () => mutateTemplates(),
      loading: templatesLoading,
    });
  }, [onRegisterActions, mutateTemplates, templatesLoading]);

  /* ── Ouvrir l'éditeur ── */
  const handleEdit = async (filename: string) => {
    setEditingTemplate(filename);
    setPreviewMode(false);
    try {
      const data = await adminService.getTemplateContent(filename);
      setEditContent(data.content);
    } catch (err) {
      logError("[TemplatesSection] Erreur chargement template:", err);
    }
  };

  /* ── Sauvegarder ── */
  const handleSave = async () => {
    if (!editingTemplate) return;
    setSaving(true);
    try {
      await adminService.updateTemplate(editingTemplate, editContent);
      showSuccessToast(
        t("admin.gallery.templateUpdated", { filename: editingTemplate }),
      );
      mutateTemplates();
      mutateContent();
    } catch (err) {
      logError("[TemplatesSection] Erreur sauvegarde template:", err);
    } finally {
      setSaving(false);
    }
  };

  /* ── Fermer l'éditeur ── */
  const handleCloseEditor = () => {
    setEditingTemplate(null);
    setEditContent("");
    setPreviewMode(false);
  };

  /* ── Créer un template ── */
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTemplateName.trim()) return;
    setCreating(true);
    try {
      await adminService.createTemplate(newTemplateName.trim());
      showSuccessToast(
        t("admin.gallery.templateCreated", {
          filename: newTemplateName.trim(),
        }),
      );
      setNewTemplateName("");
      setShowCreateForm(false);
      mutateTemplates();
    } catch (err) {
      logError("[TemplatesSection] Erreur création template:", err);
    } finally {
      setCreating(false);
    }
  };

  /* ── Supprimer un template ── */
  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await adminService.deleteTemplate(deleteTarget.filename);
      showSuccessToast(
        t("admin.gallery.templateDeleted", { filename: deleteTarget.filename }),
      );
      setDeleteTarget(null);
      mutateTemplates();
    } catch (err) {
      logError("[TemplatesSection] Erreur suppression template:", err);
    }
  };

  /* ─────────────────────── Rendu ─────────────────────── */

  // Mode éditeur
  if (editingTemplate) {
    return (
      <div className="space-y-4">
        {/* Barre d'outils éditeur */}
        <Card disableHover>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileCode2 className="w-5 h-5 text-[rgb(var(--primary))]" />
              <div>
                <h3 className="text-sm font-semibold text-[var(--text)]">
                  {editingTemplate}
                </h3>
                <p className="text-xs text-[var(--muted)]">
                  {t("admin.gallery.editTemplate")}
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPreviewMode(!previewMode)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                  previewMode
                    ? "border-[rgb(var(--primary))] text-[rgb(var(--primary))] bg-[rgba(var(--primary),0.1)]"
                    : "border-[var(--border)] text-[var(--muted)] hover:bg-[var(--color-surface-input)]"
                }`}
              >
                {previewMode ? (
                  <Code className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
                {previewMode
                  ? t("admin.gallery.editor")
                  : t("admin.gallery.preview")}
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-[rgb(var(--primary))] text-white text-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                <Save className="w-4 h-4" />
                {t("admin.gallery.save")}
              </button>
              <button
                onClick={handleCloseEditor}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[var(--border)] text-sm text-[var(--muted)] hover:bg-[var(--color-surface-input)] transition-colors"
              >
                <X className="w-4 h-4" />
                {t("admin.gallery.cancel")}
              </button>
            </div>
          </div>
        </Card>

        {/* Zone d'édition / aperçu */}
        <Card disableHover>
          {previewMode ? (
            <div className="rounded-lg border border-[var(--border)] bg-white p-4 min-h-[500px]">
              <iframe
                srcDoc={editContent}
                className="w-full min-h-[500px] border-0"
                title={t("admin.gallery.templatePreview")}
                sandbox=""
              />
            </div>
          ) : (
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="w-full min-h-[500px] p-4 rounded-lg border border-[var(--border)] bg-[var(--color-surface-subtle)] text-[var(--text)] font-mono text-sm resize-y focus:outline-none focus:ring-2 focus:ring-[rgb(var(--primary))] focus:border-transparent"
              spellCheck={false}
            />
          )}
        </Card>
      </div>
    );
  }

  // Liste des templates (Refresh et New template sont dans la carte Gallery)
  return (
    <div className="space-y-4">
      {/* Formulaire de création */}
      {showCreateForm && (
        <Card disableHover>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-[var(--text)] flex items-center gap-2">
                <Plus className="w-4 h-4" />
                {t("admin.gallery.createTemplate")}
              </h3>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="text-[var(--muted)] hover:text-[var(--text)] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text)] mb-2">
                {t("admin.gallery.templateName")}
              </label>
              <input
                type="text"
                value={newTemplateName}
                onChange={(e) => setNewTemplateName(e.target.value)}
                required
                className="auth-input"
                placeholder={t("admin.gallery.templateNamePlaceholder")}
              />
              <p className="text-xs text-[var(--muted)] mt-1">
                {t("admin.gallery.templateNameHint")}
              </p>
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 rounded-lg border border-[var(--border)] text-sm text-[var(--muted)] hover:bg-[var(--color-surface-input)] transition-colors"
              >
                {t("admin.gallery.cancel")}
              </button>
              <button
                type="submit"
                disabled={creating || !newTemplateName.trim()}
                className="px-4 py-2 rounded-lg bg-[rgb(var(--primary))] text-white text-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                {creating
                  ? t("admin.gallery.creating")
                  : t("admin.common.create")}
              </button>
            </div>
          </form>
        </Card>
      )}

      {templatesLoading ? (
        <AdminInlineLoading message={t("admin.gallery.loadingTemplates")} />
      ) : templates.length === 0 ? (
        <Card disableHover>
          <div className="py-16 text-center">
            <FileCode2 className="w-12 h-12 text-[var(--muted)] mx-auto mb-4 opacity-40" />
            <p className="text-[var(--muted)]">
              {t("admin.gallery.noTemplates")}
            </p>
          </div>
        </Card>
      ) : (
        <Card disableHover style={{ overflow: "visible" }}>
          <div className="divide-y divide-[var(--border)]">
            {templates.map((tpl: TemplateRecord) => (
              <div
                key={tpl.filename}
                className="flex items-center gap-4 py-4 px-2 hover:bg-[var(--color-surface-subtle)] transition-colors rounded-lg"
              >
                {/* Icône */}
                <div className="w-10 h-10 rounded-lg bg-[rgba(var(--primary),0.1)] flex items-center justify-center flex-shrink-0">
                  <FileCode2 className="w-5 h-5 text-[rgb(var(--primary))]" />
                </div>

                {/* Nom et infos */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--text)]">
                    {tpl.filename}
                  </p>
                  <p className="text-xs text-[var(--muted)]">
                    {formatFileSize(tpl.size)}
                    <span className="mx-2">·</span>
                    {t("admin.gallery.templateLastModified")}:{" "}
                    {formatDateTime(tpl.updated_at)}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(tpl.filename)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[var(--border)] text-sm text-[var(--text)] hover:bg-[var(--color-surface-input)] transition-colors"
                  >
                    <Code className="w-4 h-4" />
                    {t("admin.gallery.editTemplate")}
                  </button>
                  <button
                    onClick={() => setDeleteTarget(tpl)}
                    className="flex items-center justify-center px-2 py-1.5 rounded-lg text-xs text-[rgb(var(--danger))] border border-[rgba(var(--danger),0.2)] hover:bg-[rgba(var(--danger),0.1)] transition-colors"
                    title={t("admin.common.delete")}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Modal confirmation suppression */}
      <ConfirmModal
        isOpen={!!deleteTarget}
        title={t("admin.gallery.deleteTemplate")}
        message={t("admin.gallery.deleteTemplateConfirm", {
          filename: deleteTarget?.filename ?? "",
        })}
        confirmText={t("admin.common.delete")}
        variant="danger"
        onConfirm={handleDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   Section Documentation (Scanner)
   ═══════════════════════════════════════════════════════════ */

function DocsSection({
  onRegisterActions,
}: {
  onRegisterActions: (actions: GalleryDocsActions) => void;
}) {
  const { t } = useLanguage();
  const [editingSlug, setEditingSlug] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newDocSlug, setNewDocSlug] = useState("");
  const [newDocTitle, setNewDocTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<DocPageRecord | null>(null);

  const { docs, isLoading: docsLoading, mutate: mutateDocs } = useAdminDocs();
  const { mutate: mutateContent } = useAdminDocContent(editingSlug ?? null);

  useEffect(() => {
    onRegisterActions({
      openNewDoc: () => setShowCreateForm(true),
      refresh: () => mutateDocs(),
      loading: docsLoading,
    });
  }, [onRegisterActions, mutateDocs, docsLoading]);

  const handleEdit = async (slug: string) => {
    setEditingSlug(slug);
    setPreviewMode(false);
    try {
      const data = await adminService.getDocContent(slug);
      setEditContent(data.content);
    } catch (err) {
      logError("[DocsSection] Erreur chargement doc:", err);
    }
  };

  const handleSave = async () => {
    if (!editingSlug) return;
    setSaving(true);
    try {
      await adminService.updateDoc(editingSlug, editContent);
      showSuccessToast(t("admin.gallery.docUpdated", { slug: editingSlug }));
      mutateDocs();
      mutateContent();
    } catch (err) {
      logError("[DocsSection] Erreur sauvegarde doc:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleCloseEditor = () => {
    setEditingSlug(null);
    setEditContent("");
    setPreviewMode(false);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDocSlug.trim()) return;
    setCreating(true);
    try {
      await adminService.createDoc(
        newDocSlug.trim().toLowerCase(),
        newDocTitle.trim() || newDocSlug.trim(),
      );
      showSuccessToast(
        t("admin.gallery.docCreated", { slug: newDocSlug.trim() }),
      );
      setNewDocSlug("");
      setNewDocTitle("");
      setShowCreateForm(false);
      mutateDocs();
    } catch (err) {
      logError("[DocsSection] Erreur création doc:", err);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await adminService.deleteDoc(deleteTarget.slug);
      showSuccessToast(
        t("admin.gallery.docDeleted", { slug: deleteTarget.slug }),
      );
      setDeleteTarget(null);
      mutateDocs();
    } catch (err) {
      logError("[DocsSection] Erreur suppression doc:", err);
    }
  };

  if (editingSlug) {
    return (
      <div className="space-y-4">
        <Card disableHover>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-5 h-5 text-[rgb(var(--primary))]" />
              <div>
                <h3 className="text-sm font-semibold text-[var(--text)]">
                  {editingSlug}
                </h3>
                <p className="text-xs text-[var(--muted)]">
                  {t("admin.gallery.editDoc")}
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPreviewMode(!previewMode)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                  previewMode
                    ? "border-[rgb(var(--primary))] text-[rgb(var(--primary))] bg-[rgba(var(--primary),0.1)]"
                    : "border-[var(--border)] text-[var(--muted)] hover:bg-[var(--color-surface-input)]"
                }`}
              >
                {previewMode ? (
                  <Code className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
                {previewMode
                  ? t("admin.gallery.editor")
                  : t("admin.gallery.preview")}
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-[rgb(var(--primary))] text-white text-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                <Save className="w-4 h-4" />
                {t("admin.gallery.save")}
              </button>
              <button
                onClick={handleCloseEditor}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[var(--border)] text-sm text-[var(--muted)] hover:bg-[var(--color-surface-input)] transition-colors"
              >
                <X className="w-4 h-4" />
                {t("admin.gallery.cancel")}
              </button>
            </div>
          </div>
        </Card>

        <Card disableHover>
          {previewMode ? (
            <div
              className="prose prose-invert max-w-none min-h-[500px] p-4 rounded-lg border border-[var(--border)] [&_a]:text-[rgb(var(--primary))] [&_a]:underline"
              dangerouslySetInnerHTML={{ __html: editContent }}
            />
          ) : (
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              className="w-full min-h-[500px] p-4 rounded-lg border border-[var(--border)] bg-[var(--color-surface-subtle)] text-[var(--text)] font-mono text-sm resize-y focus:outline-none focus:ring-2 focus:ring-[rgb(var(--primary))] focus:border-transparent"
              spellCheck={false}
            />
          )}
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {showCreateForm && (
        <Card disableHover>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-[var(--text)] flex items-center gap-2">
                <Plus className="w-4 h-4" />
                {t("admin.gallery.createDoc")}
              </h3>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="text-[var(--muted)] hover:text-[var(--text)] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text)] mb-2">
                {t("admin.gallery.docSlug")}
              </label>
              <input
                type="text"
                value={newDocSlug}
                onChange={(e) =>
                  setNewDocSlug(
                    e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, ""),
                  )
                }
                required
                className="auth-input"
                placeholder="ex: scan-frontend"
              />
              <p className="text-xs text-[var(--muted)] mt-1">
                {t("admin.gallery.docSlugHint")}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text)] mb-2">
                {t("admin.gallery.docTitle")}
              </label>
              <input
                type="text"
                value={newDocTitle}
                onChange={(e) => setNewDocTitle(e.target.value)}
                className="auth-input"
                placeholder={t("admin.gallery.docTitlePlaceholder")}
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 rounded-lg border border-[var(--border)] text-sm text-[var(--muted)] hover:bg-[var(--color-surface-input)] transition-colors"
              >
                {t("admin.gallery.cancel")}
              </button>
              <button
                type="submit"
                disabled={creating || !newDocSlug.trim()}
                className="px-4 py-2 rounded-lg bg-[rgb(var(--primary))] text-white text-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                {creating
                  ? t("admin.gallery.creating")
                  : t("admin.common.create")}
              </button>
            </div>
          </form>
        </Card>
      )}

      {docsLoading ? (
        <AdminInlineLoading message={t("admin.gallery.loadingDocs")} />
      ) : docs.length === 0 ? (
        <Card disableHover>
          <div className="py-16 text-center">
            <FileText className="w-12 h-12 text-[var(--muted)] mx-auto mb-4 opacity-40" />
            <p className="text-[var(--muted)]">{t("admin.gallery.noDocs")}</p>
          </div>
        </Card>
      ) : (
        <Card disableHover style={{ overflow: "visible" }}>
          <div className="divide-y divide-[var(--border)]">
            {docs.map((doc: DocPageRecord) => (
              <div
                key={doc.slug}
                className="flex items-center gap-4 py-4 px-2 hover:bg-[var(--color-surface-subtle)] transition-colors rounded-lg"
              >
                <div className="w-10 h-10 rounded-lg bg-[rgba(var(--primary),0.1)] flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-[rgb(var(--primary))]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--text)]">
                    {doc.title}
                  </p>
                  <p className="text-xs text-[var(--muted)]">
                    <code>{doc.slug}</code>
                    <span className="mx-2">·</span>
                    {formatFileSize(doc.size)}
                    <span className="mx-2">·</span>
                    {t("admin.gallery.docLastModified")}:{" "}
                    {formatDateTime(doc.updated_at)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(doc.slug)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-[var(--border)] text-sm text-[var(--text)] hover:bg-[var(--color-surface-input)] transition-colors"
                  >
                    <Code className="w-4 h-4" />
                    {t("admin.gallery.editDoc")}
                  </button>
                  <button
                    onClick={() => setDeleteTarget(doc)}
                    className="flex items-center justify-center px-2 py-1.5 rounded-lg text-xs text-[rgb(var(--danger))] border border-[rgba(var(--danger),0.2)] hover:bg-[rgba(var(--danger),0.1)] transition-colors"
                    title={t("admin.common.delete")}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <ConfirmModal
        isOpen={!!deleteTarget}
        title={t("admin.gallery.deleteDoc")}
        message={t("admin.gallery.deleteDocConfirm", {
          slug: deleteTarget?.slug ?? "",
        })}
        confirmText={t("admin.common.delete")}
        variant="danger"
        onConfirm={handleDelete}
        onClose={() => setDeleteTarget(null)}
      />
    </div>
  );
}
