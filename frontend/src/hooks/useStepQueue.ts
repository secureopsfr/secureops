/**
 * Hook de queue pour l'animation de révélation des steps de scan/crawl.
 *
 * Problème résolu : React 18 bache les functional updates setState dans une
 * même boucle synchrone. Si _check et _done arrivent dans le même batch de
 * polling, l'état "loading" n'est jamais rendu. Ce hook traite un step à la
 * fois avec un délai, garantissant que chaque _check est visible avant que
 * _done le remplace.
 *
 * Exception : les steps de progression de crawl (_crawl_progress) mettent à
 * jour une position existante — ils bypassent la queue pour ne pas accumuler
 * de retard quand le crawler émet de nombreux updates.
 */

import { useState, useCallback, useRef } from "react";
import type { ScanStep, ScanStepDisplay } from "../services/scanService";
import { updateStepsOnEvent } from "../utils/scanSteps";

const BYPASS_QUEUE_STEPS = new Set([
  "crawl_progress",
  "html_crawl_progress",
  "playwright_crawl_progress",
]);

export function useStepQueue(revealDelayMs = 120) {
  const [steps, setSteps] = useState<ScanStepDisplay[]>([]);
  const queueRef = useRef<ScanStep[]>([]);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const scheduleNext = useCallback(() => {
    if (queueRef.current.length === 0) {
      timerRef.current = null;
      return;
    }
    const next = queueRef.current.shift()!;
    setSteps((prev) => updateStepsOnEvent(prev, next));
    timerRef.current = setTimeout(scheduleNext, revealDelayMs);
    // revealDelayMs is a constant — no stale closure risk
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const enqueueStep = useCallback(
    (step: ScanStep) => {
      if (BYPASS_QUEUE_STEPS.has(step.step)) {
        setSteps((prev) => updateStepsOnEvent(prev, step));
        return;
      }
      queueRef.current.push(step);
      if (timerRef.current === null) {
        scheduleNext();
      }
    },
    [scheduleNext],
  );

  const resetSteps = useCallback(() => {
    queueRef.current = [];
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setSteps([]);
  }, []);

  return { steps, enqueueStep, resetSteps };
}
