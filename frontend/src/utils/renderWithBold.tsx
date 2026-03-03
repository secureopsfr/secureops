/**
 * Utilitaire pour afficher du texte avec des mots clés en gras.
 * Convention : **mot** → <strong>mot</strong>
 */

import type { ReactNode } from "react";

/**
 * Parse une chaîne contenant des marqueurs **texte** et retourne un tableau
 * de nœuds React (texte brut ou <strong>).
 *
 * Args:
 *   text: Chaîne pouvant contenir **mot** pour mettre en gras.
 *
 * Returns:
 *   Tableau de ReactNode (string | JSX.Element) à afficher dans un fragment.
 */
export function renderWithBold(text: string): ReactNode[] {
  if (!text) return [];
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    const match = part.match(/^\*\*(.+)\*\*$/);
    if (match) {
      return <strong key={i}>{match[1]}</strong>;
    }
    return part;
  });
}
