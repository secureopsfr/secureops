"use client";

import { useState } from "react";
import {
  Mail,
  User,
  FileText,
  Calendar,
  GripVertical,
  Clock,
  CheckCircle2,
  Circle,
  Reply,
  Trash2,
} from "lucide-react";
import { log } from "../../utils/logger";
import { formatDateTimeShort } from "../../utils/dateFormat";
import { useLanguage } from "../LanguageProvider";

const STATUS_COLUMN_DEFS = [
  {
    id: "pending",
    titleKey: "admin.contact.pending" as const,
    icon: Clock,
    cssVar: "--warning",
  },
  {
    id: "in_progress",
    titleKey: "admin.contact.inProgress" as const,
    icon: Circle,
    cssVar: "--info",
  },
  {
    id: "processed",
    titleKey: "admin.contact.processed" as const,
    icon: CheckCircle2,
    cssVar: "--success",
  },
];

interface ContactMessage {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  subject: string;
  message: string;
  status: string;
  created_at: string;
  updated_at: string;
  [key: string]: unknown;
}

interface ContactKanbanProps {
  messages: ContactMessage[];
  onStatusChange: (messageId: number, newStatus: string) => void;
  updatingStatusId?: number | null;
  onReply?: (message: ContactMessage) => void;
  onDelete?: (message: ContactMessage) => void;
}

export default function ContactKanban({
  messages,
  onStatusChange,
  updatingStatusId,
  onReply,
  onDelete,
}: ContactKanbanProps) {
  const { t } = useLanguage();
  const [draggedMessage, setDraggedMessage] = useState<ContactMessage | null>(
    null,
  );
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);

  const getMessagesByStatus = (status: string) => {
    return messages.filter((msg) => msg.status === status);
  };

  const handleDragStart = (e: React.DragEvent, message: ContactMessage) => {
    setDraggedMessage(message);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData(
      "application/json",
      JSON.stringify({ id: message.id, status: message.status }),
    );
    // Créer une image de drag personnalisée
    const dragImage = e.currentTarget.cloneNode(true) as HTMLElement;
    dragImage.style.opacity = "0.8";
    dragImage.style.transform = "rotate(3deg)";
    dragImage.style.width = (e.currentTarget as HTMLElement).offsetWidth + "px";
    document.body.appendChild(dragImage);
    e.dataTransfer.setDragImage(
      dragImage,
      (e.currentTarget as HTMLElement).offsetWidth / 2,
      20,
    );
    setTimeout(() => document.body.removeChild(dragImage), 0);

    (e.currentTarget as HTMLElement).style.opacity = "0.4";
    (e.currentTarget as HTMLElement).style.transform =
      "rotate(2deg) scale(0.95)";
    (e.currentTarget as HTMLElement).style.cursor = "grabbing";
  };

  const handleDragEnd = (e: React.DragEvent) => {
    (e.currentTarget as HTMLElement).style.opacity = "1";
    (e.currentTarget as HTMLElement).style.transform = "";
    (e.currentTarget as HTMLElement).style.cursor = "grab";
    setDraggedMessage(null);
    setDragOverColumn(null);
  };

  const handleDragOver = (e: React.DragEvent, columnId: string) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = "move";
    setDragOverColumn(columnId);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    // Ne pas retirer le dragOverColumn si on est toujours dans la colonne
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      setDragOverColumn(null);
    }
  };

  const handleDrop = (e: React.DragEvent, targetStatus: string) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOverColumn(null);

    if (draggedMessage && draggedMessage.status !== targetStatus) {
      log(
        `Moving message ${draggedMessage.id} from ${draggedMessage.status} to ${targetStatus}`,
      );
      onStatusChange(draggedMessage.id, targetStatus);
    }

    setDraggedMessage(null);
  };

  const truncateText = (text: string, maxLength = 100) => {
    if (!text) return "";
    return text.length > maxLength
      ? `${text.substring(0, maxLength)}...`
      : text;
  };

  return (
    <div className="grid grid-cols-3 gap-6 pb-6">
      {STATUS_COLUMN_DEFS.map((column) => {
        const columnMessages = getMessagesByStatus(column.id);
        const isDragOver = dragOverColumn === column.id;
        const Icon = column.icon;

        const c = `var(${column.cssVar})`;

        return (
          <div
            key={column.id}
            className={`rounded-2xl border-2 backdrop-blur-sm transition-all duration-200 flex flex-col ${
              isDragOver
                ? "ring-4 ring-[rgb(var(--primary))] ring-offset-2 scale-[1.01] shadow-2xl"
                : "shadow-lg hover:shadow-xl"
            }`}
            style={{
              borderColor: isDragOver
                ? `rgba(var(--primary),0.6)`
                : `rgba(${c},0.4)`,
              background: `linear-gradient(to bottom, rgba(${c},0.1), transparent)`,
            }}
          >
            {/* Header avec bulle */}
            <div
              className="px-5 py-4 rounded-t-2xl border-b-2 backdrop-blur-sm"
              style={{
                background: `linear-gradient(to bottom right, rgba(${c},0.3), rgba(${c},0.2))`,
                color: `rgb(${c})`,
                borderColor: `rgba(${c},0.4)`,
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="p-2 rounded-xl backdrop-blur-sm"
                    style={{
                      backgroundColor: `rgba(${c},0.3)`,
                      color: `rgb(${c})`,
                    }}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-base">
                      {t(column.titleKey)}
                    </h3>
                    <p className="text-xs opacity-80 mt-0.5">
                      {columnMessages.length}{" "}
                      {columnMessages.length === 1
                        ? t("admin.contact.message")
                        : t("admin.contact.messages")}
                    </p>
                  </div>
                </div>
                <div
                  className="px-3 py-1.5 rounded-full text-sm font-bold backdrop-blur-sm shadow-lg"
                  style={{
                    backgroundColor: `rgba(${c},0.3)`,
                    color: `rgb(${c})`,
                  }}
                >
                  {columnMessages.length}
                </div>
              </div>
            </div>

            {/* Zone de drop avec bulles */}
            <div
              className={`p-4 space-y-4 flex-1 min-h-[600px] max-h-[calc(100vh-250px)] overflow-y-auto transition-all duration-200 ${
                isDragOver
                  ? "bg-[rgba(var(--primary),0.1)] border-2 border-dashed border-[rgb(var(--primary))]/50"
                  : ""
              }`}
              style={{ scrollbarWidth: "thin" }}
              onDragOver={(e) => handleDragOver(e, column.id)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, column.id)}
            >
              {columnMessages.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div
                    className="p-4 rounded-full mb-3 opacity-50"
                    style={{
                      backgroundColor: `rgba(${c},0.3)`,
                      color: `rgb(${c})`,
                    }}
                  >
                    <Icon className="h-8 w-8" />
                  </div>
                  <p className="text-[var(--muted)] text-sm opacity-60">
                    {t("admin.contact.noMessageInColumn")}
                  </p>
                  <p className="text-[var(--muted)] text-xs mt-1 opacity-40">
                    {t("admin.contact.dragHere")}
                  </p>
                </div>
              ) : (
                columnMessages.map((message) => {
                  const isDragging = draggedMessage?.id === message.id;
                  const isUpdating = updatingStatusId === message.id;

                  return (
                    <div
                      key={message.id}
                      draggable={!isUpdating}
                      onDragStart={(e) => handleDragStart(e, message)}
                      onDragEnd={handleDragEnd}
                      className={`group relative rounded-xl border-2 p-5 cursor-grab active:cursor-grabbing hover:shadow-xl hover:scale-[1.02] transition-all duration-200 backdrop-blur-sm ${
                        isDragging ? "opacity-40 scale-95 rotate-2" : ""
                      } ${isUpdating ? "opacity-50 cursor-not-allowed" : "hover:shadow-2xl"}`}
                      style={{
                        background: `linear-gradient(to bottom right, rgba(${c},0.05), rgba(${c},0.05))`,
                        borderColor: `rgba(${c},0.2)`,
                        boxShadow: isDragging
                          ? "none"
                          : "0 8px 16px -4px rgba(0, 0, 0, 0.2), 0 4px 8px -2px rgba(0, 0, 0, 0.1)",
                        userSelect: "none",
                      }}
                    >
                      {/* Indicateur de drag */}
                      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                        <GripVertical className="h-5 w-5 text-[var(--muted)]" />
                      </div>

                      {/* Loading indicator */}
                      {isUpdating && (
                        <div className="absolute top-3 right-3">
                          <div className="animate-spin rounded-full h-5 w-5 border-2 border-[rgb(var(--primary))] border-t-transparent"></div>
                        </div>
                      )}

                      {/* Date */}
                      <div className="flex items-center gap-2 mb-4 text-xs text-[var(--muted)]">
                        <Calendar className="h-3.5 w-3.5" />
                        <span>{formatDateTimeShort(message.created_at)}</span>
                      </div>

                      {/* Sujet avec icône */}
                      <div className="flex items-start gap-3 mb-4">
                        <div
                          className="p-2 rounded-lg mt-0.5 flex-shrink-0"
                          style={{
                            backgroundColor: `rgba(${c},0.3)`,
                            color: `rgb(${c})`,
                          }}
                        >
                          <FileText className="h-4 w-4" />
                        </div>
                        <h4 className="font-bold text-sm text-[var(--text)] line-clamp-2 flex-1 leading-tight">
                          {message.subject}
                        </h4>
                      </div>

                      {/* Expéditeur */}
                      <div className="flex items-center gap-3 mb-3 p-2 rounded-lg bg-[var(--color-surface-subtle)]">
                        <div
                          className="p-1.5 rounded-lg"
                          style={{
                            backgroundColor: `rgba(${c},0.3)`,
                            color: `rgb(${c})`,
                          }}
                        >
                          <User className="h-3.5 w-3.5" />
                        </div>
                        <span className="text-sm text-[var(--text)] font-medium">
                          {message.first_name} {message.last_name}
                        </span>
                      </div>

                      {/* Email */}
                      <div className="flex items-center gap-3 mb-4 p-2 rounded-lg bg-[var(--color-surface-subtle)]">
                        <div
                          className="p-1.5 rounded-lg"
                          style={{
                            backgroundColor: `rgba(${c},0.3)`,
                            color: `rgb(${c})`,
                          }}
                        >
                          <Mail className="h-3.5 w-3.5" />
                        </div>
                        <a
                          href={`mailto:${message.email}`}
                          className="text-sm text-[rgb(var(--primary))] hover:underline truncate flex-1 font-medium"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {message.email}
                        </a>
                      </div>

                      {/* Aperçu du message dans une bulle */}
                      <div className="mt-4 p-3 rounded-lg bg-[var(--color-surface-input-hover)] border border-[var(--border)] backdrop-blur-sm">
                        <p className="text-xs text-[var(--muted)] line-clamp-4 leading-relaxed">
                          {truncateText(message.message, 150)}
                        </p>
                      </div>

                      {/* Actions répondre / supprimer */}
                      <div className="mt-3 flex items-center gap-2">
                        {onReply && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onReply(message);
                            }}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-[rgba(var(--primary),0.15)] text-[rgb(var(--primary))] hover:bg-[rgba(var(--primary),0.25)] transition-colors"
                            title={t("admin.contact.replyTooltip")}
                          >
                            <Reply className="h-3.5 w-3.5" />
                            {t("admin.contact.reply")}
                          </button>
                        )}
                        {onDelete && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDelete(message);
                            }}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
                            style={{
                              backgroundColor: `rgba(var(--danger),0.1)`,
                              color: `rgb(var(--danger))`,
                            }}
                            title={t("admin.contact.deleteTooltip")}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>

                      {/* Effet de brillance au survol */}
                      <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>

                      {/* Bordure de case au survol */}
                      <div
                        className="absolute inset-0 rounded-xl border-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"
                        style={{ borderColor: `rgba(${c},0.2)` }}
                      ></div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
