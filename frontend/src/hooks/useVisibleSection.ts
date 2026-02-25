import { useState, useEffect, useRef, useCallback } from "react";

interface UseVisibleSectionOptions {
  forcedSection?: string | null;
  containerId?: string;
}

/**
 * Hook personnalisé pour détecter la section visible à l'écran
 */
export function useVisibleSection(
  sectionIds: string[],
  options: UseVisibleSectionOptions = {},
): string | null {
  const { forcedSection, containerId = "sections-container" } = options;
  const [visibleSection, setVisibleSection] = useState<string | null>(
    forcedSection || null,
  );
  const observerRef = useRef<IntersectionObserver | null>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastUpdateTimeRef = useRef(0);
  const isScrollingRef = useRef(false);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const sectionRatiosRef = useRef(new Map<string, number>());

  // Fonction pour mettre à jour la section visible avec debounce amélioré
  const updateVisibleSection = useCallback(
    (newSection: string | null) => {
      // Ignorer les mises à jour si une section forcée est active
      if (forcedSection) return;
      const now = Date.now();
      const timeSinceLastUpdate = now - lastUpdateTimeRef.current;

      // Si on est en train de scroller et que le changement est trop rapide, ignorer
      if (isScrollingRef.current && timeSinceLastUpdate < 50) {
        return;
      }

      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }

      debounceTimeoutRef.current = setTimeout(() => {
        setVisibleSection(newSection);
        lastUpdateTimeRef.current = Date.now();
      }, 120);
    },
    [forcedSection],
  );

  // Commit immédiat sans debounce (utilisé en fin de scroll ou forte confiance)
  const commitVisibleSection = useCallback((newSection: string | null) => {
    setVisibleSection(newSection);
    lastUpdateTimeRef.current = Date.now();
  }, []);

  // Détecter le scroll
  useEffect(() => {
    const container = document.getElementById(containerId);
    if (!container) return;

    const handleScroll = () => {
      isScrollingRef.current = true;

      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }

      // Marquer la fin du scroll après 300ms d'inactivité
      scrollTimeoutRef.current = setTimeout(() => {
        isScrollingRef.current = false;
        // À la fin du scroll, choisir immédiatement la section la plus visible
        let bestSectionId: string | null = null;
        let bestRatio = 0;
        sectionRatiosRef.current.forEach((ratio, sectionId) => {
          if (ratio > bestRatio) {
            bestRatio = ratio;
            bestSectionId = sectionId;
          }
        });
        if (
          !forcedSection &&
          bestSectionId &&
          bestSectionId !== visibleSection
        ) {
          commitVisibleSection(bestSectionId);
        }
      }, 100);
    };

    container.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      container.removeEventListener("scroll", handleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [containerId, forcedSection, visibleSection, commitVisibleSection]);

  useEffect(() => {
    // Attendre que le DOM soit prêt
    const initObserver = () => {
      const container = document.getElementById(containerId);
      if (!container) {
        // Retry après un court délai si le conteneur n'est pas encore disponible
        setTimeout(initObserver, 100);
        return;
      }

      // Configuration de l'Intersection Observer
      const observerOptions = {
        root: container,
        rootMargin: "-15% 0px -65% 0px", // Considère visible si 15% en haut et 65% en bas
        threshold: [0, 0.1, 0.5, 1], // Plusieurs seuils pour une détection plus précise
      };

      // Map pour stocker les ratios d'intersection de chaque section
      const sectionRatios = new Map<string, number>();

      const handleIntersection = (entries: IntersectionObserverEntry[]) => {
        // Suspendre les mises à jour si une section est forcée
        if (forcedSection) return;
        entries.forEach((entry) => {
          const sectionId = entry.target.id;
          const ratio = entry.intersectionRatio;
          sectionRatios.set(sectionId, ratio);
          sectionRatiosRef.current.set(sectionId, ratio);
        });

        // Trouve la section avec le plus grand ratio d'intersection
        let maxRatio = 0;
        let mostVisibleSection: string | null = null;

        const dynamicThreshold = isScrollingRef.current ? 0.5 : 0.1;
        sectionRatios.forEach((ratio, sectionId) => {
          if (ratio > maxRatio && ratio > dynamicThreshold) {
            // Seuil minimum dynamique (plus strict pendant le scroll)
            maxRatio = ratio;
            mostVisibleSection = sectionId;
          }
        });

        // Met à jour la section visible seulement si elle a changé
        if (mostVisibleSection && mostVisibleSection !== visibleSection) {
          // Pendant le scroll, ne valider immédiatement que si le ratio est très fort
          if (isScrollingRef.current) {
            if (maxRatio >= 0.65) {
              commitVisibleSection(mostVisibleSection);
            }
            // Sinon on attend la fin du scroll pour valider la meilleure section
          } else {
            updateVisibleSection(mostVisibleSection);
          }
        }
      };

      // Créer l'observer
      observerRef.current = new IntersectionObserver(
        handleIntersection,
        observerOptions,
      );

      // Observer toutes les sections
      sectionIds.forEach((sectionId) => {
        const element = document.getElementById(sectionId);
        if (element) {
          observerRef.current?.observe(element);
        }
      });
    };

    initObserver();

    // Cleanup
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [
    sectionIds,
    containerId,
    visibleSection,
    updateVisibleSection,
    commitVisibleSection,
    forcedSection,
  ]);

  // Si une section forcée est définie, la retourner en priorité
  return forcedSection ?? visibleSection;
}
