// Configuration AWS Cognito pour Amplify v6
// Support des deux formats : NEXT_PUBLIC_AWS_* ou NEXT_PUBLIC_*
// Adapté pour Next.js

import logger from "../utils/logger";

const region =
  process.env.NEXT_PUBLIC_AWS_REGION || process.env.NEXT_PUBLIC_REGION;
const userPoolId =
  process.env.NEXT_PUBLIC_AWS_USER_POOL_ID ||
  process.env.NEXT_PUBLIC_USER_POOL_ID;
const userPoolClientId =
  process.env.NEXT_PUBLIC_AWS_CLIENT_ID || process.env.NEXT_PUBLIC_CLIENT_ID;

// Vérification que les variables sont définies
if (!region || !userPoolId || !userPoolClientId) {
  logger.error("Variables d'environnement AWS Cognito manquantes:", {
    region: region || "NON DÉFINI",
    userPoolId: userPoolId || "NON DÉFINI",
    userPoolClientId: userPoolClientId || "NON DÉFINI",
  });
}

// Construire les URLs de redirection de manière sûre
// Pour le développement, utiliser localhost par défaut
// En production, définir NEXT_PUBLIC_APP_URL dans les variables d'environnement
const getBaseUrl = () => {
  // Essayer d'abord les variables d'environnement
  if (process.env.NEXT_PUBLIC_APP_URL) {
    return process.env.NEXT_PUBLIC_APP_URL;
  }
  // En développement, utiliser localhost (sera mis à jour dynamiquement si nécessaire)
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  return "http://localhost:3000";
};

const baseUrl =
  typeof window !== "undefined" ? getBaseUrl() : "http://localhost:3000";
// Pour Amplify v6, rediriger vers la page d'accueil
// Amplify intercepte automatiquement le code OAuth dans l'URL et l'échange
const redirectSignIn = [`${baseUrl}/`];
const redirectSignOut = [`${baseUrl}/connexion`];

const awsmobile = {
  Auth: {
    Cognito: {
      region: region ?? "",
      userPoolId: userPoolId ?? "",
      userPoolClientId: userPoolClientId ?? "",
      loginMechanisms: ["email"],
      // Configuration OAuth pour SPA (sans client secret, avec PKCE)
      loginWith: {
        oauth: {
          domain:
            process.env.NEXT_PUBLIC_AWS_COGNITO_DOMAIN ||
            process.env.NEXT_PUBLIC_COGNITO_DOMAIN ||
            "",
          scopes: ["openid", "email", "profile"],
          redirectSignIn: redirectSignIn,
          redirectSignOut: redirectSignOut,
          responseType: "code" as const, // Authorization code flow avec PKCE
        },
      },
    },
  },
};

export default awsmobile;
