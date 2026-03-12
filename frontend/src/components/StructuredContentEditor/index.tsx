"use client";

/**
 * Éditeur de contenu structuré avec éditeur WYSIWYG Tiptap + mode HTML brut.
 * Toggle entre les deux modes avec synchronisation automatique du contenu.
 */

import { useState, useCallback, useEffect, useRef } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import ResizableImage from "./ResizableImage";
import Link from "@tiptap/extension-link";
import Underline from "@tiptap/extension-underline";
import TextAlign from "@tiptap/extension-text-align";
import { TextStyle } from "@tiptap/extension-text-style";
import Color from "@tiptap/extension-color";
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  Heading1,
  Heading2,
  Heading3,
  List,
  ListOrdered,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Link as LinkIcon,
  Unlink,
  ImageIcon,
  Undo2,
  Redo2,
  Code,
  Minus,
  Palette,
} from "lucide-react";
import ImageModal from "./ImageModal";
import type { StructuredContentEditorProps } from "./types";
import { useLanguage } from "../LanguageProvider";

/* ────────────────────────── Toolbar button ────────────────────────── */

function ToolbarBtn({
  onClick,
  active = false,
  disabled = false,
  title,
  children,
}: {
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`p-1.5 rounded transition-colors ${
        active
          ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))]"
          : "text-[var(--text)] hover:bg-[var(--color-surface-hover)]"
      } disabled:opacity-30 disabled:cursor-not-allowed`}
    >
      {children}
    </button>
  );
}

/* ────────────────────────── Toolbar ────────────────────────── */

const PRESET_COLORS = [
  "#000000",
  "#434343",
  "#666666",
  "#999999",
  "#cccccc",
  "#ffffff",
  "#e60000",
  "#ff9900",
  "#ffff00",
  "#00cc00",
  "#0066cc",
  "#9933ff",
  "#ff4d4d",
  "#ffb84d",
  "#ffff80",
  "#66e066",
  "#4d9fe6",
  "#c285ff",
  "#cc0000",
  "#cc7a00",
  "#cccc00",
  "#009900",
  "#004d99",
  "#7a29cc",
  "#800000",
  "#804d00",
  "#808000",
  "#006600",
  "#003366",
  "#4d1a80",
];

function EditorToolbar({
  editor,
  onInsertImage,
}: {
  editor: ReturnType<typeof useEditor> | null;
  onInsertImage: () => void;
}) {
  const { t } = useLanguage();
  const [showColorPicker, setShowColorPicker] = useState(false);
  const colorPickerRef = useRef<HTMLDivElement>(null);
  const colorInputRef = useRef<HTMLInputElement>(null);

  const [showLinkBubble, setShowLinkBubble] = useState(false);
  const [linkUrl, setLinkUrl] = useState("");
  const [linkText, setLinkText] = useState("");
  const [linkHasSelection, setLinkHasSelection] = useState(false);
  const [linkSelectionFrom, setLinkSelectionFrom] = useState(0);
  const linkBubbleRef = useRef<HTMLDivElement>(null);
  const linkUrlInputRef = useRef<HTMLInputElement>(null);

  // Close the color picker when clicking outside
  useEffect(() => {
    if (!showColorPicker) return;
    const handleClick = (e: MouseEvent) => {
      if (
        colorPickerRef.current &&
        !colorPickerRef.current.contains(e.target as Node)
      ) {
        setShowColorPicker(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [showColorPicker]);

  // Close the link bubble when clicking outside
  useEffect(() => {
    if (!showLinkBubble) return;
    const handleClick = (e: MouseEvent) => {
      if (
        linkBubbleRef.current &&
        !linkBubbleRef.current.contains(e.target as Node)
      ) {
        setShowLinkBubble(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [showLinkBubble]);

  // Auto-focus URL input when bubble opens
  useEffect(() => {
    if (showLinkBubble) {
      setTimeout(() => linkUrlInputRef.current?.focus(), 50);
    }
  }, [showLinkBubble]);

  if (!editor) return null;

  const openLinkBubble = () => {
    const previousUrl = editor.getAttributes("link").href ?? "";
    const { from, to } = editor.state.selection;
    const hasSelection = from !== to;
    const selectedText = hasSelection
      ? editor.state.doc.textBetween(from, to)
      : "";

    setLinkUrl(previousUrl);
    setLinkText(hasSelection ? selectedText : "");
    setLinkHasSelection(hasSelection);
    setLinkSelectionFrom(from);
    setShowLinkBubble(true);
  };

  const applyLink = () => {
    const url = linkUrl.trim();
    if (!url) {
      // URL vide → supprimer le lien si on est sur un lien
      if (editor.isActive("link")) {
        editor.chain().focus().extendMarkRange("link").unsetLink().run();
      }
      setShowLinkBubble(false);
      return;
    }

    if (linkHasSelection) {
      editor
        .chain()
        .focus()
        .extendMarkRange("link")
        .setLink({ href: url })
        .run();
    } else {
      const text = linkText.trim() || url;
      const from = linkSelectionFrom;
      editor
        .chain()
        .focus()
        .insertContent(text)
        .setTextSelection({ from, to: from + text.length })
        .setLink({ href: url })
        .setTextSelection(from + text.length)
        .run();
    }
    setShowLinkBubble(false);
  };

  const currentColor =
    (editor.getAttributes("textStyle").color as string) ?? "";

  const s = 16; // icon size

  return (
    <div className="flex flex-wrap items-center gap-0.5 p-2 border-b border-[var(--border)] bg-[var(--color-surface-subtle)] rounded-t-lg">
      {/* Undo / Redo */}
      <ToolbarBtn
        onClick={() => editor.chain().focus().undo().run()}
        disabled={!editor.can().undo()}
        title={t("editor.undo")}
      >
        <Undo2 size={s} />
      </ToolbarBtn>
      <ToolbarBtn
        onClick={() => editor.chain().focus().redo().run()}
        disabled={!editor.can().redo()}
        title={t("editor.redo")}
      >
        <Redo2 size={s} />
      </ToolbarBtn>

      <span className="w-px h-5 bg-[var(--border)] mx-1" />

      {/* Texte */}
      <ToolbarBtn
        onClick={() => editor.chain().focus().toggleBold().run()}
        active={editor.isActive("bold")}
        title={t("editor.bold")}
      >
        <Bold size={s} />
      </ToolbarBtn>
      <ToolbarBtn
        onClick={() => editor.chain().focus().toggleItalic().run()}
        active={editor.isActive("italic")}
        title={t("editor.italic")}
      >
        <Italic size={s} />
      </ToolbarBtn>
      <ToolbarBtn
        onClick={() => editor.chain().focus().toggleUnderline().run()}
        active={editor.isActive("underline")}
        title={t("editor.underline")}
      >
        <UnderlineIcon size={s} />
      </ToolbarBtn>
      <ToolbarBtn
        onClick={() => editor.chain().focus().toggleStrike().run()}
        active={editor.isActive("strike")}
        title={t("editor.strikethrough")}
      >
        <Strikethrough size={s} />
      </ToolbarBtn>

      <span className="w-px h-5 bg-[var(--border)] mx-1" />

      {/* Headings */}
      <ToolbarBtn
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
        active={editor.isActive("heading", { level: 1 })}
        title={t("editor.h1")}
      >
        <Heading1 size={s} />
      </ToolbarBtn>
      <ToolbarBtn
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        active={editor.isActive("heading", { level: 2 })}
        title={t("editor.h2")}
      >
        <Heading2 size={s} />
      </ToolbarBtn>
      <ToolbarBtn
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        active={editor.isActive("heading", { level: 3 })}
        title={t("editor.h3")}
      >
        <Heading3 size={s} />
      </ToolbarBtn>

      <span className="w-px h-5 bg-[var(--border)] mx-1" />

      {/* Listes */}
      <ToolbarBtn
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        active={editor.isActive("bulletList")}
        title={t("editor.bulletList")}
      >
        <List size={s} />
      </ToolbarBtn>
      <ToolbarBtn
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        active={editor.isActive("orderedList")}
        title={t("editor.numberedList")}
      >
        <ListOrdered size={s} />
      </ToolbarBtn>

      <span className="w-px h-5 bg-[var(--border)] mx-1" />

      {/* Alignement */}
      <ToolbarBtn
        onClick={() => editor.chain().focus().setTextAlign("left").run()}
        active={editor.isActive({ textAlign: "left" })}
        title={t("editor.alignLeft")}
      >
        <AlignLeft size={s} />
      </ToolbarBtn>
      <ToolbarBtn
        onClick={() => editor.chain().focus().setTextAlign("center").run()}
        active={editor.isActive({ textAlign: "center" })}
        title={t("editor.alignCenter")}
      >
        <AlignCenter size={s} />
      </ToolbarBtn>
      <ToolbarBtn
        onClick={() => editor.chain().focus().setTextAlign("right").run()}
        active={editor.isActive({ textAlign: "right" })}
        title={t("editor.alignRight")}
      >
        <AlignRight size={s} />
      </ToolbarBtn>

      <span className="w-px h-5 bg-[var(--border)] mx-1" />

      {/* Lien */}
      <div className="relative" ref={linkBubbleRef}>
        <ToolbarBtn
          onClick={openLinkBubble}
          active={showLinkBubble || editor.isActive("link")}
          title={t("editor.insertLink")}
        >
          <LinkIcon size={s} />
        </ToolbarBtn>

        {showLinkBubble && (
          <div className="absolute top-full left-0 mt-2 z-50 p-3 rounded-2xl border border-[var(--border)] bg-[var(--color-surface)] backdrop-blur-xl shadow-[0_8px_32px_var(--color-shadow)] w-[280px]">
            {/* URL */}
            <div className="mb-2">
              <label className="block text-xs font-medium text-[var(--muted)] mb-1">
                URL
              </label>
              <input
                ref={linkUrlInputRef}
                type="url"
                value={linkUrl}
                onChange={(e) => setLinkUrl(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    applyLink();
                  }
                  if (e.key === "Escape") setShowLinkBubble(false);
                }}
                placeholder={t("editor.linkUrlPlaceholder")}
                className="w-full px-3 py-1.5 text-sm rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)] text-[var(--text)] placeholder:text-[var(--muted)] focus:outline-none focus:border-[rgb(var(--primary))] transition-colors"
              />
            </div>

            {/* Texte (seulement si pas de sélection) */}
            {!linkHasSelection && (
              <div className="mb-2">
                <label className="block text-xs font-medium text-[var(--muted)] mb-1">
                  Texte affiché
                </label>
                <input
                  type="text"
                  value={linkText}
                  onChange={(e) => setLinkText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      applyLink();
                    }
                    if (e.key === "Escape") setShowLinkBubble(false);
                  }}
                  placeholder={t("editor.linkTextPlaceholder")}
                  className="w-full px-3 py-1.5 text-sm rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)] text-[var(--text)] placeholder:text-[var(--muted)] focus:outline-none focus:border-[rgb(var(--primary))] transition-colors"
                />
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-2 mt-3">
              <button
                type="button"
                onClick={applyLink}
                className="btn btn-primary flex-1 !py-1.5 !px-3 !text-xs"
              >
                Appliquer
              </button>
              {editor.isActive("link") && (
                <button
                  type="button"
                  onClick={() => {
                    editor
                      .chain()
                      .focus()
                      .extendMarkRange("link")
                      .unsetLink()
                      .run();
                    setShowLinkBubble(false);
                  }}
                  className="btn btn-secondary !py-1.5 !px-3 !text-xs flex items-center gap-1 hover:!bg-[rgba(var(--danger),0.2)] hover:!border-[rgba(var(--danger),0.3)]"
                >
                  <Unlink size={12} />
                  {t("editor.remove")}
                </button>
              )}
              <button
                type="button"
                onClick={() => setShowLinkBubble(false)}
                className="btn btn-secondary !py-1.5 !px-2.5 !text-xs"
              >
                ✕
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Image */}
      <ToolbarBtn onClick={onInsertImage} title={t("editor.insertImage")}>
        <ImageIcon size={s} />
      </ToolbarBtn>

      <span className="w-px h-5 bg-[var(--border)] mx-1" />

      {/* Couleur */}
      <div className="relative" ref={colorPickerRef}>
        <ToolbarBtn
          onClick={() => setShowColorPicker((v) => !v)}
          active={showColorPicker}
          title={t("editor.textColor")}
        >
          <div className="flex flex-col items-center gap-0">
            <Palette size={s} />
            <span
              className="block w-4 h-1 rounded-sm mt-px"
              style={{ backgroundColor: currentColor || "currentColor" }}
            />
          </div>
        </ToolbarBtn>

        {showColorPicker && (
          <div className="absolute top-full left-0 mt-2 z-50 p-3 rounded-2xl border border-[var(--border)] bg-[var(--color-surface)] backdrop-blur-xl shadow-[0_8px_32px_var(--color-shadow)] w-[228px]">
            {/* Preset grid */}
            <div className="grid grid-cols-6 gap-1.5 mb-3">
              {PRESET_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => {
                    editor.chain().focus().setColor(c).run();
                    setShowColorPicker(false);
                  }}
                  className={`w-7 h-7 rounded-full cursor-pointer transition-all duration-200 hover:scale-125 hover:shadow-[0_0_8px_var(--color-shadow)] ${
                    currentColor === c
                      ? "ring-2 ring-[rgb(var(--primary))] ring-offset-2 ring-offset-[var(--color-surface)] scale-110"
                      : "border border-[var(--border)]"
                  }`}
                  style={{ backgroundColor: c }}
                  title={c}
                />
              ))}
            </div>

            {/* Divider */}
            <div className="border-t border-[var(--border)] my-2" />

            {/* Native color picker + reset */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => colorInputRef.current?.click()}
                className="flex-1 px-3 py-1.5 text-xs font-medium rounded-full border border-[var(--border)] bg-[var(--color-surface-input)] hover:bg-[var(--color-surface-hover)] transition-all duration-200 text-[var(--text)] cursor-pointer text-center"
              >
                Plus de couleurs…
              </button>
              <input
                ref={colorInputRef}
                type="color"
                value={currentColor || "#000000"}
                onChange={(e) => {
                  editor.chain().focus().setColor(e.target.value).run();
                }}
                onBlur={() => setShowColorPicker(false)}
                className="sr-only"
              />
              {currentColor && (
                <button
                  type="button"
                  onClick={() => {
                    editor.chain().focus().unsetColor().run();
                    setShowColorPicker(false);
                  }}
                  className="px-2.5 py-1.5 text-xs rounded-full border border-[var(--border)] bg-[var(--color-surface-input)] hover:bg-[rgba(var(--danger),0.2)] hover:border-[rgba(var(--danger),0.3)] transition-all duration-200 text-[var(--muted)] cursor-pointer"
                  title={t("editor.reset")}
                >
                  ✕
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Séparateur */}
      <ToolbarBtn
        onClick={() => editor.chain().focus().setHorizontalRule().run()}
        title={t("editor.divider")}
      >
        <Minus size={s} />
      </ToolbarBtn>

      {/* Code bloc */}
      <ToolbarBtn
        onClick={() => editor.chain().focus().toggleCodeBlock().run()}
        active={editor.isActive("codeBlock")}
        title={t("editor.codeBlock")}
      >
        <Code size={s} />
      </ToolbarBtn>
    </div>
  );
}

/* ────────────────────────── Main component ────────────────────────── */

export default function StructuredContentEditor({
  value,
  onChange,
}: StructuredContentEditorProps) {
  const [mode, setMode] = useState<"visual" | "html">("visual");
  const [showImageModal, setShowImageModal] = useState(false);
  const suppressUpdateRef = useRef(false);

  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
      }),
      ResizableImage.configure({ inline: false, allowBase64: true }),
      Link.configure({ openOnClick: false, autolink: true }),
      Underline,
      TextAlign.configure({ types: ["heading", "paragraph"] }),
      TextStyle,
      Color,
    ],
    content: value || "",
    onUpdate: ({ editor: ed }) => {
      if (suppressUpdateRef.current) return;
      onChange(ed.getHTML());
    },
    editorProps: {
      attributes: {
        class: "tiptap-editor-content",
      },
    },
  });

  // Sync external value → editor (when parent resets the value, e.g. after save)
  useEffect(() => {
    if (!editor) return;
    const currentHtml = editor.getHTML();
    // Only push if the HTML actually differs (avoids cursor-jump loops)
    if (value !== currentHtml) {
      suppressUpdateRef.current = true;
      editor.commands.setContent(value || "", { emitUpdate: false });
      suppressUpdateRef.current = false;
    }
  }, [value, editor]);

  /* ── Switching modes ── */
  const switchToHtml = useCallback(() => {
    setMode("html");
  }, []);

  const switchToVisual = useCallback(() => {
    if (editor) {
      suppressUpdateRef.current = true;
      editor.commands.setContent(value || "", { emitUpdate: false });
      suppressUpdateRef.current = false;
    }
    setMode("visual");
  }, [editor, value]);

  /* ── Image insertion ── */
  const handleInsertImage = useCallback(
    (imageUrl: string, altText: string, caption?: string) => {
      if (mode === "visual" && editor) {
        // Insert via Tiptap
        editor
          .chain()
          .focus()
          .setImage({
            src: imageUrl,
            alt: altText,
            title: caption || undefined,
          })
          .run();
      } else {
        // Fallback: append raw HTML
        const safeAlt = altText.replace(/"/g, "&quot;");
        const safeCaption = caption
          ? caption.replace(/</g, "&lt;").replace(/>/g, "&gt;")
          : undefined;

        const styleParts: string[] = [];
        styleParts.push("max-width: 100%");
        styleParts.push("height: auto");
        styleParts.push(
          "border-radius: 0.5rem",
          "display: block",
          "margin: 1.5rem 0",
        );
        const imgStyle = styleParts.join("; ");

        const imageHtml = safeCaption
          ? `<figure style="margin: 1.5rem 0;">
  <img src="${imageUrl}" alt="${safeAlt}" style="${imgStyle};" />
  <figcaption style="text-align: center; font-style: italic; color: #6b7280; margin-top: 0.5rem; font-size: 0.875rem;">${safeCaption}</figcaption>
</figure>`
          : `<img src="${imageUrl}" alt="${safeAlt}" style="${imgStyle};" />`;

        const prefix = value && value.trim().length > 0 ? `${value}\n\n` : "";
        onChange(`${prefix}${imageHtml}`);
      }
      setShowImageModal(false);
    },
    [mode, editor, value, onChange],
  );

  const tabBase =
    "px-4 py-2 text-sm font-medium rounded-t-lg transition-colors cursor-pointer select-none";
  const tabActive = `${tabBase} bg-[var(--color-surface-input)] text-[var(--text)] border border-b-0 border-[var(--border)]`;
  const tabInactive = `${tabBase} text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--color-surface-subtle)]`;

  return (
    <div className="space-y-0">
      {/* Mode tabs */}
      <div className="flex items-end gap-1">
        <button
          type="button"
          onClick={switchToVisual}
          className={mode === "visual" ? tabActive : tabInactive}
        >
          Éditeur visuel
        </button>
        <button
          type="button"
          onClick={switchToHtml}
          className={mode === "html" ? tabActive : tabInactive}
        >
          HTML
        </button>
      </div>

      {/* Visual mode */}
      {mode === "visual" && (
        <div className="border border-[var(--border)] rounded-lg rounded-tl-none overflow-hidden">
          <EditorToolbar
            editor={editor}
            onInsertImage={() => setShowImageModal(true)}
          />
          <div className="bg-[var(--color-surface-input)] min-h-[300px] max-h-[500px] overflow-y-auto">
            <EditorContent editor={editor} />
          </div>
        </div>
      )}

      {/* HTML mode */}
      {mode === "html" && (
        <div className="border border-[var(--border)] rounded-lg rounded-tl-none overflow-hidden">
          <div className="flex items-center gap-3 p-2 border-b border-[var(--border)] bg-[var(--color-surface-subtle)]">
            <button
              type="button"
              onClick={() => setShowImageModal(true)}
              className="px-3 py-1.5 rounded border border-[var(--border)] bg-[var(--color-surface-input)] hover:bg-[var(--color-surface-hover)] transition-colors flex items-center gap-2 text-xs font-semibold text-[var(--text)] cursor-pointer"
            >
              <ImageIcon className="w-3.5 h-3.5" />
              Insérer une image
            </button>
          </div>
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            rows={14}
            className="w-full font-mono text-sm p-4 bg-[var(--color-surface-input)] text-[var(--text)] focus:outline-none resize-y min-h-[300px]"
            placeholder="Collez ici le HTML de l'article ou de l'email."
          />
        </div>
      )}

      {/* Image modal (shared between both modes) */}
      <ImageModal
        isOpen={showImageModal}
        onClose={() => setShowImageModal(false)}
        onInsert={(url, alt, caption) => handleInsertImage(url, alt, caption)}
      />
    </div>
  );
}
