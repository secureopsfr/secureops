/**
 * Constantes de layout et calculs SVG pour ScanLoader.
 * Toute la logique géométrique (positions, paths, timings) est isolée ici.
 */

import type { ScanStepDisplay } from "../../services/scanService";
import { COLUMN_INDEX, getStepColumn } from "./ScanLoaderSteps";

// --- Constantes layout ---
export const COL_WIDTH = 48;
export const COL_GAP = 8;
export const COL_CENTER_X: [number, number, number] = [
  COL_WIDTH / 2,
  COL_WIDTH + COL_GAP + COL_WIDTH / 2,
  COL_WIDTH * 2 + COL_GAP * 2 + COL_WIDTH / 2,
];
export const ROW_CONTENT = 56;
export const ROW_GAP = 22;
/** Espace vertical supplémentaire après la séparation et avant la fusion. */
const SPLIT_MERGE_PADDING = 20;
export const ROW_STRIDE = ROW_CONTENT + ROW_GAP;
export const CIRCLE_SIZE = 28;
export const CIRCLE_RADIUS = CIRCLE_SIZE / 2;
export const CIRCLE_AREA_WIDTH = COL_WIDTH * 3 + COL_GAP * 2;

/** Rayon des coins split (vertical → branches). */
const CORNER_RADIUS = 18;
/** Rayon pour les courbes de merge. */
const MERGE_CORNER_RADIUS = 22;
/** Kappa pour approximation Bezier d'un arc circulaire (≈ 0.552). */
const KAPPA = 0.5522847498;

/** Délai avant apparition du point (ms) pour qu'il apparaisse à la fin de la ligne. */
export const POINT_APPEAR_DELAY = 380;
/** Durée d'un "pas" : trait + apparition du point (ms). */
export const STEP_DURATION = 830;
/** Durée de l'animation de dessin de la ligne (ms). */
export const PATH_DRAW_DURATION = 500;
const POINT_ANIM_DURATION = 250;

export interface ConnectorSegment {
  d: string;
  done: boolean;
  anomalyCount?: number;
  key: string;
  /** Délai (ms) avant de démarrer l'animation. */
  delayMs: number;
  /** Couleur neutre pour le trait du crawler arrêté uniquement. */
  muted?: boolean;
}

/** Y du centre du cercle pour la ligne i (layout fixe, fallback). */
export function circleCenterY(row: number): number {
  return row * ROW_STRIDE + ROW_CONTENT / 2;
}

/**
 * Calcule les Y-centres de chaque cercle en tenant compte des hauteurs de lignes
 * variables (ex. panneau détails déplié). Le cercle est toujours dans les
 * ROW_CONTENT premiers pixels de sa ligne.
 */
export function computeCircleYs(rowHeights: number[]): number[] {
  const ys: number[] = [];
  let y = 0;
  for (let i = 0; i < rowHeights.length; i++) {
    ys.push(y + ROW_CONTENT / 2);
    y += rowHeights[i] + ROW_GAP;
  }
  return ys;
}

/** Hauteur totale du SVG à partir des hauteurs de lignes. */
export function totalSvgHeightFromRows(rowHeights: number[]): number {
  return (
    rowHeights.reduce((s, h) => s + h, 0) +
    Math.max(0, rowHeights.length - 1) * ROW_GAP
  );
}

/**
 * Clamp du rayon pour éviter débordements.
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
export function pathWithRoundedCorners(
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

/**
 * Calcule les paths SVG et les délais d'animation par colonne.
 */
export function computeConnectors(
  steps: ScanStepDisplay[],
  circleYs?: number[],
): {
  segments: ConnectorSegment[];
  pointDelays: number[];
  totalDurationMs: number;
} {
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
    pointDelays[mergeInto] = mergeDelay + PATH_DRAW_DURATION;
  }

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

  // Ordonnancement strict global : trait -> point -> trait -> point.
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
