"""Utilitaires liés à l'environnement (prod/dev).

La variable IS_PROD est utilisée par les services pour distinguer
prod (localhost/IP privées bloquées, ports restreints) du mode dev
(localhost autorisé pour les tests locaux).
"""

import os


def is_prod_env() -> bool:
    """Indique si l'environnement est en mode production.

    La variable d'environnement IS_PROD est considérée vraie si elle vaut
    "1", "true" ou "yes" (insensible à la casse). Si elle est absente,
    le comportement par défaut est conservateur (prod).

    Returns:
        bool: True si l'environnement est considéré comme production.
    """
    value = os.getenv("IS_PROD", "true").lower().strip()
    return value in ("1", "true", "yes")
