"""Exceptions personnalisées pour le User Service."""


class UserServiceError(Exception):
    """Exception de base pour les erreurs du User Service."""

    pass


class UserNotFoundError(UserServiceError):
    """Exception levée quand un utilisateur n'est pas trouvé."""

    pass


class FederatedUserError(UserServiceError):
    """Exception levée pour les utilisateurs fédérés (Google, Facebook, etc.).

    Les utilisateurs fédérés n'ont pas de mot de passe stocké dans Cognito.
    """

    pass


class InvalidPasswordError(UserServiceError):
    """Exception levée quand le mot de passe est incorrect."""

    pass


class CognitoConfigurationError(UserServiceError):
    """Exception levée quand la configuration Cognito est incomplète."""

    pass
