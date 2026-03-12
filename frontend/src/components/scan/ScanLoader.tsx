"use client";

import { useEffect, useMemo, useState } from "react";
import { useLanguage } from "../LanguageProvider";
import { LoadingSpinner } from "../LoadingScreen";
import type { ScanStepDisplay } from "../../services/scanService";
import {
  CIRCLE_AREA_WIDTH,
  ROW_CONTENT,
  ROW_GAP,
  computeCircleYs,
  computeConnectors,
  totalSvgHeightFromRows,
} from "./ScanLoaderGeometry";
import { buildTimelineSteps, getStepColumn } from "./ScanLoaderSteps";
import {
  AnimatedConnectorPath,
  AnimatedEllipsis,
} from "./ScanLoaderPrimitives";
import { StepRow } from "./ScanLoaderStepRow";

interface ScanLoaderProps {
  steps: ScanStepDisplay[];
  /** Clé i18n pour le titre (défaut: scanner.loading). */
  titleKey?: string;
  /** Mode both : affiche 3 colonnes avec ligne qui split/merge. */
  crawlMode?: "html" | "playwright" | "both";
  /** Appelé quand l'animation totale est terminée. */
  onAnimationComplete?: () => void;
}

export default function ScanLoader({
  steps,
  titleKey = "scanner.loading",
  crawlMode,
  onAnimationComplete,
}: ScanLoaderProps) {
  const { t } = useLanguage();
  const isCrawlerLoading =
    titleKey === "scanner.crawlLoading" || crawlMode !== undefined;
  const initialMessageKey = isCrawlerLoading
    ? "scanner.loadingInitCrawl"
    : "scanner.loadingInitScan";
  /** Hauteurs mesurées (px) des panneaux détails, indexées par step index. */
  const [detailsHeights, setDetailsHeights] = useState<Record<number, number>>(
    {},
  );

  const timelineSteps = useMemo(() => buildTimelineSteps(steps, t), [steps, t]);

  const hasParallelBranches =
    crawlMode === "both" &&
    (timelineSteps.some((s) => s.step.startsWith("html_")) ||
      timelineSteps.some((s) => s.step.startsWith("playwright_")));

  /** Hauteur totale de chaque ligne = ROW_CONTENT + hauteur du panneau détails. */
  const rowHeights = useMemo(
    () => timelineSteps.map((_, i) => ROW_CONTENT + (detailsHeights[i] ?? 0)),
    [timelineSteps, detailsHeights],
  );

  const circleYs = useMemo(() => computeCircleYs(rowHeights), [rowHeights]);
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
    onAnimationComplete();
  }, [onAnimationComplete, connectors]);

  return (
    <div className="flex w-full max-w-4xl flex-col items-center px-6 pb-10">
      <h3 className="section-title shrink-0 text-center text-[1.65rem]">
        {t(titleKey).replace(/\.{3}$/, "")}
        <AnimatedEllipsis />
      </h3>

      {timelineSteps.length === 0 ? (
        <div className="mt-8 flex flex-col items-center gap-4">
          <LoadingSpinner size="md" />
          <span className="text-[1.05rem] text-muted-theme">
            {t(initialMessageKey).replace(/\.{3}$/, "")}
            <AnimatedEllipsis />
          </span>
        </div>
      ) : (
        <div className="mt-8 mx-auto flex w-full max-w-4xl flex-col items-center">
          <div className="relative w-full" style={{ minHeight: svgHeight }}>
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
                  key={i}
                  step={s}
                  column={
                    hasParallelBranches
                      ? getStepColumn(s.step, timelineSteps, i)
                      : "common"
                  }
                  pointDelay={connectors.pointDelays[i] ?? 0}
                  isLatestStep={i === timelineSteps.length - 1}
                  onDetailsHeightChange={(h) =>
                    setDetailsHeights((prev) => {
                      if (prev[i] === h) return prev;
                      return { ...prev, [i]: h };
                    })
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
