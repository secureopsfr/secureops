"use client";

import React from "react";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: "default" | "testimonial";
  onClick?: () => void;
  disableHover?: boolean;
  style?: React.CSSProperties;
}

/**
 * Composant de carte générique réutilisable.
 * Memoïsé pour éviter les re-renders inutiles lorsqu'il est rendu en boucle.
 */
const Card: React.FC<CardProps> = React.memo(
  ({
    children,
    className = "",
    variant = "default",
    onClick,
    disableHover = false,
    style,
  }) => {
    const baseClasses = "card";
    const variantClasses = variant === "testimonial" ? "testimonial" : "";
    const hoverClasses = disableHover ? "no-hover" : "";

    return (
      <div
        className={`${baseClasses} ${variantClasses} ${hoverClasses} ${className}`.trim()}
        onClick={onClick}
        style={{ ...(onClick ? { cursor: "pointer" } : {}), ...style }}
      >
        {children}
      </div>
    );
  },
);

Card.displayName = "Card";

export default Card;
