"use client";

import React, { useEffect, useState } from "react";
import { useVisibleSection } from "../hooks/useVisibleSection";

interface Section {
  id: string;
  title: string;
}

interface TableOfContentsProps {
  sections: Section[];
  onSectionClick?: (sectionId: string) => void;
  isSectionAvailable?: (section: Section) => boolean;
  getUnavailableTooltip?: (sectionId: string) => string | null;
  containerId?: string;
  title?: string;
  className?: string;
}

/**
 * Composant réutilisable pour afficher un sommaire/table des matières
 */
const TableOfContents: React.FC<TableOfContentsProps> = ({
  sections,
  onSectionClick,
  isSectionAvailable = () => true,
  getUnavailableTooltip = () => null,
  containerId = "sections-container",
  title = "Sommaire",
  className = "",
}) => {
  const [highlightSection, setHighlightSection] = useState<string | null>(null);

  // Toutes les sections avec leur statut de disponibilité
  const sectionsWithStatus = sections.map((section) => ({
    ...section,
    isAvailable: isSectionAvailable(section),
  }));

  // Extraire les IDs des sections disponibles pour la détection de visibilité
  const availableSectionIds = sectionsWithStatus
    .filter((section) => section.isAvailable)
    .map((section) => section.id);

  // Utiliser le hook personnalisé pour détecter la section visible, avec priorité à la section forcée
  const visibleSection = useVisibleSection(availableSectionIds, {
    forcedSection: highlightSection,
    containerId,
  });

  /**
   * Gère le clic sur une section du sommaire avec scroll smooth
   */
  const handleSectionClick = (sectionId: string, isAvailable: boolean) => {
    // Ne pas permettre le clic sur les sections non disponibles
    if (!isAvailable) {
      return;
    }

    // Mise à jour immédiate de la surbrillance pour réactivité
    setHighlightSection(sectionId);

    const sectionElement = document.getElementById(sectionId);
    const container = document.getElementById(containerId);

    if (sectionElement && container) {
      // Calculer la position de la section par rapport au conteneur
      const sectionTop = sectionElement.offsetTop;
      const offset = 10; // Petit offset pour ne pas coller au bord
      const targetTop = sectionTop - offset;

      // Scroll smooth vers la section
      container.scrollTo({
        top: targetTop,
        behavior: "smooth",
      });
    }

    // Appeler la fonction de callback si fournie
    if (onSectionClick) {
      onSectionClick(sectionId);
    }
  };

  // Si l'observer confirme la même section que la surbrillance, on libère tout de suite
  useEffect(() => {
    if (highlightSection && visibleSection === highlightSection) {
      setHighlightSection(null);
    }
  }, [visibleSection, highlightSection]);

  return (
    <div className={`relative ${className}`} style={{ padding: "24px" }}>
      {title && (
        <h2
          className="text-xl font-semibold mb-4"
          style={{ color: "var(--color-text)", fontWeight: 600 }}
        >
          {title}
        </h2>
      )}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "12px",
          alignItems: "flex-start",
        }}
      >
        {sectionsWithStatus.map((section, index) => {
          const isVisible = (highlightSection || visibleSection) === section.id;
          const isAvailable = section.isAvailable;

          return (
            <button
              key={index}
              className={`group relative text-left transition-all duration-200 font-medium ${
                isAvailable ? "cursor-pointer" : "cursor-not-allowed"
              }`}
              style={{
                display: "block",
                width: "100%",
                padding: "8px 0",
                backgroundColor: "transparent",
                border: "none",
                outline: "none",
                fontSize: "16px",
                textAlign: "left",
                color: isVisible
                  ? "rgb(var(--primary))"
                  : isAvailable
                    ? "var(--color-toc-text)"
                    : "var(--color-toc-text-disabled)",
              }}
              onClick={() => handleSectionClick(section.id, isAvailable)}
              disabled={!isAvailable}
            >
              <span className="font-semibold">{section.title}</span>
              {!isAvailable && (
                <span
                  className="ml-2 text-xs"
                  style={{ color: "var(--color-toc-text-disabled)" }}
                >
                  (Non disponible)
                </span>
              )}
              {!isAvailable && getUnavailableTooltip(section.id) && (
                <div
                  className="pointer-events-none absolute left-full top-1/2 ml-3 hidden -translate-y-1/2 whitespace-normal rounded-lg px-6 py-4 text-base font-normal shadow-2xl shadow-black/30 group-hover:flex z-30 w-[350px]"
                  style={{
                    backgroundColor: "var(--color-tooltip-bg)",
                    border: "1px solid var(--color-border)",
                    color: "var(--color-text)",
                  }}
                  role="tooltip"
                >
                  {getUnavailableTooltip(section.id)}
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default TableOfContents;
