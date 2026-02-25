import React from "react";
import Card from "./Card";

interface FeatureCardProps {
  title: string;
  body: string;
  className?: string;
  icon?: React.ReactNode;
}

/**
 * Composant de carte de fonctionnalité réutilisable.
 * Memoïsé pour éviter les re-renders inutiles dans les listes (.map).
 */
const FeatureCard: React.FC<FeatureCardProps> = React.memo(
  ({ title, body, className = "", icon }) => {
    return (
      <Card className={className}>
        {icon && <div className="mb-3">{icon}</div>}
        <h3
          className="text-xl font-semibold mb-2"
          style={{ color: "var(--text)" }}
        >
          {title}
        </h3>
        <p style={{ color: "var(--muted)" }}>{body}</p>
      </Card>
    );
  },
);

FeatureCard.displayName = "FeatureCard";

export default FeatureCard;
