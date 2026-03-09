"use client";

import { useEffect, useMemo, useRef, useState } from "react";
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
  /** Appelé quand l'animation totale est terminée. */
  onAnimationComplete?: () => void;
}

const STEP_I18N_KEYS: Record<string, string> = {
  crawl_html_done: "scanner.crawlHtmlDone",
  crawl_playwright_done: "scanner.crawlPlaywrightDone",
  crawl_stopping_other: "scanner.crawlStoppingOther",
  crawl_merging: "scanner.crawlMerging",
};

/**
 * Colonne du step pour le layout en Y.
 * crawl_stopping_other = étape du crawler qu'on arrête (l'autre) → html ou playwright selon qui a fini en premier.
 */
function getStepColumn(
  step: string,
  steps: ScanStepDisplay[],
  index: number,
): "html" | "common" | "playwright" {
  if (step.startsWith("html_")) return "html";
  if (step.startsWith("playwright_")) return "playwright";
  if (step === "crawl_html_done") return "html";
  if (step === "crawl_playwright_done") return "playwright";
  if (step === "crawl_stopping_other") {
    // L'étape précédente indique qui a fini → l'autre est celui qu'on arrête
    const prev = index > 0 ? steps[index - 1]?.step : "";
    return prev === "crawl_html_done" ? "playwright" : "html";
  }
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
/** Espace vertical supplémentaire après la séparation et avant la fusion. */
const SPLIT_MERGE_PADDING = 20;
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
  /** Délai (ms) avant de démarrer l'animation, pour respecter l'ordre par colonne. */
  delayMs: number;
}

/** Rayon des coins split (vertical → branches). */
const CORNER_RADIUS = 18;
/** Rayon pour les courbes de merge. */
const MERGE_CORNER_RADIUS = 22;

/** Kappa pour approximation Bezier d'un arc circulaire (≈ 0.552). */
const KAPPA = 0.5522847498;

/**
 * Clamp du rayon pour éviter débordements.
 * Facteurs permissifs pour des arrondis bien visibles.
 */
function clampRadius(
  r: number,
  y0: number,
  yMid: number,
  y1: number,
  x0: number,
  x1: number,
): number {
  const dVert1 = Math.abs(y0 - yMid);
  const dVert2 = Math.abs(y1 - yMid);
  const dHoriz = Math.abs(x1 - x0);
  const maxFromVert = Math.min(dVert1, dVert2) * 0.52;
  const maxFromHoriz = dHoriz * 0.5;
  const maxR = Math.max(12, Math.min(maxFromVert, maxFromHoriz));
  return Math.min(r, maxR);
}

/**
 * Path vertical → horizontal → vertical avec courbes de Bézier cubiques.
 * Si radiusOverride est fourni, pas de clamp (pour symétrie split/merge).
 */
function pathWithRoundedCorners(
  x0: number,
  y0: number,
  yMid: number,
  x1: number,
  y1: number,
  r: number,
  radiusOverride?: number,
): string {
  const radius =
    radiusOverride !== undefined
      ? radiusOverride
      : clampRadius(r, y0, yMid, y1, x0, x1);
  const goLeft = x1 < x0;

  const c1x = goLeft ? x0 - radius : x0 + radius;
  const c2x = goLeft ? x1 + radius : x1 - radius;
  const k = radius * KAPPA;

  const approach1 =
    y0 < yMid ? yMid - radius : yMid + radius;
  const approach2 =
    y1 > yMid ? yMid + radius : yMid - radius;

  const cp1x = x0;
  const cp1y = y0 < yMid ? approach1 + k : approach1 - k;
  const cp2x = goLeft ? c1x + k : c1x - k;
  const cp2y = yMid;

  const cp3x = goLeft ? c2x - k : c2x + k;
  const cp3y = yMid;
  const cp4x = x1;
  const cp4y = y1 > yMid ? approach2 - k : approach2 + k;

  return `M ${x0} ${y0} L ${x0} ${approach1} C ${cp1x} ${cp1y} ${cp2x} ${cp2y} ${c1x} ${yMid} L ${c2x} ${yMid} C ${cp3x} ${cp3y} ${cp4x} ${cp4y} ${x1} ${approach2} L ${x1} ${y1}`;
}

/** Délai avant apparition du point (ms) pour qu'il apparaisse à la fin de la ligne. */
const POINT_APPEAR_DELAY = 380;
/** Durée d'un "pas" : trait + apparition du point (ms). */
const STEP_DURATION = 630;

/**
 * Calcule les paths SVG et les délais d'animation par colonne.
 * Chaque trait attend que le précédent dans la même colonne ait fini + point apparu.
 */
const POINT_ANIM_DURATION = 250;

function computeConnectors(
  steps: ScanStepDisplay[],
): { segments: ConnectorSegment[]; pointDelays: number[]; totalDurationMs: number } {
  const segments: ConnectorSegment[] = [];
  const pointDelays = new Array<number>(steps.length).fill(0);
  const cols = steps.map((s, i) =>
    COLUMN_INDEX[getStepColumn(s.step, steps, i)],
  );

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

  let commonDelay = 0;
  let htmlDelay = 0;
  let pwDelay = 0;

  // Commun AVANT split : liaisons verticales consécutives (rows <= splitAfter uniquement)
  const splitAfterRow = splitAfter ?? -1;
  for (let i = 0; i < steps.length - 1; i++) {
    if (
      cols[i] === 1 &&
      cols[i + 1] === 1 &&
      i <= splitAfterRow &&
      i + 1 <= splitAfterRow
    ) {
      segments.push({
        d: `M ${COL_CENTER_X[1]} ${circleBottomY(i)} V ${circleTopY(i + 1)}`,
        done: steps[i].done ?? false,
        key: `seq-c-${i}`,
        delayMs: commonDelay,
      });
      pointDelays[i + 1] = commonDelay + POINT_APPEAR_DELAY;
      commonDelay += STEP_DURATION;
    }
  }

  const commonBeforeSplit = commonDelay;

  // Split : commun → html et commun → playwright (symétrie parfaite)
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
    const yMidAvg = (y1 + y2) / 2;
    const ySplit = Math.min(
      y0 + SPLIT_MERGE_PADDING,
      (y0 + yMidAvg) / 2,
    );

    const rLeft =
      htmlRows[0] !== undefined
        ? clampRadius(
            CORNER_RADIUS,
            y0,
            ySplit,
            y1,
            COL_CENTER_X[1],
            COL_CENTER_X[0],
          )
        : CORNER_RADIUS;
    const rRight =
      pwRows[0] !== undefined
        ? clampRadius(
            CORNER_RADIUS,
            y0,
            ySplit,
            y2,
            COL_CENTER_X[1],
            COL_CENTER_X[2],
          )
        : CORNER_RADIUS;
    const rSplit = Math.min(rLeft, rRight);

    if (htmlRows[0] !== undefined) {
      htmlDelay = commonBeforeSplit;
      segments.push({
        d: pathWithRoundedCorners(
          COL_CENTER_X[1],
          y0,
          ySplit,
          COL_CENTER_X[0],
          y1,
          CORNER_RADIUS,
          rSplit,
        ),
        done: steps[splitAfter].done ?? false,
        key: "split-html",
        delayMs: htmlDelay,
      });
      pointDelays[htmlRows[0]] = htmlDelay + POINT_APPEAR_DELAY;
      htmlDelay += STEP_DURATION;
    }
    if (pwRows[0] !== undefined) {
      pwDelay = commonBeforeSplit;
      segments.push({
        d: pathWithRoundedCorners(
          COL_CENTER_X[1],
          y0,
          ySplit,
          COL_CENTER_X[2],
          y2,
          CORNER_RADIUS,
          rSplit,
        ),
        done: steps[splitAfter].done ?? false,
        key: "split-pw",
        delayMs: pwDelay,
      });
      pointDelays[pwRows[0]] = pwDelay + POINT_APPEAR_DELAY;
      pwDelay += STEP_DURATION;
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
      delayMs: htmlDelay,
    });
    pointDelays[b] = htmlDelay + POINT_APPEAR_DELAY;
    htmlDelay += STEP_DURATION;
  }
  for (let j = 0; j < pwRows.length - 1; j++) {
    const a = pwRows[j]!;
    const b = pwRows[j + 1]!;
    segments.push({
      d: `M ${COL_CENTER_X[2]} ${circleBottomY(a)} V ${circleTopY(b)}`,
      done: steps[a].done ?? false,
      key: `pw-${j}`,
      delayMs: pwDelay,
    });
    pointDelays[b] = pwDelay + POINT_APPEAR_DELAY;
    pwDelay += STEP_DURATION;
  }

  // Merge : html et playwright → commun (symétrie parfaite)
  const mergeDelay = Math.max(htmlDelay, pwDelay);
  if (mergeInto !== undefined && (htmlRows.length > 0 || pwRows.length > 0)) {
    const lastHtml = htmlRows[htmlRows.length - 1];
    const lastPw = pwRows[pwRows.length - 1];
    const yTarget = circleTopY(mergeInto);
    const bottomHtml = lastHtml !== undefined ? circleBottomY(lastHtml) : yTarget;
    const bottomPw = lastPw !== undefined ? circleBottomY(lastPw) : yTarget;
    const maxBottom =
      lastHtml !== undefined && lastPw !== undefined
        ? Math.max(bottomHtml, bottomPw)
        : lastHtml !== undefined
          ? bottomHtml
          : bottomPw;
    const gapToTarget = yTarget - maxBottom;
    const yMerge = maxBottom + Math.min(SPLIT_MERGE_PADDING, gapToTarget * 0.6);

    const rMergeHtml = clampRadius(
      MERGE_CORNER_RADIUS,
      bottomHtml,
      yMerge,
      yTarget,
      COL_CENTER_X[0],
      COL_CENTER_X[1],
    );
    const rMergePw = clampRadius(
      MERGE_CORNER_RADIUS,
      bottomPw,
      yMerge,
      yTarget,
      COL_CENTER_X[2],
      COL_CENTER_X[1],
    );
    const rMerge = Math.min(rMergeHtml, rMergePw);

    if (lastHtml !== undefined) {
      segments.push({
        d: pathWithRoundedCorners(
          COL_CENTER_X[0],
          bottomHtml,
          yMerge,
          COL_CENTER_X[1],
          yTarget,
          MERGE_CORNER_RADIUS,
          rMerge,
        ),
        done: steps[lastHtml].done ?? false,
        key: "merge-html",
        delayMs: mergeDelay,
      });
    }
    if (lastPw !== undefined) {
      segments.push({
        d: pathWithRoundedCorners(
          COL_CENTER_X[2],
          bottomPw,
          yMerge,
          COL_CENTER_X[1],
          yTarget,
          MERGE_CORNER_RADIUS,
          rMerge,
        ),
        done: steps[lastPw].done ?? false,
        key: "merge-pw",
        delayMs: mergeDelay,
      });
    }
    // Le point de fusion apparaît quand les traits merge sont finis (pas avant)
    pointDelays[mergeInto] = mergeDelay + PATH_DRAW_DURATION;
  }

  // Commun APRÈS merge : segments verticaux (rows >= mergeInto), après la fusion
  let afterMergeDelay =
    mergeInto !== undefined && (htmlRows.length > 0 || pwRows.length > 0)
      ? mergeDelay + PATH_DRAW_DURATION
      : commonDelay;
  const mergeIntoRow = mergeInto ?? steps.length;
  for (let i = 0; i < steps.length - 1; i++) {
    if (
      cols[i] === 1 &&
      cols[i + 1] === 1 &&
      i >= mergeIntoRow &&
      i + 1 >= mergeIntoRow
    ) {
      segments.push({
        d: `M ${COL_CENTER_X[1]} ${circleBottomY(i)} V ${circleTopY(i + 1)}`,
        done: steps[i].done ?? false,
        key: `seq-c-after-${i}`,
        delayMs: afterMergeDelay,
      });
      pointDelays[i + 1] = afterMergeDelay + POINT_APPEAR_DELAY;
      afterMergeDelay += STEP_DURATION;
    }
  }

  const maxConnectorEnd =
    segments.length > 0
      ? Math.max(...segments.map((s) => s.delayMs + PATH_DRAW_DURATION))
      : 0;
  const maxPointEnd =
    pointDelays.length > 0
      ? Math.max(...pointDelays.map((d) => d + POINT_ANIM_DURATION))
      : 0;
  const totalDurationMs = Math.max(maxConnectorEnd, maxPointEnd);

  return { segments, pointDelays, totalDurationMs };
}

/** Durée de l'animation de dessin de la ligne (ms). */
const PATH_DRAW_DURATION = 500;

function AnimatedConnectorPath({
  d,
  done,
  segKey,
  delayMs,
}: {
  d: string;
  done: boolean;
  segKey: string;
  delayMs: number;
}) {
  const pathRef = useRef<SVGPathElement>(null);
  const [length, setLength] = useState<number | null>(null);

  useEffect(() => {
    const el = pathRef.current;
    if (el) {
      setLength(el.getTotalLength());
    }
  }, [d]);

  const strokeColor = done
    ? "rgb(var(--success))"
    : "rgba(var(--primary), 0.2)";

  if (length == null) {
    return (
      <path
        ref={pathRef}
        d={d}
        fill="none"
        stroke={strokeColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray="9999"
        strokeDashoffset="9999"
      />
    );
  }

  return (
    <path
      ref={pathRef}
      d={d}
      fill="none"
      stroke={strokeColor}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="scan-animate-path"
      style={{
        strokeDasharray: length,
        strokeDashoffset: length,
        animation: `scan-draw-path ${PATH_DRAW_DURATION}ms ease-out ${delayMs}ms forwards`,
      }}
    />
  );
}

interface StepRowProps {
  step: string;
  message: string;
  done: boolean;
  column: "html" | "common" | "playwright";
  index: number;
  pointDelay: number;
}

function StepRow({
  step,
  message,
  done,
  column,
  index,
  pointDelay,
}: StepRowProps) {
  const { t } = useLanguage();
  const msg = getDisplayMessage(step, message, t);
  const colIdx = COLUMN_INDEX[column];
  const isHtml = column === "html";
  const isRight = column === "common" || column === "playwright";

  return (
    <li
      className="relative flex min-w-0 items-center py-2"
      style={{ minHeight: ROW_CONTENT }}
    >
      {/* Zone gauche : message HTML, apparaît avec le point */}
      <div className="flex min-w-0 flex-1 justify-end pr-3">
        {isHtml && (
          <span
            className={`text-sm scan-animate-point ${done ? "text-muted-theme" : "font-medium text-[var(--text)]"}`}
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
        style={{ width: CIRCLE_AREA_WIDTH }}
      >
        <div
          className="flex shrink-0 items-center justify-center"
          style={{ width: COL_WIDTH }}
        >
          {colIdx === 0 && <StepCircle done={done} animateDelay={pointDelay} />}
        </div>
        <div className="shrink-0" style={{ width: COL_GAP }} />
        <div
          className="flex shrink-0 items-center justify-center"
          style={{ width: COL_WIDTH }}
        >
          {colIdx === 1 && <StepCircle done={done} animateDelay={pointDelay} />}
        </div>
        <div className="shrink-0" style={{ width: COL_GAP }} />
        <div
          className="flex shrink-0 items-center justify-center"
          style={{ width: COL_WIDTH }}
        >
          {colIdx === 2 && <StepCircle done={done} animateDelay={pointDelay} />}
        </div>
      </div>
      {/* Zone droite : message Commun/Playwright, apparaît avec le point */}
      <div className="flex min-w-0 flex-1 justify-start pl-3">
        {isRight && (
          <span
            className={`text-sm scan-animate-point ${done ? "text-muted-theme" : "font-medium text-[var(--text)]"}`}
            style={{
              opacity: 0,
              animation: `scan-point-appear 0.25s ease-out ${pointDelay}ms forwards`,
            }}
          >
            {msg}
          </span>
        )}
      </div>
    </li>
  );
}

function StepCircle({
  done,
  animateDelay = 0,
}: {
  done: boolean;
  animateDelay?: number;
}) {
  return (
    <span
      className="flex h-6 w-6 shrink-0 items-center justify-center scan-animate-point"
      role="status"
      aria-label={done ? "Terminé" : "En cours"}
      style={{
        opacity: 0,
        animation: `scan-point-appear 0.25s ease-out ${animateDelay}ms forwards`,
      }}
    >
      {done ? (
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[rgba(var(--success),0.2)] text-[rgb(var(--success))]">
          <Check className="h-3.5 w-3.5" strokeWidth={2.5} />
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
            <Check className="h-3.5 w-3.5" strokeWidth={2.5} />
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
  onAnimationComplete,
}: ScanLoaderProps) {
  const { t } = useLanguage();
  const useBoth =
    crawlMode === "both" &&
    (steps.some((s) => s.step.startsWith("html_")) ||
      steps.some((s) => s.step.startsWith("playwright_")));

  const connectors = useMemo(
    () => (useBoth ? computeConnectors(steps) : null),
    [useBoth, steps],
  );

  useEffect(() => {
    if (!onAnimationComplete) return;
    if (connectors) {
      const id = setTimeout(onAnimationComplete, connectors.totalDurationMs);
      return () => clearTimeout(id);
    }
    // Mode simple : pas d'animation à attendre, callback immédiat
    onAnimationComplete();
  }, [onAnimationComplete, connectors]);

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
            {connectors && (
              <>
                <svg
                  className="absolute left-1/2 top-0 z-0 -translate-x-1/2"
                  width={CIRCLE_AREA_WIDTH}
                  height={steps.length * ROW_STRIDE}
                  viewBox={`0 0 ${CIRCLE_AREA_WIDTH} ${steps.length * ROW_STRIDE}`}
                  preserveAspectRatio="xMinYMin meet"
                  aria-hidden="true"
                >
                  {connectors.segments.map((seg) => (
                    <AnimatedConnectorPath
                      key={seg.key}
                      d={seg.d}
                      done={seg.done}
                      segKey={seg.key}
                      delayMs={seg.delayMs}
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
                      column={getStepColumn(s.step, steps, i)}
                      index={i}
                      pointDelay={connectors.pointDelays[i] ?? 0}
                    />
                  ))}
                </ul>
              </>
            )}
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
