"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, Check, Minus } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { LoadingSpinner } from "../LoadingScreen";
import { PATH_DRAW_DURATION } from "./ScanLoaderGeometry";

/** Points de suspension animés (opacité en cascade). */
export function AnimatedEllipsis() {
  return (
    <span className="inline-flex scan-loading-ellipsis" aria-hidden="true">
      <span>.</span>
      <span>.</span>
      <span>.</span>
    </span>
  );
}

export function StepCircle({
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
  const { t } = useLanguage();
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
          ? t("scanner.ariaStopped")
          : done
            ? anomalous
              ? t("scanner.ariaFindingDetected")
              : t("scanner.ariaDone")
            : t("scanner.ariaInProgress")
      }
      style={{
        opacity: 0,
        animation: `scan-point-appear 0.25s ease-out ${animateDelay}ms forwards`,
      }}
    >
      {done ? (
        <span
          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${circleClass}`}
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

export function AnimatedConnectorPath({
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
