"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { fetchAuthSession } from "aws-amplify/auth";
import { Upload, ImageIcon, FolderOpen, Check } from "lucide-react";
import { GenericButton } from "../buttons";
import Modal from "../ui/Modal";
import { error } from "../../utils/logger";
import { formatFileSize } from "../../utils/numberFormatter";
import { getApiBaseUrl } from "../../utils/apiClient";
import adminService from "../../services/admin";
import type { ImageRecord } from "../../services/admin";

interface ImageModalProps {
  isOpen: boolean;
  onClose: () => void;
  onInsert: (imageUrl: string, altText: string, caption?: string) => void;
}

/**
 * Modal pour ajouter une image dans le contenu structuré (email / newsletter).
 * Supporte l'upload de fichier et l'insertion par URL.
 */
export default function ImageModal({
  isOpen,
  onClose,
  onInsert,
}: ImageModalProps) {
  type SourceTab = "upload" | "gallery";
  const [sourceTab, setSourceTab] = useState<SourceTab>("upload");

  const [imageUrl, setImageUrl] = useState("");
  const [imageName, setImageName] = useState("");
  const [altText, setAltText] = useState("");
  const [caption, setCaption] = useState("");
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /* ── Gallery state ── */
  const [galleryImages, setGalleryImages] = useState<ImageRecord[]>([]);
  const [galleryLoading, setGalleryLoading] = useState(false);
  const [galleryError, setGalleryError] = useState<string | null>(null);
  const [gallerySearch, setGallerySearch] = useState("");

  const loadGallery = useCallback(async () => {
    setGalleryLoading(true);
    setGalleryError(null);
    try {
      const res = await adminService.getImages({
        sortBy: "date",
        sortOrder: "desc",
      });
      setGalleryImages(res.images ?? []);
    } catch {
      setGalleryError("Impossible de charger la galerie.");
    } finally {
      setGalleryLoading(false);
    }
  }, []);

  // Load gallery when opening that tab
  useEffect(() => {
    if (isOpen && sourceTab === "gallery" && galleryImages.length === 0) {
      loadGallery();
    }
  }, [isOpen, sourceTab, galleryImages.length, loadGallery]);

  useEffect(() => {
    if (!isOpen) {
      setImageUrl("");
      setImageName("");
      setAltText("");
      setCaption("");
      setSelectedImage(null);
      setUploadError(null);
      setSourceTab("upload");
      setGalleryImages([]);
      setGallerySearch("");
    }
  }, [isOpen]);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const allowedTypes = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
      ];
      if (!allowedTypes.includes(file.type)) {
        setUploadError(
          "Type de fichier non autorisé. Formats acceptés : JPG, PNG, GIF, WebP",
        );
        return;
      }

      const maxSize = 5 * 1024 * 1024; // 5MB
      if (file.size > maxSize) {
        setUploadError("Fichier trop volumineux. Taille maximale : 5 Mo");
        return;
      }

      setSelectedImage(file);
      setUploadError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      const event = {
        target: { files: [file] },
      } as unknown as React.ChangeEvent<HTMLInputElement>;
      handleImageSelect(event);
    }
  };

  const handleUpload = async () => {
    if (!selectedImage) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      let token: string | undefined;
      try {
        const session = await fetchAuthSession();
        token = session.tokens?.accessToken?.toString();
      } catch {
        // Continuer sans token si impossible
      }

      const formData = new FormData();
      formData.append("file", selectedImage);
      if (imageName.trim()) {
        formData.append("slug", imageName.trim());
      }

      const headers: HeadersInit = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(
        `${getApiBaseUrl()}/admin/api/upload-image`,
        {
          method: "POST",
          headers,
          body: formData,
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const detail = errorData?.detail;
        if (response.status === 409 && detail) {
          throw new Error(detail);
        }
        throw new Error(
          detail || `Erreur lors de l'upload: ${response.status}`,
        );
      }

      const result = await response.json();
      let uploadedUrl = result.url || result.image_url || "";

      // Transformer l'URL relative en URL absolue via le gateway
      if (uploadedUrl.startsWith("/")) {
        const baseUrl = getApiBaseUrl().replace(/\/$/, "");
        uploadedUrl = `${baseUrl}/admin${uploadedUrl}`;
      }

      setImageUrl(uploadedUrl);
      setSelectedImage(null);
    } catch (err) {
      error("[ImageModal] Erreur upload image:", err);
      setUploadError(
        err instanceof Error
          ? err.message
          : "Erreur lors de l'upload de l'image",
      );
    } finally {
      setIsUploading(false);
    }
  };

  const getImageFullUrl = (relativeUrl: string) => {
    const baseUrl = getApiBaseUrl().replace(/\/$/, "");
    return `${baseUrl}/admin${relativeUrl}`;
  };

  const handleGallerySelect = (img: ImageRecord) => {
    const fullUrl = getImageFullUrl(img.url);
    setImageUrl(fullUrl);
    // Pre-fill alt text with filename (without extension)
    if (!altText.trim()) {
      const nameWithoutExt = img.filename.replace(/\.[^.]+$/, "");
      setAltText(nameWithoutExt);
    }
  };

  const handleInsert = () => {
    const finalImageUrl = imageUrl.trim();
    if (finalImageUrl) {
      onInsert(
        finalImageUrl,
        altText.trim() || "Image",
        caption.trim() || undefined,
      );
      onClose();
    }
  };

  const filteredGallery = gallerySearch.trim()
    ? galleryImages.filter((img) =>
        img.filename.toLowerCase().includes(gallerySearch.toLowerCase()),
      )
    : galleryImages;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Ajouter une image"
      maxWidth="600px"
    >
      <div className="flex flex-col" style={{ maxHeight: "calc(80vh - 6rem)" }}>
        {/* Onglets source : Upload / Galerie (fixe en haut) */}
        <div className="flex items-center gap-1 border border-[var(--border)] rounded-lg p-1 bg-[var(--color-surface-subtle)] shrink-0">
          <button
            type="button"
            onClick={() => setSourceTab("upload")}
            className={`flex items-center gap-2 px-4 py-2 rounded text-sm font-medium transition-all flex-1 justify-center ${
              sourceTab === "upload"
                ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
            }`}
          >
            <Upload className="w-4 h-4" />
            Uploader
          </button>
          <button
            type="button"
            onClick={() => setSourceTab("gallery")}
            className={`flex items-center gap-2 px-4 py-2 rounded text-sm font-medium transition-all flex-1 justify-center ${
              sourceTab === "gallery"
                ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
                : "bg-transparent text-[var(--muted)] hover:text-[var(--text)]"
            }`}
          >
            <FolderOpen className="w-4 h-4" />
            Galerie
          </button>
        </div>

        {/* Contenu scrollable */}
        <div className="overflow-y-auto flex-1 min-h-0 space-y-5 mt-5 pr-1">
          {/* ─── Tab : Upload ─── */}
          {sourceTab === "upload" && (
            <>
              {/* Zone d'upload */}
              <div>
                <label className="block text-sm font-medium text-[var(--text)] mb-2">
                  Image
                </label>
                <div
                  className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors ${
                    selectedImage || imageUrl
                      ? "border-[rgb(var(--primary))] bg-[rgba(var(--primary),0.05)]"
                      : "border-[var(--border)] hover:border-[rgb(var(--primary))]"
                  }`}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                >
                  {selectedImage ? (
                    <div className="space-y-3">
                      <div className="text-[rgb(var(--primary))]">
                        <ImageIcon className="mx-auto h-8 w-8" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-[var(--text)]">
                          {selectedImage.name}
                        </p>
                        <p className="text-xs text-[var(--muted)]">
                          {formatFileSize(selectedImage.size)}
                        </p>
                      </div>
                      <div className="flex gap-2 justify-center">
                        <GenericButton
                          label={
                            isUploading ? "Upload en cours..." : "Uploader"
                          }
                          onClick={handleUpload}
                          disabled={isUploading}
                          variant="primary"
                          size="sm"
                          icon={<Upload className="w-3 h-3" />}
                          iconPosition="left"
                        />
                        <GenericButton
                          label="Annuler"
                          onClick={() => {
                            setSelectedImage(null);
                            if (fileInputRef.current) {
                              fileInputRef.current.value = "";
                            }
                          }}
                          variant="secondary"
                          size="sm"
                        />
                      </div>
                    </div>
                  ) : imageUrl ? (
                    <div className="space-y-2">
                      <img
                        src={imageUrl}
                        alt="Preview"
                        className="mx-auto max-h-32 rounded"
                        loading="lazy"
                        decoding="async"
                      />
                      <button
                        type="button"
                        onClick={() => setImageUrl("")}
                        className="text-xs text-[rgb(var(--danger))] hover:text-[rgba(var(--danger),0.8)] cursor-pointer transition-colors"
                      >
                        Changer l&apos;image
                      </button>
                    </div>
                  ) : (
                    <div>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleImageSelect}
                        className="hidden"
                        id="image-upload-modal"
                      />
                      <label
                        htmlFor="image-upload-modal"
                        className="cursor-pointer flex flex-col items-center"
                      >
                        <ImageIcon className="mx-auto h-8 w-8 text-[var(--muted)]" />
                        <span className="mt-2 text-sm text-[var(--muted)]">
                          Glissez-déposez votre image ici ou cliquez pour
                          sélectionner
                        </span>
                      </label>
                    </div>
                  )}
                </div>
                {uploadError && (
                  <p className="mt-2 text-sm text-[rgb(var(--danger))]">
                    {uploadError}
                  </p>
                )}
              </div>

              {/* Nom de l'image */}
              <div>
                <label className="block text-sm font-medium text-[var(--text)] mb-2">
                  Nom de l&apos;image (optionnel)
                </label>
                <input
                  type="text"
                  value={imageName}
                  onChange={(e) => setImageName(e.target.value)}
                  placeholder="ex: hero-banner, promo-ete-2026"
                  className="auth-input w-full"
                />
                <p className="mt-1 text-xs text-[var(--muted)]">
                  Nom utilisé pour enregistrer le fichier. Si vide, un
                  identifiant unique sera généré.
                </p>
              </div>

              {/* Ou saisie d'URL */}
              <div>
                <label className="block text-sm font-medium text-[var(--text)] mb-2">
                  Ou coller une URL d&apos;image
                </label>
                <input
                  type="url"
                  value={imageUrl}
                  onChange={(e) => setImageUrl(e.target.value)}
                  placeholder="https://example.com/image.jpg"
                  className="auth-input w-full"
                />
              </div>
            </>
          )}

          {/* ─── Tab : Galerie ─── */}
          {sourceTab === "gallery" && (
            <div>
              {/* Recherche */}
              <input
                type="text"
                value={gallerySearch}
                onChange={(e) => setGallerySearch(e.target.value)}
                placeholder="Rechercher une image…"
                className="auth-input w-full mb-3"
              />

              {galleryLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-2 border-[rgb(var(--primary))] border-t-transparent" />
                  <span className="ml-2 text-sm text-[var(--muted)]">
                    Chargement…
                  </span>
                </div>
              ) : galleryError ? (
                <div className="text-center py-8">
                  <p className="text-sm text-[rgb(var(--danger))] mb-2">
                    {galleryError}
                  </p>
                  <GenericButton
                    label="Réessayer"
                    onClick={loadGallery}
                    variant="secondary"
                    size="sm"
                  />
                </div>
              ) : filteredGallery.length === 0 ? (
                <div className="text-center py-8">
                  <ImageIcon className="mx-auto h-8 w-8 text-[var(--muted)] mb-2" />
                  <p className="text-sm text-[var(--muted)]">
                    {gallerySearch.trim()
                      ? "Aucune image ne correspond à la recherche"
                      : "Aucune image dans la galerie"}
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-2">
                  {filteredGallery.map((img) => {
                    const fullUrl = getImageFullUrl(img.url);
                    const thumbUrl = getImageFullUrl(
                      img.thumbnail_url || img.url,
                    );
                    const isSelected = imageUrl === fullUrl;
                    return (
                      <button
                        key={img.filename}
                        type="button"
                        onClick={() => handleGallerySelect(img)}
                        className={`relative group rounded-lg overflow-hidden border-2 transition-all aspect-square ${
                          isSelected
                            ? "border-[rgb(var(--primary))] ring-2 ring-[rgb(var(--primary))] ring-offset-1 ring-offset-[var(--color-surface)]"
                            : "border-[var(--border)] hover:border-[rgb(var(--primary))]"
                        }`}
                      >
                        <img
                          src={thumbUrl}
                          alt={img.filename}
                          className="w-full h-full object-cover"
                          loading="lazy"
                          decoding="async"
                        />
                        {/* Overlay filename */}
                        <div className="absolute inset-x-0 bottom-0 bg-black/60 px-1.5 py-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <p className="text-[10px] text-white truncate">
                            {img.filename}
                          </p>
                        </div>
                        {/* Selected check */}
                        {isSelected && (
                          <div className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-[rgb(var(--primary))] flex items-center justify-center">
                            <Check className="w-3 h-3 text-white" />
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Preview of selected gallery image */}
              {imageUrl && (
                <div className="mt-3 p-2 rounded-lg border border-[rgb(var(--primary))] bg-[rgba(var(--primary),0.05)] flex items-center gap-3">
                  <img
                    src={imageUrl}
                    alt="Sélection"
                    className="w-12 h-12 rounded object-cover shrink-0"
                    loading="lazy"
                    decoding="async"
                  />
                  <p className="text-sm text-[var(--text)] truncate flex-1">
                    Image sélectionnée
                  </p>
                  <button
                    type="button"
                    onClick={() => setImageUrl("")}
                    className="text-xs text-[rgb(var(--danger))] hover:text-[rgba(var(--danger),0.8)] transition-colors shrink-0"
                  >
                    Retirer
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Texte alternatif */}
          <div>
            <label className="block text-sm font-medium text-[var(--text)] mb-2">
              Texte alternatif (alt) *
            </label>
            <input
              type="text"
              value={altText}
              onChange={(e) => setAltText(e.target.value)}
              placeholder="Description de l'image"
              className="auth-input w-full"
            />
          </div>

          {/* Légende */}
          <div>
            <label className="block text-sm font-medium text-[var(--text)] mb-2">
              Légende (optionnel)
            </label>
            <input
              type="text"
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder="Légende qui apparaîtra sous l'image"
              className="auth-input w-full"
            />
          </div>
        </div>

        {/* Actions (fixe en bas) */}
        <div className="flex justify-end gap-3 pt-4 mt-4 border-t border-[var(--border)] shrink-0">
          <GenericButton
            label="Annuler"
            onClick={onClose}
            variant="secondary"
          />
          <GenericButton
            label="Ajouter"
            onClick={handleInsert}
            disabled={!imageUrl.trim()}
            variant="primary"
            icon={<ImageIcon className="w-4 h-4" />}
            iconPosition="left"
          />
        </div>
      </div>
    </Modal>
  );
}
