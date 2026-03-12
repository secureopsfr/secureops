"use client";

import { useEffect, useRef } from "react";

const REVEAL_SELECTOR = ".doc-intro, .doc-toc, .doc-section";

/**
 * Anime l’apparition des blocs (.doc-intro, .doc-toc, .doc-section) au scroll,
 * comme pour la politique de confidentialité (landing-reveal).
 */
export function useDocBlockReveal(
  containerRef: React.RefObject<HTMLElement | null>,
  content: string | null,
) {
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !content) return;

    const blocks = container.querySelectorAll<HTMLElement>(REVEAL_SELECTOR);
    if (blocks.length === 0) return;

    blocks.forEach((el) => {
      el.classList.add("landing-reveal", "doc-reveal-block");
    });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            (entry.target as HTMLElement).classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.05, rootMargin: "0px 0px 60px 0px" },
    );

    observerRef.current = observer;
    blocks.forEach((el) => observer.observe(el));

    return () => {
      observer.disconnect();
      observerRef.current = null;
    };
  }, [containerRef, content]);
}
