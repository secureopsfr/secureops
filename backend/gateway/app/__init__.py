"""Service Gateway pour l'application Immosphere.

Ce package implémente l'API Gateway qui sert de point d'entrée unique
pour toutes les requêtes vers les différents microservices du système.
Il contient également des mocks pour faciliter les tests.
"""

from unittest.mock import MagicMock

mock_response = MagicMock()
mock_response.content = b"test content"
mock_response.status_code = 200
mock_response.headers = {"Content-Type": "application/json"}
