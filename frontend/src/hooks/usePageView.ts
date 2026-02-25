"use client";

/**
 * Hook React pour tracker automatiquement les pages vues et la durée de visite.
 *
 * Utilise le pathname Next.js pour détecter les changements de route et
 * envoie les événements via le service analyticsTracker.
 *
 * Événements émis :
 * - session_start : une seule fois par session (premier chargement)
 * - page_view : à chaque changement de route
 * - page_exit : quand l'utilisateur quitte la page (avec la durée)
 */

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import {
  initAnalytics,
  trackPageView,
  trackPageExit,
  trackSessionStart,
} from "../services/analyticsTracker";

export function usePageView(): void {
  const pathname = usePathname();
  const enteredAt = useRef<number>(0);
  const previousPage = useRef<string | null>(null);

  // Initialiser le tracker au premier rendu
  useEffect(() => {
    initAnalytics();
  }, []);

  useEffect(() => {
    // Si la page n'a pas changé, ne rien faire
    if (pathname === previousPage.current) return;

    const now = Date.now();

    // Envoyer page_exit pour la page précédente (si elle existe)
    if (previousPage.current !== null) {
      const duration = now - enteredAt.current;
      trackPageExit(previousPage.current, duration);
    }

    // Envoyer session_start (ne s'exécute qu'une seule fois par session)
    trackSessionStart(pathname);

    // Envoyer page_view pour la nouvelle page
    trackPageView(pathname);

    // Mettre à jour les refs
    previousPage.current = pathname;
    enteredAt.current = now;

    // Cleanup : envoyer page_exit quand le composant se démonte
    return () => {
      const exitDuration = Date.now() - enteredAt.current;
      trackPageExit(pathname, exitDuration);
    };
  }, [pathname]);
}
