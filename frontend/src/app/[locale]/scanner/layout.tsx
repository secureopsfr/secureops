"use client";

import ScannerGuard from "../../../components/scan/ScannerGuard";

/**
 * Layout de la page Scanner : accès réservé aux utilisateurs connectés.
 * Redirige vers /connexion?returnTo=/scanner si non authentifié.
 */
export default function ScannerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ScannerGuard>{children}</ScannerGuard>;
}
