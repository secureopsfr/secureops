"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { log } from "../../utils/logger";
import LoadingScreen from "../LoadingScreen";
import { useLanguage } from "../LanguageProvider";
import { useAuthUser } from "../../hooks/useAuthUser";

interface AuthGuardProps {
  children: React.ReactNode;
  /** Message affiché pendant la vérification de l'authentification. */
  loadingMessageKey?: string;
}

/**
 * Garde d'accès générique : redirige vers la connexion si l'utilisateur n'est pas authentifié.
 * Utilisé pour mon-compte et autres pages protégées.
 * Réagit à la déconnexion automatique (session expirée) via listenToAuthEvents.
 */
export default function AuthGuard({
  children,
  loadingMessageKey = "common.loading",
}: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { t, lp } = useLanguage();
  const { user, isLoading: authLoading } = useAuthUser({
    listenToAuthEvents: true,
  });

  useEffect(() => {
    if (authLoading) return;

    if (!user) {
      const returnTo = pathname || lp("/");
      log(
        "[AuthGuard] Utilisateur non authentifié, redirection vers /connexion",
      );
      router.push(
        `${lp("/connexion")}?returnTo=${encodeURIComponent(returnTo)}`,
      );
    }
  }, [authLoading, user, router, lp, pathname]);

  if (authLoading || !user) {
    return <LoadingScreen variant="fullPage" message={t(loadingMessageKey)} />;
  }

  return <>{children}</>;
}
