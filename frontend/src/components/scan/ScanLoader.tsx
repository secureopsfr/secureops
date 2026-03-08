"use client";

import { useLanguage } from "../LanguageProvider";
import { LoadingSpinner } from "../LoadingScreen";
import { Check } from "lucide-react";
import type { ScanStepDisplay } from "../../services/scanService";

interface ScanLoaderProps {
  steps: ScanStepDisplay[];
  /** Clé i18n pour le titre (défaut: scanner.loading). */
  titleKey?: string;
  /** Mode both : affiche 3 colonnes avec ligne qui split/merge. */
  crawlMode?: "html" | "playwright" | "both";
}

const STEP_I18N_KEYS: Record<string, string> = {
  crawl_html_done: "scanner.crawlHtmlDone",
  crawl_playwright_done: "scanner.crawlPlaywrightDone",
  crawl_stopping_other: "scanner.crawlStoppingOther",
  crawl_merging: "scanner.crawlMerging",
};

function getStepColumn(step: string): "html" | "common" | "playwright" {
  if (step.startsWith("html_")) return "html";
  if (step.startsWith("playwright_")) return "playwright";
  return "common";
}

function getDisplayMessage(
  step: string,
  message: string,
  t: (key: string) => string,
): string {
  return STEP_I18N_KEYS[step] ? t(STEP_I18N_KEYS[step]) : message;
}

const COLUMN_INDEX = { html: 0, common: 1, playwright: 2 } as const;

// --- Constantes layout mode "both" (une seule source de vérité) ---
const COL_WIDTH = 48;
const COL_GAP = 8;
const COL_CENTER_X: [number, number, number] = [
  COL_WIDTH / 2,
  COL_WIDTH + COL_GAP + COL_WIDTH / 2,
  COL_WIDTH * 2 + COL_GAP * 2 + COL_WIDTH / 2,
];
const ROW_CONTENT = 56;
const ROW_GAP = 12;
const ROW_STRIDE = ROW_CONTENT + ROW_GAP;
const CIRCLE_SIZE = 24;
const CIRCLE_RADIUS = CIRCLE_SIZE / 2;

/** Y du centre du cercle pour la ligne i. */
function circleCenterY(row: number): number {
  return row * ROW_STRIDE + ROW_CONTENT / 2;
}
/** Y du bord bas du cercle. */
function circleBottomY(row: number): number {
  return circleCenterY(row) + CIRCLE_RADIUS;
}
/** Y du bord haut du cercle. */
function circleTopY(row: number): number {
  return circleCenterY(row) - CIRCLE_RADIUS;
}

interface ConnectorSegment {
  d: string;
  done: boolean;
  key: string;
}

/**
 * Calcule les paths SVG pour les connecteurs.
 * Phases : Commun (verticale) → Split (Y) → Parallèle (HTML | Playwright) → Merge (Y inversé).
 */
function computeConnectors(steps: ScanStepDisplay[]): ConnectorSegment[] {
  const segments: ConnectorSegment[] = [];
  const cols = steps.map((s) => COLUMN_INDEX[getStepColumn(s.step)]);

  const htmlRows: number[] = [];
  const pwRows: number[] = [];
  const commonRows: number[] = [];
  cols.forEach((c, i) => {
    if (c === 0) htmlRows.push(i);
    else if (c === 2) pwRows.push(i);
    else commonRows.push(i);
  });

  const splitAfter = commonRows
    .filter((r) => r < (htmlRows[0] ?? Infinity) && r < (pwRows[0] ?? Infinity))
    .pop();
  const mergeInto = commonRows.find(
    (r) =>
      r >
      Math.max(
        htmlRows[htmlRows.length - 1] ?? -1,
        pwRows[pwRows.length - 1] ?? -1,
      ),
  );

  // Commun : liaisons verticales consécutives
  for (let i = 0; i < steps.length - 1; i++) {
    if (cols[i] === 1 && cols[i + 1] === 1) {
      segments.push({
        d: `M ${COL_CENTER_X[1]} ${circleBottomY(i)} V ${circleTopY(i + 1)}`,
        done: steps[i].done ?? false,
        key: `seq-c-${i}`,
      });
    }
  }

  // Split : commun → html et commun → playwright (même ySplit)
  if (
    splitAfter !== undefined &&
    (htmlRows[0] !== undefined || pwRows[0] !== undefined)
  ) {
    const y0 = circleBottomY(splitAfter);
    const y1 =
      htmlRows[0] !== undefined
        ? circleTopY(htmlRows[0])
        : circleTopY(pwRows[0]!);
    const y2 = pwRows[0] !== undefined ? circleTopY(pwRows[0]) : y1;
    const ySplit = (y0 + (y1 + y2) / 2) / 2;

    if (htmlRows[0] !== undefined) {
      segments.push({
        d: `M ${COL_CENTER_X[1]} ${y0} V ${ySplit} H ${COL_CENTER_X[0]} V ${circleTopY(htmlRows[0])}`,
        done: steps[splitAfter].done ?? false,
        key: "split-html",
      });
    }
    if (pwRows[0] !== undefined) {
      segments.push({
        d: `M ${COL_CENTER_X[1]} ${y0} V ${ySplit} H ${COL_CENTER_X[2]} V ${circleTopY(pwRows[0])}`,
        done: steps[splitAfter].done ?? false,
        key: "split-pw",
      });
    }
  }

  // Parallèle : html→html et playwright→playwright
  for (let j = 0; j < htmlRows.length - 1; j++) {
    const a = htmlRows[j]!;
    const b = htmlRows[j + 1]!;
    segments.push({
      d: `M ${COL_CENTER_X[0]} ${circleBottomY(a)} V ${circleTopY(b)}`,
      done: steps[a].done ?? false,
      key: `html-${j}`,
    });
  }
  for (let j = 0; j < pwRows.length - 1; j++) {
    const a = pwRows[j]!;
    const b = pwRows[j + 1]!;
    segments.push({
      d: `M ${COL_CENTER_X[2]} ${circleBottomY(a)} V ${circleTopY(b)}`,
      done: steps[a].done ?? false,
      key: `pw-${j}`,
    });
  }

  // Merge : html et playwright → commun
  if (mergeInto !== undefined && (htmlRows.length > 0 || pwRows.length > 0)) {
    const lastHtml = htmlRows[htmlRows.length - 1];
    const lastPw = pwRows[pwRows.length - 1];
    const yTarget = circleTopY(mergeInto);
    const yMerge =
      lastHtml !== undefined && lastPw !== undefined
        ? Math.max(circleBottomY(lastHtml), circleBottomY(lastPw))
        : lastHtml !== undefined
          ? (circleBottomY(lastHtml) + yTarget) / 2
          : (circleBottomY(lastPw!) + yTarget) / 2;

    if (lastHtml !== undefined) {
      segments.push({
        d: `M ${COL_CENTER_X[0]} ${circleBottomY(lastHtml)} V ${yMerge} H ${COL_CENTER_X[1]} V ${yTarget}`,
        done: steps[lastHtml].done ?? false,
        key: "merge-html",
      });
    }
    if (lastPw !== undefined) {
      segments.push({
        d: `M ${COL_CENTER_X[2]} ${circleBottomY(lastPw)} V ${yMerge} H ${COL_CENTER_X[1]} V ${yTarget}`,
        done: steps[lastPw].done ?? false,
        key: "merge-pw",
      });
    }
  }

  return segments;
}

interface StepRowProps {
  step: string;
  message: string;
  done: boolean;
  column: "html" | "common" | "playwright";
}

function StepRow({ step, message, done, column }: StepRowProps) {
  const { t } = useLanguage();
  const msg = STEP_I18N_KEYS[step] ? t(STEP_I18N_KEYS[step]) : message;
  const colIdx = COLUMN_INDEX[column];
  const isHtml = column === "html";
  const isRight = column === "common" || column === "playwright";

  return (
    <li
      className="relative flex min-w-0 items-center py-2"
      style={{ minHeight: ROW_CONTENT }}
    >
      {/* Zone gauche : message HTML, juste à côté du point */}
      <div className="flex min-w-0 flex-1 justify-end pr-3">
        {isHtml && (
          <span
            className={`text-sm ${done ? "text-muted-theme" : "font-medium text-[var(--text)]"}`}
          >
            {msg}
          </span>
        )}
      </div>
      {/* Graph centré : 3 colonnes */}
      <div
        className="flex shrink-0 items-center"
        style={{ width: CIRCLE_AREA_WIDTH }}
      >
        <div
          className="flex shrink-0 items-center justify-center"
          style={{ width: COL_WIDTH }}
        >
          {colIdx === 0 && <StepCircle done={done} />}
        </div>
        <div className="shrink-0" style={{ width: COL_GAP }} />
        <div
          className="flex shrink-0 items-center justify-center"
          style={{ width: COL_WIDTH }}
        >
          {colIdx === 1 && <StepCircle done={done} />}
        </div>
        <div className="shrink-0" style={{ width: COL_GAP }} />
        <div
          className="flex shrink-0 items-center justify-center"
          style={{ width: COL_WIDTH }}
        >
          {colIdx === 2 && <StepCircle done={done} />}
        </div>
      </div>
      {/* Zone droite : message Commun/Playwright, juste à côté du point */}
      <div className="flex min-w-0 flex-1 justify-start pl-3">
        {isRight && (
          <span
            className={`text-sm ${done ? "text-muted-theme" : "font-medium text-[var(--text)]"}`}
          >
            {msg}
          </span>
        )}
      </div>
    </li>
  );
}

function StepCircle({ done }: { done: boolean }) {
  return (
    <span
      className="flex h-6 w-6 shrink-0 items-center justify-center"
      role="status"
      aria-label={done ? "Terminé" : "En cours"}
    >
      {done ? (
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[rgba(var(--success),0.2)] text-[rgb(var(--success))]">
          <Check className="h-3.5 w-3.5" strokeWidth={3} />
        </span>
      ) : (
        <LoadingSpinner size="sm" />
      )}
    </span>
  );
}

interface TimelineStepProps {
  step: string;
  message: string;
  done: boolean;
  isLast: boolean;
}

function TimelineStep({ step, message, done, isLast }: TimelineStepProps) {
  const { t } = useLanguage();
  const msg = STEP_I18N_KEYS[step] ? t(STEP_I18N_KEYS[step]) : message;

  return (
    <li className="relative flex gap-4 pb-5 last:pb-0">
      {!isLast && (
        <span
          className="absolute left-[11px] top-7 w-0.5 z-0"
          aria-hidden="true"
          style={{
            height: "calc(100% - 1.75rem)",
            background: done
              ? "rgb(var(--success))"
              : "rgba(var(--primary), 0.2)",
          }}
        />
      )}
      <span className="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center">
        {done ? (
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[rgba(var(--success),0.2)] text-[rgb(var(--success))]">
            <Check className="h-3.5 w-3.5" strokeWidth={3} />
          </span>
        ) : (
          <LoadingSpinner size="sm" />
        )}
      </span>
      <span className="min-w-0 flex-1 pt-0.5 text-base">{msg}</span>
    </li>
  );
}

const CIRCLE_AREA_WIDTH = COL_WIDTH * 3 + COL_GAP * 2;

export default function ScanLoader({
  steps,
  titleKey = "scanner.loading",
  crawlMode,
}: ScanLoaderProps) {
  const { t } = useLanguage();
  const useBoth =
    crawlMode === "both" &&
    (steps.some((s) => s.step.startsWith("html_")) ||
      steps.some((s) => s.step.startsWith("playwright_")));

  return (
    <div className="mx-auto max-w-4xl p-10 text-center">
      <h3 className="section-title -mt-2 mb-10 text-center text-2xl">
        {t(titleKey)}
      </h3>

      {steps.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-8">
          <LoadingSpinner size="md" />
          <span className="text-base text-muted-theme">{t(titleKey)}</span>
        </div>
      ) : useBoth ? (
        <div className="mx-auto flex w-full max-w-2xl flex-col items-center">
          <div
            className="relative w-full"
            style={{ minHeight: steps.length * ROW_STRIDE }}
          >
            <svg
              className="absolute left-1/2 top-0 z-0 -translate-x-1/2"
              width={CIRCLE_AREA_WIDTH}
              height={steps.length * ROW_STRIDE}
              viewBox={`0 0 ${CIRCLE_AREA_WIDTH} ${steps.length * ROW_STRIDE}`}
              preserveAspectRatio="xMinYMin meet"
              aria-hidden="true"
            >
              {computeConnectors(steps).map((seg) => (
                <path
                  key={seg.key}
                  d={seg.d}
                  fill="none"
                  stroke={
                    seg.done
                      ? "rgb(var(--success))"
                      : "rgba(var(--primary), 0.45)"
                  }
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              ))}
            </svg>
            <ul className="relative flex flex-col" style={{ gap: ROW_GAP }}>
              {steps.map((s, i) => (
                <StepRow
                  key={`${s.step}-${i}`}
                  step={s.step}
                  message={s.message}
                  done={s.done ?? false}
                  column={getStepColumn(s.step)}
                />
              ))}
            </ul>
          </div>
        </div>
      ) : (
        <ul className="mx-auto flex w-full max-w-md flex-col items-stretch">
          {steps.map((s, i) => (
            <TimelineStep
              key={`${s.step}-${i}`}
              step={s.step}
              message={s.message}
              done={s.done ?? false}
              isLast={i === steps.length - 1}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
