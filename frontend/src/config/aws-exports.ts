// Configuration AWS Cognito pour Amplify v6 (email / mot de passe uniquement).
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

if (!region || !userPoolId || !userPoolClientId) {
  logger.error("Variables d'environnement AWS Cognito manquantes:", {
    region: region || "NON DÉFINI",
    userPoolId: userPoolId || "NON DÉFINI",
    userPoolClientId: userPoolClientId || "NON DÉFINI",
  });
}

const awsmobile = {
  Auth: {
    Cognito: {
      region: region ?? "",
      userPoolId: userPoolId ?? "",
      userPoolClientId: userPoolClientId ?? "",
      loginMechanisms: ["email" as const],
    },
  },
};

export default awsmobile;
