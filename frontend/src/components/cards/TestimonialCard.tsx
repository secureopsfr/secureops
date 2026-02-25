import React from "react";
import Card from "./Card";

interface TestimonialCardProps {
  quote: string;
  author: string;
  className?: string;
}

/**
 * Composant de carte de témoignage réutilisable.
 * Memoïsé pour éviter les re-renders inutiles dans les listes (.map).
 */
const TestimonialCard: React.FC<TestimonialCardProps> = React.memo(
  ({ quote, author, className = "" }) => {
    return (
      <Card variant="testimonial" className={className}>
        <div className="testimonial">{quote}</div>
        <div className="author">{author}</div>
      </Card>
    );
  },
);

TestimonialCard.displayName = "TestimonialCard";

export default TestimonialCard;
