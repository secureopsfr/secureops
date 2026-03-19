"use client";

/**
 * Affiche les vrais résultats de scan floutés en arrière-plan du gate.
 * Utilise la même structure que ScanResults (ScanResultHeroCard + ScanSummarySection)
 * pour que l'aperçu ait exactement la même forme que la page de résultats réelle.
 */

import { useLanguage } from "../LanguageProvider";
import ScanResultHeroCard from "./ScanResultHeroCard";
import ScanSummarySection from "./ScanSummarySection";
import { severitySort } from "./scanConstants";
import type { ScanResult } from "../../services/scanService";

interface FakeScanResultsBlurredProps {
  /** Résultat réel du scan (pour afficher la même structure avec les vraies données). */
  result: ScanResult;
}

export default function FakeScanResultsBlurred({
  result,
}: FakeScanResultsBlurredProps) {
  const { t } = useLanguage();
  const sortedFindings = [...result.findings].sort(severitySort);

  return (
    <div
      className="space-y-6 select-none pointer-events-none"
      style={{
        filter: "blur(8px)",
        opacity: 0.85,
        userSelect: "none",
      }}
      aria-hidden
    >
      <ScanResultHeroCard
        url={result.url}
        score={result.score}
        findings={sortedFindings}
        durationSeconds={result.duration}
      />
      <ScanSummarySection
        findings={result.findings}
        category_summaries={result.category_summaries}
        total_tests_count={result.total_tests_count}
        animate={false}
      />
    </div>
  );
}
