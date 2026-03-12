"use client";

import { getScoreBadge } from "./scanConstants";

interface ScoreChipProps {
  score: number;
}

/** Score badge couleur compact pour les onglets et les aperçus de page. */
export default function ScoreChip({ score }: ScoreChipProps) {
  const { ringColor, labelKey } = getScoreBadge(score);
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold text-white"
      style={{ background: ringColor }}
      title={labelKey}
    >
      {score}/100
    </span>
  );
}
