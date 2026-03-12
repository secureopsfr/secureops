"use client";

import React from "react";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  variant?: "default" | "testimonial";
  disableHover?: boolean;
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
    ...rest
  }) => {
    const baseClasses = "card";
    const variantClasses = variant === "testimonial" ? "testimonial" : "";
    const hoverClasses = disableHover ? "no-hover" : "";

    return (
      <div
        className={`${baseClasses} ${variantClasses} ${hoverClasses} ${className}`.trim()}
        onClick={onClick}
        style={{ ...(onClick ? { cursor: "pointer" } : {}), ...style }}
        {...rest}
      >
        {children}
      </div>
    );
  },
);

Card.displayName = "Card";

export default Card;
