"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { log } from "../../utils/logger";
import LoadingScreen from "../LoadingScreen";
import { useLanguage } from "../LanguageProvider";
import { useAuthUser } from "../../hooks/useAuthUser";

interface ScannerGuardProps {
  children: React.ReactNode;
}

/**
 * Garde d'accès pour la page Scanner.
 * Redirige vers la connexion (avec returnTo) si l'utilisateur n'est pas authentifié.
 */
export default function ScannerGuard({ children }: ScannerGuardProps) {
  const router = useRouter();
  const { t, lp } = useLanguage();
  const { user, isLoading: authLoading } = useAuthUser();

  useEffect(() => {
    if (authLoading) return;

    if (!user) {
      log(
        "[ScannerGuard] Utilisateur non authentifié, redirection vers /connexion",
      );
      router.push(
        `${lp("/connexion")}?returnTo=${encodeURIComponent(lp("/scanner"))}`,
      );
    }
  }, [authLoading, user, router, lp]);

  if (authLoading || !user) {
    return (
      <LoadingScreen variant="fullPage" message={t("scanner.checkingAccess")} />
    );
  }

  return <>{children}</>;
}
