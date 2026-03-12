/**
 * Utilitaires purs pour la gestion des steps de scan/crawl.
 */

import type { ScanStep, ScanStepDisplay } from "../services/scanService";

/**
 * Met à jour le tableau de steps en réponse à un event de step entrant.
 * - `_done` : remplace le dernier step (ou le step `_check` correspondant) par sa version done.
 * - `crawl_progress` / `html_crawl_progress` / `playwright_crawl_progress` : met à jour le step existant.
 * - `crawl_stopping_other` : remplace le dernier step de crawl_progress de la branche arrêtée.
 * - `crawl_merging` : marque crawl_stopping_other comme done et ajoute le step merging.
 * - Tous les autres : ajoute un nouveau step.
 */
export function updateStepsOnEvent(
  prev: ScanStepDisplay[],
  stepData: ScanStep,
): ScanStepDisplay[] {
  const step = stepData.step;
  const done = step.endsWith("_done");

  const isCrawlMerging = step === "crawl_merging";
  const isCrawlStoppingOther = step === "crawl_stopping_other";
  const isCrawlProgress =
    step === "crawl_progress" ||
    step === "html_crawl_progress" ||
    step === "playwright_crawl_progress";

  if (isCrawlStoppingOther && prev.length > 0) {
    const lastDone = prev.findLastIndex((s) =>
      ["crawl_html_done", "crawl_playwright_done"].includes(s.step),
    );
    const branchToReplace =
      lastDone >= 0 && prev[lastDone]?.step === "crawl_html_done"
        ? "playwright"
        : "html";
    const targetStep =
      branchToReplace === "playwright"
        ? "playwright_crawl_progress"
        : "html_crawl_progress";
    const idx = prev.findLastIndex((s) => s.step === targetStep);
    if (idx >= 0) {
      const updated = [...prev];
      updated[idx] = { ...stepData, done: false };
      return updated;
    }
  }

  if (isCrawlMerging && prev.length > 0) {
    const updated = [...prev];
    const stopIdx = updated.findLastIndex(
      (s) => s.step === "crawl_stopping_other",
    );
    if (stopIdx >= 0) {
      updated[stopIdx] = { ...updated[stopIdx], done: true };
    }
    return [...updated, { ...stepData, done: false }];
  }

  if (done && prev.length > 0) {
    const updated = [...prev];

    // Mapping explicite des steps _done vers leur step de progression correspondant.
    // Évite de dépendre d'une convention _check inexistante pour ces steps.
    const PROGRESS_REPLACEMENTS: Record<string, string> = {
      crawl_done: "crawl_progress",
      crawl_html_done: "html_crawl_progress",
      crawl_playwright_done: "playwright_crawl_progress",
    };
    const progressStep = PROGRESS_REPLACEMENTS[step];
    if (progressStep !== undefined) {
      const idx = updated.findLastIndex((s) => s.step === progressStep);
      if (idx >= 0) {
        updated[idx] = { ...stepData, done: true };
        return updated;
      }
    }

    const checkStep = step.replace("_done", "_check");
    const idx = updated.findLastIndex((s) => s.step === checkStep);
    if (idx >= 0) {
      updated[idx] = { ...stepData, done: true };
    } else {
      updated[updated.length - 1] = { ...stepData, done: true };
    }
    return updated;
  }

  if (isCrawlProgress && prev.length > 0) {
    const lastIdx = prev.findLastIndex((s) => s.step === step);
    if (lastIdx >= 0) {
      const updated = [...prev];
      updated[lastIdx] = { ...stepData, done: false };
      return updated;
    }
    // Le crawl est déjà terminé (crawl_html_done a remplacé html_crawl_progress) :
    // ignorer les updates de progression tardifs pour ne pas en rajouter après le done.
    const crawlAlreadyDone = prev.some(
      (s) =>
        s.step === "crawl_done" ||
        s.step === "crawl_html_done" ||
        s.step === "crawl_playwright_done",
    );
    if (crawlAlreadyDone) return prev;
  }

  return [...prev, { ...stepData, done: false }];
}
