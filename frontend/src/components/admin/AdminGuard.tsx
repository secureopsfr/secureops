"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchAuthSession } from "aws-amplify/auth";
import { log, error } from "../../utils/logger";
import LoadingScreen from "../LoadingScreen";
import { useLanguage } from "../LanguageProvider";
import { useAuthUser } from "../../hooks/useAuthUser";

interface AdminGuardProps {
  children: React.ReactNode;
}

/**
 * Composant de protection pour les routes admin.
 * Vérifie que l'utilisateur est authentifié et appartient au groupe 'admin' dans Cognito.
 */
export default function AdminGuard({ children }: AdminGuardProps) {
  const router = useRouter();
  const { t, lp } = useLanguage();
  const { user, isLoading: authLoading } = useAuthUser();
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Wait until the auth hook finishes
    if (authLoading) return;

    // Not authenticated → redirect to login
    if (!user) {
      log(
        "[AdminGuard] Utilisateur non authentifié, redirection vers /connexion",
      );
      router.push(lp("/connexion"));
      setIsChecking(false);
      return;
    }

    // Authenticated → check admin group in the access token
    const checkAdminGroup = async () => {
      try {
        const session = await fetchAuthSession();
        const accessToken = session.tokens?.accessToken;

        if (!accessToken) {
          log("[AdminGuard] Pas de token d'accès disponible");
          router.push(lp("/connexion"));
          return;
        }

        let payload = accessToken.payload as Record<string, unknown>;
        const tokenWithDecode = accessToken as {
          decodePayload?: () => Record<string, unknown>;
        };
        if (typeof tokenWithDecode.decodePayload === "function") {
          payload = tokenWithDecode.decodePayload();
        }

        const groups = (payload?.["cognito:groups"] as string[]) || [];
        const isAdmin = Array.isArray(groups) && groups.includes("admin");

        if (isAdmin) {
          log("[AdminGuard] Utilisateur autorisé (admin)");
          setIsAuthorized(true);
        } else {
          log(
            "[AdminGuard] Utilisateur non autorisé (pas admin), redirection vers /",
          );
          router.push(lp("/"));
        }
      } catch (err) {
        error("[AdminGuard] Erreur lors de la vérification des groupes:", err);
        router.push(lp("/connexion"));
      } finally {
        setIsChecking(false);
      }
    };

    checkAdminGroup();
  }, [authLoading, user, router, lp]);

  // Afficher un loader pendant la vérification
  if (isChecking) {
    return (
      <LoadingScreen variant="fullPage" message={t("admin.checkingAccess")} />
    );
  }

  // Si autorisé, afficher le contenu
  if (isAuthorized) {
    return <>{children}</>;
  }

  // Sinon, ne rien afficher (la redirection est en cours)
  return null;
}
