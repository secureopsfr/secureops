"use client";

import { useEffect, useState } from "react";
import { getCurrentUser, fetchAuthSession } from "aws-amplify/auth";
import { User } from "lucide-react";
import { log } from "../../utils/logger";

/**
 * Affiche les informations de l'administrateur connecté (email Cognito, groupe).
 */
export default function AdminInfo() {
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    const loadUser = async () => {
      try {
        const user = await getCurrentUser();
        const session = await fetchAuthSession();
        const idToken = session.tokens?.idToken;

        if (idToken) {
          const payload = idToken.payload as Record<string, unknown>;
          const userEmail = (payload?.email as string) ?? user.username;
          setEmail(userEmail);
          log("[AdminInfo] Utilisateur:", userEmail);
        } else {
          setEmail(user.username);
        }
      } catch {
        // Silencieux — AdminGuard gère la redirection si pas connecté
      }
    };

    loadUser();
  }, []);

  if (!email) return null;

  return (
    <div className="flex items-center gap-2 text-sm text-[var(--muted)]">
      <User className="w-4 h-4" />
      <span>{email}</span>
    </div>
  );
}
