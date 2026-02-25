"""Service CRUD générique partagé entre tous les micro-services.

Ce module fournit une classe `CRUDService` générique qui servira
pour interagir avec la base de données de chaque service.
"""

from typing import Any, Dict, List, Optional


class CRUDService:
    """Service CRUD générique.

    Attributes:
        resource_name (str): nom logique de la ressource ciblée.
    """

    def __init__(self, resource_name: str) -> None:
        """Initialise le service CRUD.

        Args:
            resource_name (str): nom de la ressource.
        """
        self.resource_name = resource_name

    async def get_by_id(self, resource_id: Any) -> Optional[Dict[str, Any]]:
        """Récupère une ressource par identifiant.

        Args:
            resource_id (Any): identifiant unique de la ressource.

        Returns:
            Optional[Dict[str, Any]]: ressource trouvée ou None.
        """
        # À implémenter lors du branchement à la base de données
        return None

    async def list(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Liste les ressources selon des filtres.

        Args:
            filters (Optional[Dict[str, Any]]): filtres d'égalité simples.

        Returns:
            List[Dict[str, Any]]: liste des ressources.
        """
        # À implémenter lors du branchement à la base de données
        return []

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une ressource.

        Args:
            data (Dict[str, Any]): données de la ressource.

        Returns:
            Dict[str, Any]: ressource créée.
        """
        # À implémenter lors du branchement à la base de données
        return data

    async def update(self, resource_id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Met à jour une ressource.

        Args:
            resource_id (Any): identifiant unique de la ressource.
            data (Dict[str, Any]): nouvelles valeurs.

        Returns:
            Optional[Dict[str, Any]]: ressource mise à jour, sinon None.
        """
        # À implémenter lors du branchement à la base de données
        return None

    async def delete(self, resource_id: Any) -> bool:
        """Supprime une ressource.

        Args:
            resource_id (Any): identifiant unique de la ressource.

        Returns:
            bool: True si une ressource a été supprimée, sinon False.
        """
        # À implémenter lors du branchement à la base de données
        return False
