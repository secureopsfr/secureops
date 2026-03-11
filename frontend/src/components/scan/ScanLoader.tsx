"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useLanguage } from "../LanguageProvider";
import { LoadingSpinner } from "../LoadingScreen";
import {
  AlertTriangle,
  Check,
  ChevronDown,
  ChevronUp,
  Minus,
} from "lucide-react";
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
  crawl_stopping_other_done: "scanner.crawlStoppingOtherDone",
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
  done: boolean,
  t: (key: string) => string,
): string {
  const key =
    step === "crawl_stopping_other" && done
      ? STEP_I18N_KEYS["crawl_stopping_other_done"]
      : STEP_I18N_KEYS[step];
  return key ? t(key) : message;
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
const ROW_GAP = 22;
/** Espace vertical supplémentaire après la séparation et avant la fusion. */
const SPLIT_MERGE_PADDING = 20;
const ROW_STRIDE = ROW_CONTENT + ROW_GAP;
const CIRCLE_SIZE = 28;
const CIRCLE_RADIUS = CIRCLE_SIZE / 2;

/** Y du centre du cercle pour la ligne i (layout fixe, fallback). */
function circleCenterY(row: number): number {
  return row * ROW_STRIDE + ROW_CONTENT / 2;
}

/**
 * Calcule les Y-centres de chaque cercle en tenant compte des hauteurs de lignes
 * variables (ex. panneau détails déplié). Le cercle est toujours dans les
 * ROW_CONTENT premiers pixels de sa ligne.
 */
function computeCircleYs(rowHeights: number[]): number[] {
  const ys: number[] = [];
  let y = 0;
  for (let i = 0; i < rowHeights.length; i++) {
    ys.push(y + ROW_CONTENT / 2);
    y += rowHeights[i] + ROW_GAP;
  }
  return ys;
}

/** Hauteur totale du SVG à partir des hauteurs de lignes. */
function totalSvgHeightFromRows(rowHeights: number[]): number {
  return (
    rowHeights.reduce((s, h) => s + h, 0) +
    Math.max(0, rowHeights.length - 1) * ROW_GAP
  );
}

interface ConnectorSegment {
  d: string;
  done: boolean;
  anomalyCount?: number;
  key: string;
  /** Délai (ms) avant de démarrer l'animation, pour respecter l'ordre par colonne. */
  delayMs: number;
  /** Couleur neutre pour le trait du crawler arrêté uniquement. */
  muted?: boolean;
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

  const approach1 = y0 < yMid ? yMid - radius : yMid + radius;
  const approach2 = y1 > yMid ? yMid + radius : yMid - radius;

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
const STEP_DURATION = 830;

/**
 * Calcule les paths SVG et les délais d'animation par colonne.
 * Chaque trait attend que le précédent dans la même colonne ait fini + point apparu.
 */
const POINT_ANIM_DURATION = 250;

function computeConnectors(
  steps: ScanStepDisplay[],
  circleYs?: number[],
): {
  segments: ConnectorSegment[];
  pointDelays: number[];
  totalDurationMs: number;
} {
  // Helpers locaux qui utilisent les positions Y dynamiques si fournies.
  const cy = (i: number) => (circleYs ? circleYs[i] : circleCenterY(i));
  const cby = (i: number) => cy(i) + CIRCLE_RADIUS;
  const cty = (i: number) => cy(i) - CIRCLE_RADIUS;

  const segments: ConnectorSegment[] = [];
  const pointDelays = new Array<number>(steps.length).fill(0);
  const cols = steps.map(
    (s, i) => COLUMN_INDEX[getStepColumn(s.step, steps, i)],
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
  const stoppingOtherCol = steps.findIndex(
    (s) => s.step === "crawl_stopping_other",
  );
  const mutedMergeHtml = stoppingOtherCol >= 0 && cols[stoppingOtherCol] === 0;
  const mutedMergePw = stoppingOtherCol >= 0 && cols[stoppingOtherCol] === 2;
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
        d: `M ${COL_CENTER_X[1]} ${cby(i)} V ${cty(i + 1)}`,
        done: steps[i].done ?? false,
        anomalyCount: steps[i + 1]?.anomaly_count ?? 0,
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
    const y0 = cby(splitAfter);
    const y1 = htmlRows[0] !== undefined ? cty(htmlRows[0]) : cty(pwRows[0]!);
    const y2 = pwRows[0] !== undefined ? cty(pwRows[0]) : y1;
    const yMidAvg = (y1 + y2) / 2;
    const ySplit = Math.min(y0 + SPLIT_MERGE_PADDING, (y0 + yMidAvg) / 2);

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
        anomalyCount: steps[htmlRows[0]]?.anomaly_count ?? 0,
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
        anomalyCount: steps[pwRows[0]]?.anomaly_count ?? 0,
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
      d: `M ${COL_CENTER_X[0]} ${cby(a)} V ${cty(b)}`,
      done: steps[a].done ?? false,
      anomalyCount: steps[b].anomaly_count ?? 0,
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
      d: `M ${COL_CENTER_X[2]} ${cby(a)} V ${cty(b)}`,
      done: steps[a].done ?? false,
      anomalyCount: steps[b].anomaly_count ?? 0,
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
    const yTarget = cty(mergeInto);
    const bottomHtml = lastHtml !== undefined ? cby(lastHtml) : yTarget;
    const bottomPw = lastPw !== undefined ? cby(lastPw) : yTarget;
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
        anomalyCount: steps[mergeInto]?.anomaly_count ?? 0,
        key: "merge-html",
        delayMs: mergeDelay,
        muted: mutedMergeHtml,
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
        anomalyCount: steps[mergeInto]?.anomaly_count ?? 0,
        key: "merge-pw",
        delayMs: mergeDelay,
        muted: mutedMergePw,
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
        d: `M ${COL_CENTER_X[1]} ${cby(i)} V ${cty(i + 1)}`,
        done: steps[i].done ?? false,
        anomalyCount: steps[i + 1]?.anomaly_count ?? 0,
        key: `seq-c-after-${i}`,
        delayMs: afterMergeDelay,
      });
      pointDelays[i + 1] = afterMergeDelay + POINT_APPEAR_DELAY;
      afterMergeDelay += STEP_DURATION;
    }
  }

  // Ordonnancement strict : trait -> point -> trait -> point.
  // On garde la géométrie des segments, mais on séquence leur timing globalement.
  segments.forEach((seg, index) => {
    seg.delayMs = index * STEP_DURATION;
  });
  pointDelays[0] = 0;
  for (let i = 1; i < pointDelays.length; i += 1) {
    pointDelays[i] = (i - 1) * STEP_DURATION + PATH_DRAW_DURATION;
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
  anomalyCount = 0,
  delayMs,
  muted = false,
}: {
  d: string;
  done: boolean;
  anomalyCount?: number;
  segKey: string;
  delayMs: number;
  muted?: boolean;
}) {
  const pathRef = useRef<SVGPathElement>(null);
  const [length, setLength] = useState<number | null>(null);

  useEffect(() => {
    const el = pathRef.current;
    if (el) {
      setLength(el.getTotalLength());
    }
  }, [d]);

  const strokeColor = muted
    ? "rgba(255, 255, 255, 0.18)"
    : done && anomalyCount > 0
      ? "rgb(var(--warning))"
      : done
        ? "rgb(var(--success))"
        : "rgba(var(--primary), 0.2)";

  if (length == null) {
    return (
      <path
        ref={pathRef}
        d={d}
        fill="none"
        stroke={strokeColor}
        strokeWidth="3"
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
      strokeWidth="3"
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
  anomalyCount: number;
  column: "html" | "common" | "playwright";
  index: number;
  pointDelay: number;
  isLatestStep: boolean;
  details?: string[];
  detailsExpanded?: boolean;
  onToggleDetails?: () => void;
  /** Appelé avec la hauteur (px) du panneau détails quand il change (0 = replié). */
  onDetailsHeightChange?: (height: number) => void;
}

function StepRow({
  step,
  message,
  done,
  anomalyCount,
  column,
  pointDelay,
  isLatestStep,
  details,
  detailsExpanded = false,
  onToggleDetails,
  onDetailsHeightChange,
}: StepRowProps) {
  const { t } = useLanguage();
  const msg = getDisplayMessage(step, message, done, t);
  const colIdx = COLUMN_INDEX[column];
  const isHtml = column === "html";
  const isRight = column === "common" || column === "playwright";
  const isStoppingOther = step === "crawl_stopping_other";
  const isAnomalous = done && anomalyCount > 0 && !isStoppingOther;
  const hasDetails = Boolean(details && details.length > 0 && onToggleDetails);

  // Panneau détails : ref pour mesure + auto-scroll
  const detailsRef = useRef<HTMLDivElement | null>(null);
  const [autoFollow, setAutoFollow] = useState(true);

  // Réinitialiser l'auto-scroll à l'ouverture
  useEffect(() => {
    if (detailsExpanded) setAutoFollow(true);
  }, [detailsExpanded]);

  // Auto-scroll vers le bas
  useEffect(() => {
    if (!detailsExpanded || !autoFollow) return;
    const el = detailsRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [detailsExpanded, details, autoFollow]);

  // Mesurer la hauteur du panneau et remonter au parent via callback
  useEffect(() => {
    if (!detailsExpanded) {
      onDetailsHeightChange?.(0);
      return;
    }
    const el = detailsRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      // offsetHeight du panneau + pt-3 (12px) déjà inclus dans le padding
      onDetailsHeightChange?.(el.offsetHeight);
    });
    ro.observe(el);
    // Mesure initiale
    onDetailsHeightChange?.(el.offsetHeight);
    return () => ro.disconnect();
  }, [detailsExpanded, onDetailsHeightChange]);

  return (
    <li className="flex min-w-0 flex-col" style={{ minHeight: ROW_CONTENT }}>
      {/* Ligne principale — hauteur fixe ROW_CONTENT */}
      <div
        className="flex min-w-0 items-center"
        style={{ height: ROW_CONTENT }}
      >
        {/* Zone gauche : message HTML */}
        <div className="flex min-w-0 flex-1 justify-end pr-3">
          {isHtml && (
            <span
              className={`text-base scan-animate-point whitespace-nowrap ${
                isLatestStep
                  ? "font-semibold text-[var(--text)]"
                  : isStoppingOther && done
                    ? "text-[rgba(255,255,255,0.3)]"
                    : isAnomalous
                      ? "font-medium text-[rgb(var(--warning))]"
                      : done
                        ? "text-muted-theme"
                        : "font-medium text-[var(--text)]"
              }`}
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
              <span
                className={`text-base whitespace-nowrap ${
                  isLatestStep
                    ? "font-semibold text-[var(--text)]"
                    : isStoppingOther && done
                      ? "text-[rgba(255,255,255,0.3)]"
                      : isAnomalous
                        ? "font-medium text-[rgb(var(--warning))]"
                        : done
                          ? "text-muted-theme"
                          : "font-medium text-[var(--text)]"
                }`}
              >
                {msg}
              </span>
              {hasDetails && (
                <div className="mt-1">
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 text-xs text-[rgb(var(--primary))] hover:underline"
                    onClick={onToggleDetails}
                  >
                    {detailsExpanded
                      ? "Masquer les détails"
                      : "Voir les détails"}
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

      {/* Panneau détails — dans le flux, aligné avec la zone texte droite */}
      {hasDetails && detailsExpanded && (
        <div className="flex min-w-0 items-start">
          {/* Miroir de la zone gauche */}
          <div className="flex-1" />
          {/* Miroir de la zone cercles */}
          <div className="shrink-0" style={{ width: CIRCLE_AREA_WIDTH }} />
          {/* Zone droite : panneau aligné avec le titre */}
          <div className="flex min-w-0 flex-1 pl-3">
            <div
              ref={detailsRef}
              className="w-full max-h-44 overflow-y-auto rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] pt-2 pb-2 px-3 shadow-lg"
              onWheel={() => setAutoFollow(false)}
              onTouchStart={() => setAutoFollow(false)}
              onPointerDown={() => setAutoFollow(false)}
            >
              <ul className="space-y-1 pr-1">
                {(details ?? []).map((detail, idx) => (
                  <li
                    key={`${step}-detail-${idx}`}
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

function StepCircle({
  done,
  animateDelay = 0,
  muted = false,
  anomalous = false,
}: {
  done: boolean;
  animateDelay?: number;
  muted?: boolean;
  anomalous?: boolean;
}) {
  const circleClass = muted
    ? "bg-[rgba(255,255,255,0.06)] border border-[rgba(255,255,255,0.14)]"
    : anomalous
      ? "bg-[rgba(var(--warning),0.22)] text-[rgb(var(--warning))]"
      : "bg-[rgba(var(--success),0.2)] text-[rgb(var(--success))]";
  return (
    <span
      className="flex h-6 w-6 shrink-0 items-center justify-center scan-animate-point"
      role="status"
      aria-label={
        muted
          ? "Arrete"
          : done
            ? anomalous
              ? "Anomalie detectee"
              : "Termine"
            : "En cours"
      }
      style={{
        opacity: 0,
        animation: `scan-point-appear 0.25s ease-out ${animateDelay}ms forwards`,
      }}
    >
      {done ? (
        <span
          className={`flex h-7 w-7 items-center justify-center rounded-full ${circleClass}`}
        >
          {muted ? (
            <Minus
              className="h-3.5 w-3.5 text-[rgba(255,255,255,0.35)]"
              strokeWidth={2.5}
            />
          ) : anomalous ? (
            <AlertTriangle className="h-4 w-4" strokeWidth={2.5} />
          ) : (
            <Check className="h-4 w-4" strokeWidth={2.5} />
          )}
        </span>
      ) : (
        <LoadingSpinner size="sm" />
      )}
    </span>
  );
}

const CIRCLE_AREA_WIDTH = COL_WIDTH * 3 + COL_GAP * 2;

/** Points de suspension animés (opacité en cascade). */
function AnimatedEllipsis() {
  return (
    <span className="inline-flex scan-loading-ellipsis" aria-hidden="true">
      <span>.</span>
      <span>.</span>
      <span>.</span>
    </span>
  );
}

function isMultiScanStep(step: string): boolean {
  return (
    step.startsWith("domain_") ||
    step.startsWith("page_scan_") ||
    step === "domain_checks_done" ||
    step === "multi_scan_done"
  );
}

interface TimelineStep extends ScanStepDisplay {
  details?: string[];
  groupKey?: "domain" | "pages";
}

function buildTimelineSteps(rawSteps: ScanStepDisplay[]): TimelineStep[] {
  const isMulti = rawSteps.some((s) => isMultiScanStep(s.step));
  if (!isMulti) return rawSteps;

  const timeline: TimelineStep[] = [
    {
      step: "multi_scan_init",
      message: "Initialisation du scan...",
      done: true,
    },
  ];
  let domainIdx = -1;
  let pagesIdx = -1;
  let hasMultiScanDone = false;
  let donePages = 0;
  let errorPages = 0;
  const pageStates = new Map<string, "done" | "error">();
  let totalPages: number | null = null;

  const pageStartRe = /^Analyse de (.+?) \((\d+)\/(\d+)\)/;
  const pageDoneRe = /^Page analysée : (.+)$/;
  const pageErrorRe = /^Page inaccessible : (.+)$/;
  const domainDoneMessageByStep: Record<string, string> = {
    domain_tls_check: "TLS/HTTPS vérifié.",
    domain_robots_check: "robots.txt vérifié.",
    domain_sitemap_check: "Sitemap vérifié.",
    domain_exposed_files_check: "Fichiers exposés vérifiés.",
    domain_directory_listing_check: "Directory listing vérifié.",
    domain_cors_check: "CORS (domaine) vérifié.",
  };
  const seenDomainChecks: string[] = [];

  const ensureDomainStep = (): number => {
    if (domainIdx >= 0) return domainIdx;
    timeline.push({
      step: "domain_parallel_group",
      message: "Vérifications domaine en parallèle...",
      done: false,
      details: [],
      groupKey: "domain",
    });
    domainIdx = timeline.length - 1;
    return domainIdx;
  };

  const ensurePagesStep = (): number => {
    if (pagesIdx >= 0) return pagesIdx;
    timeline.push({
      step: "pages_parallel_group",
      message: "Analyses des pages en parallèle...",
      done: false,
      details: [],
      groupKey: "pages",
    });
    pagesIdx = timeline.length - 1;
    return pagesIdx;
  };

  for (const step of rawSteps) {
    const msg = (step.message ?? "").trim();

    if (step.step.startsWith("domain_")) {
      const idx = ensureDomainStep();
      if (step.step === "domain_checks_done") {
        const doneDetails = seenDomainChecks.map(
          (k) => `✓ ${domainDoneMessageByStep[k] ?? "Vérification terminée."}`,
        );
        timeline[idx] = {
          ...timeline[idx],
          done: true,
          message: "Checks domaine terminés.",
          details: [...(timeline[idx].details ?? []), ...doneDetails],
        };
      } else if (msg) {
        if (
          step.step.endsWith("_check") &&
          !seenDomainChecks.includes(step.step)
        ) {
          seenDomainChecks.push(step.step);
        }
        timeline[idx].details = [...(timeline[idx].details ?? []), msg];
      }
      continue;
    }

    if (step.step.startsWith("page_scan_")) {
      const idx = ensurePagesStep();
      if (msg) {
        timeline[idx].details = [...(timeline[idx].details ?? []), msg];
      }

      const mStart = msg.match(pageStartRe);
      if (mStart) {
        const total = Number(mStart[3]);
        if (Number.isFinite(total) && total > 0) {
          totalPages = totalPages == null ? total : Math.max(totalPages, total);
        }
      } else {
        const mDone = msg.match(pageDoneRe);
        if (mDone?.[1]) {
          const url = mDone[1].trim();
          if (!pageStates.has(url)) {
            pageStates.set(url, "done");
            donePages += 1;
          }
        } else {
          const mError = msg.match(pageErrorRe);
          if (mError?.[1]) {
            const url = mError[1].trim();
            if (!pageStates.has(url)) {
              pageStates.set(url, "error");
              errorPages += 1;
            }
          }
        }
      }

      const total = totalPages ?? donePages + errorPages;
      timeline[idx] = {
        ...timeline[idx],
        message:
          total > 0
            ? `Analyses des pages en parallèle (${donePages + errorPages}/${total})...`
            : "Analyses des pages en parallèle...",
      };
      continue;
    }

    if (step.step === "multi_scan_done") {
      hasMultiScanDone = true;
      if (pagesIdx >= 0) {
        const total = totalPages ?? donePages + errorPages;
        timeline[pagesIdx] = {
          ...timeline[pagesIdx],
          done: true,
          message:
            total > 0
              ? `Analyses des pages terminées (${donePages + errorPages}/${total}).`
              : "Analyses des pages terminées.",
        };
      }
      timeline.push({
        ...step,
        done: true,
      });
      continue;
    }

    timeline.push(step);
  }

  if (hasMultiScanDone) {
    timeline.push({
      step: "multi_scan_results_compute",
      message: "Calcul des résultats...",
      done: true,
    });
  }

  return timeline;
}

export default function ScanLoader({
  steps,
  titleKey = "scanner.loading",
  crawlMode,
  onAnimationComplete,
}: ScanLoaderProps) {
  const { t } = useLanguage();
  const [showDomainDetails, setShowDomainDetails] = useState(false);
  const [showPagesDetails, setShowPagesDetails] = useState(false);
  /** Hauteurs mesurées (px) des panneaux détails, indexées par groupKey. */
  const [detailsHeights, setDetailsHeights] = useState<Record<string, number>>(
    {},
  );

  const timelineSteps = useMemo(() => buildTimelineSteps(steps), [steps]);
  const hasParallelBranches =
    crawlMode === "both" &&
    (timelineSteps.some((s) => s.step.startsWith("html_")) ||
      timelineSteps.some((s) => s.step.startsWith("playwright_")));

  /** Hauteur totale de chaque ligne = ROW_CONTENT + hauteur du panneau détails. */
  const rowHeights = useMemo(
    () =>
      timelineSteps.map(
        (s) =>
          ROW_CONTENT + (s.groupKey ? (detailsHeights[s.groupKey] ?? 0) : 0),
      ),
    [timelineSteps, detailsHeights],
  );

  /** Y-centres des cercles dans le repère SVG, tenant compte des lignes variables. */
  const circleYs = useMemo(() => computeCircleYs(rowHeights), [rowHeights]);

  /** Hauteur totale du SVG. */
  const svgHeight = useMemo(
    () => totalSvgHeightFromRows(rowHeights),
    [rowHeights],
  );

  const connectors = useMemo(
    () => computeConnectors(timelineSteps, circleYs),
    [timelineSteps, circleYs],
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
    <div className="flex w-full max-w-4xl flex-col items-center px-6 pb-10">
      {/* Titre fixe en haut — ne bouge pas quand les étapes s'ajoutent */}
      <h3 className="section-title shrink-0 text-center text-[1.65rem]">
        {t(titleKey).replace(/\.{3}$/, "")}
        <AnimatedEllipsis />
      </h3>

      {timelineSteps.length === 0 ? (
        <div className="mt-8 flex flex-col items-center gap-4">
          <LoadingSpinner size="md" />
          <span className="text-[1.05rem] text-muted-theme">
            {t(titleKey).replace(/\.{3}$/, "")}
            <AnimatedEllipsis />
          </span>
        </div>
      ) : (
        <div className="mt-8 mx-auto flex w-full max-w-4xl flex-col items-center">
          <div className="relative w-full" style={{ minHeight: svgHeight }}>
            {/* SVG dynamique : suit les hauteurs réelles des lignes */}
            <svg
              className="absolute left-1/2 top-0 z-0 -translate-x-1/2"
              width={CIRCLE_AREA_WIDTH}
              height={svgHeight}
              viewBox={`0 0 ${CIRCLE_AREA_WIDTH} ${svgHeight}`}
              preserveAspectRatio="xMinYMin meet"
              aria-hidden="true"
            >
              {connectors.segments.map((seg) => (
                <AnimatedConnectorPath
                  key={seg.key}
                  d={seg.d}
                  done={seg.done}
                  anomalyCount={seg.anomalyCount ?? 0}
                  segKey={seg.key}
                  delayMs={seg.delayMs}
                  muted={seg.muted}
                />
              ))}
            </svg>
            <ul className="relative flex flex-col" style={{ gap: ROW_GAP }}>
              {timelineSteps.map((s, i) => (
                <StepRow
                  key={`${s.step}-${i}`}
                  step={s.step}
                  message={s.message}
                  done={s.done ?? false}
                  anomalyCount={s.anomaly_count ?? 0}
                  column={
                    hasParallelBranches
                      ? getStepColumn(s.step, timelineSteps, i)
                      : "common"
                  }
                  index={i}
                  pointDelay={connectors.pointDelays[i] ?? 0}
                  isLatestStep={i === timelineSteps.length - 1}
                  details={s.details}
                  detailsExpanded={
                    s.groupKey === "domain"
                      ? showDomainDetails
                      : s.groupKey === "pages"
                        ? showPagesDetails
                        : false
                  }
                  onToggleDetails={
                    s.groupKey === "domain"
                      ? () => setShowDomainDetails((v) => !v)
                      : s.groupKey === "pages"
                        ? () => setShowPagesDetails((v) => !v)
                        : undefined
                  }
                  onDetailsHeightChange={
                    s.groupKey
                      ? (h) =>
                          setDetailsHeights((prev) => {
                            if (prev[s.groupKey!] === h) return prev;
                            return { ...prev, [s.groupKey!]: h };
                          })
                      : undefined
                  }
                />
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
