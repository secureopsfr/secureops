"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { log } from "../../utils/logger";
import LoadingScreen from "../LoadingScreen";
import { useLanguage } from "../LanguageProvider";
import { useAuthUser } from "../../hooks/useAuthUser";

interface ScannerGuardProps {
  children: React.ReactNode;
}

/**
 * Garde d'accès pour les pages Scanner (scanner, docs, analyses, etc.).
 * Redirige vers la connexion (avec returnTo = page actuelle) si l'utilisateur
 * n'est pas authentifié. Réagit aussi à la déconnexion automatique (session expirée).
 */
export default function ScannerGuard({ children }: ScannerGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { t, lp } = useLanguage();
  const { user, isLoading: authLoading } = useAuthUser({
    listenToAuthEvents: true,
  });

  useEffect(() => {
    if (authLoading) return;

    if (!user) {
      const returnTo = pathname || lp("/scanner");
      log(
        "[ScannerGuard] Utilisateur non authentifié, redirection vers /connexion",
      );
      router.push(
        `${lp("/connexion")}?returnTo=${encodeURIComponent(returnTo)}`,
      );
    }
  }, [authLoading, user, router, lp, pathname]);

  if (authLoading || !user) {
    return (
      <LoadingScreen variant="fullPage" message={t("scanner.checkingAccess")} />
    );
  }

  return <>{children}</>;
}
