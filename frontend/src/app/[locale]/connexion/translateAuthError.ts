/**
 * Traduit les erreurs d'authentification Cognito en messages utilisateur.
 */
export function translateAuthError(
  error: unknown,
  t: (key: string) => string,
): string {
  const errorMessage =
    error instanceof Error
      ? error.message
      : typeof error === "string"
        ? error
        : "";
  const errorLower = errorMessage.toLowerCase();

  if (
    errorLower.includes("incorrect username or password") ||
    errorLower.includes("invalid credentials")
  ) {
    return t("auth.errors.incorrectCredentials");
  }
  if (errorLower.includes("user does not exist")) {
    return t("auth.errors.userNotExist");
  }
  if (errorLower.includes("user is disabled")) {
    return t("auth.errors.userDisabled");
  }
  if (
    errorLower.includes("password attempts exceeded") ||
    errorLower.includes("attempt limit exceeded")
  ) {
    return t("auth.errors.attemptsExceeded");
  }
  if (
    errorLower.includes("already a signed in user") ||
    errorLower.includes("already signed in")
  ) {
    return t("auth.errors.alreadySignedIn");
  }
  if (errorLower.includes("network") || errorLower.includes("fetch")) {
    return t("auth.errors.networkError");
  }
  if (
    errorLower.includes("user is not confirmed") ||
    errorLower.includes("not confirmed") ||
    errorLower.includes("user not confirmed") ||
    errorLower.includes("confirmation required")
  ) {
    return t("auth.errors.accountNotConfirmed");
  }

  return errorMessage || t("auth.errors.defaultLoginError");
}
