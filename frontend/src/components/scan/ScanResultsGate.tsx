"use client";

import { LogIn } from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import { GenericButton } from "../buttons";

interface ScanResultsGateProps {
  /** URL de redirection vers la page de connexion (avec returnTo si supporté). */
  signInHref: string;
}

/**
 * Contenu du popup affiché quand le scan est terminé mais l'utilisateur n'est pas connecté.
 * Invite à se connecter pour accéder aux résultats et à l'export.
 */
export default function ScanResultsGate({ signInHref }: ScanResultsGateProps) {
  const { t } = useLanguage();

  return (
    <div className="flex flex-col items-center gap-4 text-center">
      <p className="text-muted-theme text-sm max-w-md">
        {t("scanner.gateDesc")}
      </p>
      <p className="text-muted-theme text-xs max-w-md">
        {t("scanner.gateHistoryDesc")}
      </p>
      <GenericButton
        label={t("scanner.gateCta")}
        href={signInHref}
        variant="primary"
        icon={<LogIn className="w-4 h-4" />}
        iconPosition="left"
      />
    </div>
  );
}
