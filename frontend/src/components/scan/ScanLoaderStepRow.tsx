"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import {
  COL_GAP,
  COL_WIDTH,
  CIRCLE_AREA_WIDTH,
  ROW_CONTENT,
} from "./ScanLoaderGeometry";
import { COLUMN_INDEX } from "./ScanLoaderSteps";
import { getDisplayMessage } from "./ScanLoaderSteps";
import { StepCircle } from "./ScanLoaderPrimitives";
import type { TimelineStep } from "./ScanLoaderSteps";

export interface StepRowProps {
  step: TimelineStep;
  column: "html" | "common" | "playwright";
  pointDelay: number;
  isLatestStep: boolean;
  /** Appelé avec la hauteur (px) du panneau détails quand il change (0 = replié). */
  onDetailsHeightChange?: (height: number) => void;
}

export function StepRow({
  step,
  column,
  pointDelay,
  isLatestStep,
  onDetailsHeightChange,
}: StepRowProps) {
  const { t } = useLanguage();
  const [detailsExpanded, setDetailsExpanded] = useState(false);
  const [autoFollow, setAutoFollow] = useState(true);
  const detailsRef = useRef<HTMLDivElement | null>(null);

  const msg = getDisplayMessage(step, t);
  const colIdx = COLUMN_INDEX[column];
  const isHtml = column === "html";
  const isRight = column === "common" || column === "playwright";
  const isStoppingOther = step.step === "crawl_stopping_other";
  const done = step.done ?? false;
  const anomalyCount = step.anomaly_count ?? 0;
  const isAnomalous = done && anomalyCount > 0 && !isStoppingOther;
  const hasDetails = Boolean(step.details && step.details.length > 0);

  useEffect(() => {
    if (detailsExpanded) setAutoFollow(true);
  }, [detailsExpanded]);

  useEffect(() => {
    if (!detailsExpanded || !autoFollow) return;
    const el = detailsRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [detailsExpanded, step.details, autoFollow]);

  // Mesurer la hauteur du panneau et remonter au parent
  useEffect(() => {
    if (!detailsExpanded) {
      onDetailsHeightChange?.(0);
      return;
    }
    const el = detailsRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      onDetailsHeightChange?.(el.offsetHeight);
    });
    ro.observe(el);
    onDetailsHeightChange?.(el.offsetHeight);
    return () => ro.disconnect();
  }, [detailsExpanded, onDetailsHeightChange]);

  const textClass = (base: string) =>
    `${base} whitespace-nowrap ${
      isLatestStep
        ? "font-semibold text-[var(--text)]"
        : isStoppingOther && done
          ? "text-[rgba(255,255,255,0.3)]"
          : isAnomalous
            ? "font-medium text-[rgb(var(--warning))]"
            : done
              ? "text-muted-theme"
              : "font-medium text-[var(--text)]"
    }`;

  return (
    <li className="flex min-w-0 flex-col" style={{ minHeight: ROW_CONTENT }}>
      <div
        className="flex min-w-0 items-center"
        style={{ height: ROW_CONTENT }}
      >
        {/* Zone gauche : message HTML */}
        <div className="flex min-w-0 flex-1 justify-end pr-3">
          {isHtml && (
            <span
              className={textClass("text-base scan-animate-point")}
              style={{
                opacity: 0,
                animation: `scan-point-appear 0.25s ease-out ${pointDelay}ms forwards`,
              }}
            >
              {msg}
            </span>
          )}
        </div>

        {/* Graph centré : 3 colonnes */}
        <div
          className="flex shrink-0 items-center"
          style={{ width: CIRCLE_AREA_WIDTH, height: ROW_CONTENT }}
        >
          <div
            className="flex shrink-0 items-center justify-center"
            style={{ width: COL_WIDTH }}
          >
            {colIdx === 0 && (
              <StepCircle
                done={done}
                animateDelay={pointDelay}
                muted={isStoppingOther && done}
                anomalous={isAnomalous}
              />
            )}
          </div>
          <div className="shrink-0" style={{ width: COL_GAP }} />
          <div
            className="flex shrink-0 items-center justify-center"
            style={{ width: COL_WIDTH }}
          >
            {colIdx === 1 && (
              <StepCircle
                done={done}
                animateDelay={pointDelay}
                muted={isStoppingOther && done}
                anomalous={isAnomalous}
              />
            )}
          </div>
          <div className="shrink-0" style={{ width: COL_GAP }} />
          <div
            className="flex shrink-0 items-center justify-center"
            style={{ width: COL_WIDTH }}
          >
            {colIdx === 2 && (
              <StepCircle
                done={done}
                animateDelay={pointDelay}
                muted={isStoppingOther && done}
                anomalous={isAnomalous}
              />
            )}
          </div>
        </div>

        {/* Zone droite : message Commun/Playwright */}
        <div className="flex min-w-0 flex-1 justify-start pl-3">
          {isRight && (
            <div
              className="scan-animate-point"
              style={{
                opacity: 0,
                animation: `scan-point-appear 0.25s ease-out ${pointDelay}ms forwards`,
              }}
            >
              <span className={textClass("text-base")}>{msg}</span>
              {hasDetails && (
                <div className="mt-1">
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 text-xs text-[rgb(var(--primary))] hover:underline"
                    onClick={() => setDetailsExpanded((v) => !v)}
                  >
                    {detailsExpanded
                      ? t("scanner.hideDetails")
                      : t("scanner.showDetails")}
                    {detailsExpanded ? (
                      <ChevronUp className="h-3.5 w-3.5" />
                    ) : (
                      <ChevronDown className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Panneau détails */}
      {hasDetails && detailsExpanded && (
        <div className="flex min-w-0 items-start">
          <div className="flex-1" />
          <div className="shrink-0" style={{ width: CIRCLE_AREA_WIDTH }} />
          <div className="flex min-w-0 flex-1 pl-3">
            <div
              ref={detailsRef}
              className="w-full max-h-44 overflow-y-auto rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] pt-2 pb-2 px-3 shadow-lg"
              onWheel={() => setAutoFollow(false)}
              onTouchStart={() => setAutoFollow(false)}
              onPointerDown={() => setAutoFollow(false)}
            >
              <ul className="space-y-1 pr-1">
                {(step.details ?? []).map((detail, idx) => (
                  <li
                    key={`${step.step}-detail-${idx}`}
                    className="text-xs text-[var(--muted)]"
                  >
                    {detail}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </li>
  );
}
