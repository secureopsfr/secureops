"use client";

import { useEffect, useRef, useState } from "react";

export interface UseInViewOptions {
  /** Seuil d’intersection (0–1). Défaut : 0.1 */
  threshold?: number;
  /** Racine du viewport (null = viewport). */
  root?: Element | null;
  /** Marge autour du root (ex. "100px"). */
  rootMargin?: string;
  /** Ne déclencher qu’une fois (ne plus observer après visibilité). */
  once?: boolean;
}

/**
 * Détecte si un élément est visible dans le viewport via IntersectionObserver.
 *
 * Args:
 *   options - Seuil, root, rootMargin, once.
 *
 * Returns:
 *   [ref, isInView] - Ref à attacher au nœud, et état de visibilité.
 */
export function useInView(
  options: UseInViewOptions = {},
): [(node: HTMLElement | null) => void, boolean] {
  const {
    threshold = 0.1,
    root = null,
    rootMargin = "0px",
    once = true,
  } = options;

  const [isInView, setIsInView] = useState(false);
  const ref = useRef<HTMLElement | null>(null);
  const setRef = (node: HTMLElement | null) => {
    ref.current = node;
  };

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (!entry) return;
        if (entry.isIntersecting) {
          setIsInView(true);
          if (once) observer.unobserve(entry.target);
        } else if (!once) {
          setIsInView(false);
        }
      },
      { threshold, root, rootMargin },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold, root, rootMargin, once]);

  return [setRef, isInView];
}
