"""Schémas Pydantic pour les métriques de performance."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class PerformanceMetricCreate(BaseModel):
    """Requête de création d'une métrique de performance."""

    service_prefix: str = Field(..., description="Préfixe du service (ex: admin, user, scan)")
    endpoint: str = Field(..., description="Chemin complet de l'endpoint côté gateway")
    route: Optional[str] = Field(None, description="Route de base sans paramètres ni valeurs numériques (ex: /analytics-query/dvf/bbox-sales)")
    method: str = Field(..., description="Méthode HTTP utilisée")
    status_code: int = Field(..., ge=100, le=599, description="Code HTTP retourné")
    duration_ms: float = Field(..., ge=0, description="Durée de traitement en millisecondes")
    success: bool = Field(..., description="Indique si la requête est considérée comme un succès")
    observed_at: Optional[datetime] = Field(None, description="Horodatage de l'observation (UTC)")
    client_ip_hash: Optional[str] = Field(None, description="Adresse IP du client pseudonymisée via HMAC-SHA256 pour RGPD")
    request_params: Optional[Dict[str, Any]] = Field(None, description="Paramètres de la requête (query/body résumés)")
    user_id_hash: Optional[str] = Field(
        None, alias="userIdHash", serialization_alias="userIdHash", description="Identifiant utilisateur pseudonymisé (HMAC)"
    )
    request_size_bytes: Optional[int] = Field(None, description="Taille de la requête envoyée en octets (pour corrélation taille/latence)")
    response_size_bytes: Optional[int] = Field(None, description="Taille de la réponse reçue en octets (pour métriques de volumétrie)")
    request_size_kb: Optional[float] = Field(None, description="Taille de la requête envoyée en kilooctets (calculée automatiquement)")
    response_size_kb: Optional[float] = Field(None, description="Taille de la réponse reçue en kilooctets (calculée automatiquement)")

    model_config = ConfigDict(populate_by_name=True)


class PerformanceMetricResponse(BaseModel):
    """Réponse retournée après l'enregistrement d'une métrique."""

    success: bool = Field(True, description="Indique si l'opération a réussi")
    metric_id: str = Field(..., description="Identifiant unique de la métrique enregistrée")
    created_at: datetime = Field(..., description="Horodatage de création en base")


class PerformanceMetricSummary(BaseModel):
    """Résumé agrégé des métriques pour une route."""

    route: str = Field(..., description="Route agrégée sans paramètres (ex: /analytics-query/dvf/bbox-sales)")
    method: Optional[str] = Field(None, description="Méthode HTTP (présente uniquement si le regroupement par méthode est activé)")
    count: int = Field(..., description="Nombre de requêtes agrégées")
    success_rate: float = Field(..., serialization_alias="successRate", description="Taux de succès entre 0 et 1")
    client_error_rate: float = Field(0.0, serialization_alias="clientErrorRate", description="Taux d'erreurs 4xx entre 0 et 1")
    server_error_rate: float = Field(0.0, serialization_alias="serverErrorRate", description="Taux d'erreurs 5xx entre 0 et 1")
    timeout_rate: float = Field(0.0, serialization_alias="timeoutRate", description="Taux de timeouts (504) entre 0 et 1")
    avg_ms: float | None = Field(None, serialization_alias="avgMs", description="Durée moyenne en millisecondes")
    p5_ms: float | None = Field(None, serialization_alias="p5Ms", description="5ᵉ percentile en millisecondes")
    p95_ms: float | None = Field(None, serialization_alias="p95Ms", description="95ᵉ percentile en millisecondes")
    median_ms: float | None = Field(None, serialization_alias="medianMs", description="Médiane (ms)")
    min_ms: float | None = Field(None, serialization_alias="minMs", description="Durée minimale en millisecondes")
    max_ms: float | None = Field(None, serialization_alias="maxMs", description="Durée maximale en millisecondes")
    variance_ms2: float | None = Field(None, serialization_alias="varianceMs2", description="Variance (ms²)")
    std_ms: float | None = Field(None, serialization_alias="stdMs", description="Écart-type (ms)")
    avg_request_size_kb: float | None = Field(None, serialization_alias="avgRequestSizeKb", description="Taille moyenne des requêtes en kilooctets")
    p5_request_size_kb: float | None = Field(
        None, serialization_alias="p5RequestSizeKb", description="5ᵉ percentile des tailles de requêtes en kilooctets"
    )
    median_request_size_kb: float | None = Field(
        None, serialization_alias="medianRequestSizeKb", description="Médiane des tailles de requêtes en kilooctets"
    )
    p95_request_size_kb: float | None = Field(
        None, serialization_alias="p95RequestSizeKb", description="95ᵉ percentile des tailles de requêtes en kilooctets"
    )
    min_request_size_kb: float | None = Field(None, serialization_alias="minRequestSizeKb", description="Taille minimale des requêtes en kilooctets")
    max_request_size_kb: float | None = Field(None, serialization_alias="maxRequestSizeKb", description="Taille maximale des requêtes en kilooctets")
    variance_request_size_kb: float | None = Field(
        None, serialization_alias="varianceRequestSizeKb", description="Variance des tailles de requêtes en kilooctets²"
    )
    std_request_size_kb: float | None = Field(
        None, serialization_alias="stdRequestSizeKb", description="Écart-type des tailles de requêtes en kilooctets"
    )
    avg_response_size_kb: float | None = Field(None, serialization_alias="avgResponseSizeKb", description="Taille moyenne des réponses en kilooctets")
    p5_response_size_kb: float | None = Field(
        None, serialization_alias="p5ResponseSizeKb", description="5ᵉ percentile des tailles de réponses en kilooctets"
    )
    median_response_size_kb: float | None = Field(
        None, serialization_alias="medianResponseSizeKb", description="Médiane des tailles de réponses en kilooctets"
    )
    p95_response_size_kb: float | None = Field(
        None, serialization_alias="p95ResponseSizeKb", description="95ᵉ percentile des tailles de réponses en kilooctets"
    )
    min_response_size_kb: float | None = Field(
        None, serialization_alias="minResponseSizeKb", description="Taille minimale des réponses en kilooctets"
    )
    max_response_size_kb: float | None = Field(
        None, serialization_alias="maxResponseSizeKb", description="Taille maximale des réponses en kilooctets"
    )
    variance_response_size_kb: float | None = Field(
        None, serialization_alias="varianceResponseSizeKb", description="Variance des tailles de réponses en kilooctets²"
    )
    std_response_size_kb: float | None = Field(
        None, serialization_alias="stdResponseSizeKb", description="Écart-type des tailles de réponses en kilooctets"
    )

    model_config = ConfigDict(populate_by_name=True)


class PerformanceSummaryResponse(BaseModel):
    """Réponse contenant la liste agrégée des métriques."""

    metrics: list[PerformanceMetricSummary] = Field(default_factory=list, description="Liste des métriques agrégées")

    model_config = ConfigDict(populate_by_name=True)


class ServiceMetricSummary(BaseModel):
    """Résumé agrégé des métriques par service backend.

    Attributes:
        service_prefix (str): identifiant du service backend.
        count (int): nombre total de requêtes agrégées pour le service.
        success_rate (float): taux de succès entre 0 et 1.
        client_error_rate (float): taux d'erreurs 4xx entre 0 et 1.
        server_error_rate (float): taux d'erreurs 5xx entre 0 et 1.
        timeout_rate (float): taux de réponses 504 entre 0 et 1.
        avg_ms (float | None): durée moyenne des requêtes en millisecondes.
        p5_ms (float | None): 5ᵉ percentile des durées en millisecondes.
        median_ms (float | None): médiane des durées en millisecondes.
        p95_ms (float | None): 95ᵉ percentile des durées en millisecondes.
        min_ms (float | None): durée minimale en millisecondes.
        max_ms (float | None): durée maximale en millisecondes.
        variance_ms2 (float | None): variance des durées en millisecondes carrés.
        std_ms (float | None): écart-type des durées en millisecondes.
        avg_request_size_kb (float | None): taille moyenne des requêtes en kilooctets.
        p5_request_size_kb (float | None): 5ᵉ percentile des tailles de requêtes en kilooctets.
        median_request_size_kb (float | None): médiane des tailles de requêtes en kilooctets.
        p95_request_size_kb (float | None): 95ᵉ percentile des tailles de requêtes en kilooctets.
        min_request_size_kb (float | None): taille minimale des requêtes en kilooctets.
        max_request_size_kb (float | None): taille maximale des requêtes en kilooctets.
        variance_request_size_kb (float | None): variance des tailles de requêtes en kilooctets carrés.
        std_request_size_kb (float | None): écart-type des tailles de requêtes en kilooctets.
        avg_response_size_kb (float | None): taille moyenne des réponses en kilooctets.
        p5_response_size_kb (float | None): 5ᵉ percentile des tailles de réponses en kilooctets.
        median_response_size_kb (float | None): médiane des tailles de réponses en kilooctets.
        p95_response_size_kb (float | None): 95ᵉ percentile des tailles de réponses en kilooctets.
        min_response_size_kb (float | None): taille minimale des réponses en kilooctets.
        max_response_size_kb (float | None): taille maximale des réponses en kilooctets.
        variance_response_size_kb (float | None): variance des tailles de réponses en kilooctets carrés.
        std_response_size_kb (float | None): écart-type des tailles de réponses en kilooctets.
    """

    service_prefix: str = Field(..., serialization_alias="servicePrefix", description="Identifiant du service backend")
    count: int = Field(..., description="Nombre de requêtes agrégées")
    success_rate: float = Field(..., serialization_alias="successRate", description="Taux de succès entre 0 et 1")
    client_error_rate: float = Field(0.0, serialization_alias="clientErrorRate", description="Taux d'erreurs 4xx entre 0 et 1")
    server_error_rate: float = Field(0.0, serialization_alias="serverErrorRate", description="Taux d'erreurs 5xx entre 0 et 1")
    timeout_rate: float = Field(0.0, serialization_alias="timeoutRate", description="Taux de timeouts (504) entre 0 et 1")
    avg_ms: float | None = Field(None, serialization_alias="avgMs", description="Durée moyenne en millisecondes")
    p5_ms: float | None = Field(None, serialization_alias="p5Ms", description="5ᵉ percentile en millisecondes")
    median_ms: float | None = Field(None, serialization_alias="medianMs", description="Médiane (ms)")
    p95_ms: float | None = Field(None, serialization_alias="p95Ms", description="95ᵉ percentile en millisecondes")
    min_ms: float | None = Field(None, serialization_alias="minMs", description="Durée minimale en millisecondes")
    max_ms: float | None = Field(None, serialization_alias="maxMs", description="Durée maximale en millisecondes")
    variance_ms2: float | None = Field(None, serialization_alias="varianceMs2", description="Variance (ms²)")
    std_ms: float | None = Field(None, serialization_alias="stdMs", description="Écart-type (ms)")
    avg_request_size_kb: float | None = Field(None, serialization_alias="avgRequestSizeKb", description="Taille moyenne des requêtes en kilooctets")
    p5_request_size_kb: float | None = Field(
        None, serialization_alias="p5RequestSizeKb", description="5ᵉ percentile des tailles de requêtes en kilooctets"
    )
    median_request_size_kb: float | None = Field(
        None, serialization_alias="medianRequestSizeKb", description="Médiane des tailles de requêtes en kilooctets"
    )
    p95_request_size_kb: float | None = Field(
        None, serialization_alias="p95RequestSizeKb", description="95ᵉ percentile des tailles de requêtes en kilooctets"
    )
    min_request_size_kb: float | None = Field(None, serialization_alias="minRequestSizeKb", description="Taille minimale des requêtes en kilooctets")
    max_request_size_kb: float | None = Field(None, serialization_alias="maxRequestSizeKb", description="Taille maximale des requêtes en kilooctets")
    variance_request_size_kb: float | None = Field(
        None, serialization_alias="varianceRequestSizeKb", description="Variance des tailles de requêtes en kilooctets²"
    )
    std_request_size_kb: float | None = Field(
        None, serialization_alias="stdRequestSizeKb", description="Écart-type des tailles de requêtes en kilooctets"
    )
    avg_response_size_kb: float | None = Field(None, serialization_alias="avgResponseSizeKb", description="Taille moyenne des réponses en kilooctets")
    p5_response_size_kb: float | None = Field(
        None, serialization_alias="p5ResponseSizeKb", description="5ᵉ percentile des tailles de réponses en kilooctets"
    )
    median_response_size_kb: float | None = Field(
        None, serialization_alias="medianResponseSizeKb", description="Médiane des tailles de réponses en kilooctets"
    )
    p95_response_size_kb: float | None = Field(
        None, serialization_alias="p95ResponseSizeKb", description="95ᵉ percentile des tailles de réponses en kilooctets"
    )
    min_response_size_kb: float | None = Field(
        None, serialization_alias="minResponseSizeKb", description="Taille minimale des réponses en kilooctets"
    )
    max_response_size_kb: float | None = Field(
        None, serialization_alias="maxResponseSizeKb", description="Taille maximale des réponses en kilooctets"
    )
    variance_response_size_kb: float | None = Field(
        None, serialization_alias="varianceResponseSizeKb", description="Variance des tailles de réponses en kilooctets²"
    )
    std_response_size_kb: float | None = Field(
        None, serialization_alias="stdResponseSizeKb", description="Écart-type des tailles de réponses en kilooctets"
    )

    model_config = ConfigDict(populate_by_name=True)


class ServiceSummaryResponse(BaseModel):
    """Réponse contenant la liste agrégée des métriques par service."""

    metrics: list[ServiceMetricSummary] = Field(default_factory=list, description="Liste des métriques agrégées par service")

    model_config = ConfigDict(populate_by_name=True)


class TimeSeriesPoint(BaseModel):
    """Un point de données dans une série temporelle."""

    timestamp: datetime = Field(..., description="Horodatage du début du bucket temporel (UTC)")
    count: int = Field(..., description="Nombre de requêtes dans ce bucket")
    avg_ms: float | None = Field(None, serialization_alias="avgMs", description="Durée moyenne en millisecondes dans ce bucket")

    model_config = ConfigDict(populate_by_name=True)


class TimeSeriesResponse(BaseModel):
    """Réponse contenant une série temporelle de métriques pour un filtre donné."""

    route: str | None = Field(None, description="Route filtrée (None si toutes les routes)")
    bucket_minutes: int = Field(..., serialization_alias="bucketMinutes", description="Taille du bucket temporel en minutes")
    points: list[TimeSeriesPoint] = Field(default_factory=list, description="Points de la série temporelle ordonnés chronologiquement")

    model_config = ConfigDict(populate_by_name=True)
