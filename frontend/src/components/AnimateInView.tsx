"use client";

import React, { useEffect, useState } from "react";
import { useInView } from "../hooks/useInView";

export interface AnimateInViewProps extends Omit<
  React.HTMLAttributes<HTMLElement>,
  "className"
> {
  children: React.ReactNode;
  /** Animer uniquement au montage (hero), sans observer le scroll. */
  initialOnly?: boolean;
  /** Délai en ms avant de considérer visible (pour initialOnly). */
  delay?: number;
  /** Classe(s) additionnelle(s). */
  className?: string;
  /** Élément HTML utilisé. */
  as?: "div" | "section" | "article" | "footer" | "li";
}

/**
 * Enveloppe du contenu pour animation d’apparition (bas → haut).
 * En mode scroll : devient visible quand l’élément entre dans le viewport.
 * En mode initialOnly : devient visible après le délai au chargement.
 */
export default function AnimateInView({
  children,
  initialOnly = false,
  delay = 0,
  className = "",
  as: Tag = "div",
  ...rest
}: AnimateInViewProps) {
  const [ref, isInView] = useInView({
    threshold: 0.05,
    rootMargin: "0px 0px 60px 0px",
    once: true,
  });
  const [initialVisible, setInitialVisible] = useState(false);

  useEffect(() => {
    if (!initialOnly) return;
    const t = setTimeout(() => setInitialVisible(true), delay);
    return () => clearTimeout(t);
  }, [initialOnly, delay]);

  const visible = initialOnly ? initialVisible : isInView;
  const baseClass = "landing-reveal";
  const visibleClass = visible ? "is-visible" : "";
  const combined = [baseClass, visibleClass, className]
    .filter(Boolean)
    .join(" ");

  return (
    <Tag ref={initialOnly ? undefined : ref} className={combined} {...rest}>
      {children}
    </Tag>
  );
}
