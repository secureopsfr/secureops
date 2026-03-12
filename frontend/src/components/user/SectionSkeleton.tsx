"use client";

import React from "react";
import Card from "../ui/cards/Card";

interface SectionSkeletonProps {
  id: string;
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  children: React.ReactNode;
  className?: string;
}

/**
 * Composant squelette pour toutes les sections de la page utilisateur
 * Fournit une structure commune avec icône, titre et contenu
 */
const SectionSkeleton: React.FC<SectionSkeletonProps> = ({
  id,
  icon: Icon,
  title,
  children,
  className = "",
}) => {
  return (
    <section id={id}>
      <Card className={className} disableHover>
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            gap: "0.75rem",
            marginBottom: "1.5rem",
          }}
        >
          {Icon && (
            <span style={{ flexShrink: 0 }}>
              <Icon className="w-6 h-6 text-[rgb(var(--primary))]" />
            </span>
          )}
          <h2
            className="text-2xl font-bold text-[rgb(var(--primary))]"
            style={{ margin: 0 }}
          >
            {title}
          </h2>
        </div>
        {children}
      </Card>
    </section>
  );
};

export default SectionSkeleton;
