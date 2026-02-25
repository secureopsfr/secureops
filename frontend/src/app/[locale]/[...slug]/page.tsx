import { notFound } from "next/navigation";

/**
 * Catch-all pour les chemins sous [locale] qui ne correspondent à aucune page.
 * Force l'affichage de [locale]/not-found.tsx (Header, Footer, 404 stylisé).
 */
export default function CatchAllNotFound() {
  notFound();
}
