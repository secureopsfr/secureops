"""Exceptions personnalisées pour Admin Service."""


class AdminServiceError(Exception):
    """Erreur générique du Admin Service."""


class NotFoundError(AdminServiceError):
    """Erreur pour une ressource non trouvée."""


class ValidationError(AdminServiceError):
    """Erreur pour une validation métier invalide."""
