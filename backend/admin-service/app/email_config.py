"""Configuration pour l'envoi d'emails via Microsoft Graph."""

import logging
import os
import time
from pathlib import Path
from typing import Optional, Tuple

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# ── Chargement des variables d'environnement ────────────────────────────

base_path = Path(__file__).parent.parent
env_path = base_path / ".env"

if env_path.exists():
    result = load_dotenv(env_path, override=True)
    if result:
        logger.info("Variables chargées depuis: %s", env_path)
    else:
        logger.warning("Fichier .env trouvé mais non chargé: %s", env_path)
else:
    logger.debug("Fichier .env non trouvé: %s — utilisation des variables système", env_path)

load_dotenv(override=False)

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
ADMIN_ALERT_EMAIL = os.getenv("ADMIN_ALERT_EMAIL", "") or os.getenv("SENDER_EMAIL", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

logger.info("Configuration Microsoft Graph chargée:")
logger.info("  TENANT_ID: %s", "✓ défini" if TENANT_ID else "✗ manquant")
logger.info("  CLIENT_ID: %s", "✓ défini" if CLIENT_ID else "✗ manquant")
logger.info("  CLIENT_SECRET: %s", "✓ défini" if CLIENT_SECRET else "✗ manquant")
logger.info("  SENDER_EMAIL: %s", "✓ défini" if SENDER_EMAIL else "✗ manquant")
logger.info("  FRONTEND_URL: %s", FRONTEND_URL)

# ── Cache du token Microsoft Graph (TTL ~55 min) ────────────────────────

_TOKEN_TTL_SECONDS = 55 * 60  # tokens MS durent 1 h, on renouvelle à 55 min
_cached_token: Tuple[str, float] | None = None  # (token, expiry_timestamp)


def get_graph_access_token() -> str:
    """Récupère un token d'accès pour Microsoft Graph (avec cache TTL ~55 min).

    Returns:
        str: Token d'accès valide.

    Raises:
        ValueError: Si la configuration d'authentification est absente.
        requests.HTTPError: Si la récupération du token échoue.
    """
    global _cached_token  # noqa: PLW0603

    # Retourner le token en cache s'il est encore valide
    if _cached_token is not None:
        token, expiry = _cached_token
        if time.monotonic() < expiry:
            logger.debug("Token Microsoft Graph servi depuis le cache")
            return token

    if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET]):
        raise ValueError("Configuration Microsoft Graph manquante (TENANT_ID, CLIENT_ID, CLIENT_SECRET).")

    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    try:
        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()
        token = response.json()["access_token"]
        _cached_token = (token, time.monotonic() + _TOKEN_TTL_SECONDS)
        logger.info("Nouveau token Microsoft Graph obtenu et mis en cache (%d s)", _TOKEN_TTL_SECONDS)
        return token
    except requests.HTTPError as e:
        error_detail = ""
        try:
            error_response = response.json()
            error_detail = error_response.get("error_description", error_response.get("error", "Erreur inconnue"))
        except (ValueError, AttributeError):
            error_detail = response.text if hasattr(response, "text") else str(e)

        raise ValueError(
            f"Erreur d'authentification Microsoft Graph (401): {error_detail}. "
            f"Vérifiez que TENANT_ID, CLIENT_ID et CLIENT_SECRET sont corrects et que "
            f"l'application Azure AD a les permissions nécessaires pour Microsoft Graph."
        ) from e


def _get_template_path(template_name: str) -> Path:
    """Retourne le chemin vers un template HTML.

    Args:
        template_name: Nom du fichier template

    Returns:
        Path: Chemin vers le fichier template
    """
    templates_dir = Path(__file__).parent.parent / "data" / "templates" / "emails"
    return templates_dir / template_name


def _load_template(template_name: str, variables: dict) -> str:
    """Charge un template HTML et remplace les variables.

    Args:
        template_name: Nom du fichier template
        variables: Dictionnaire de variables à remplacer

    Returns:
        str: Contenu HTML avec les variables remplacées
    """
    template_path = _get_template_path(template_name)
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remplacer les variables {{variable}} par leurs valeurs
    for key, value in variables.items():
        content = content.replace(f"{{{{{key}}}}}", str(value))

    return content


def _send_graph_email(to_email: str, subject: str, html_body: str, from_address: Optional[str] = None, save_to_sent: bool = True) -> bool:
    """Envoie un email HTML via Microsoft Graph.

    Args:
        to_email: Adresse email du destinataire.
        subject: Sujet de l'email.
        html_body: Corps HTML de l'email.
        from_address: Adresse expéditrice (env SENDER_EMAIL par défaut).
        save_to_sent: Indique si le mail doit apparaître dans les éléments envoyés.

    Returns:
        bool: True si l'envoi a réussi.

    Raises:
        ValueError: Si la configuration Graph est invalide.
        requests.HTTPError: Si l'appel Graph échoue.
    """
    access_token = get_graph_access_token()

    resolved_from = from_address or SENDER_EMAIL
    if not resolved_from:
        raise ValueError("Aucune adresse expéditrice disponible pour Microsoft Graph.")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": [{"emailAddress": {"address": to_email}}],
        },
        "saveToSentItems": save_to_sent,
    }

    send_url = f"https://graph.microsoft.com/v1.0/users/{resolved_from}/sendMail"
    response = requests.post(send_url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()
    return True


async def send_newsletter_email(
    to_email: str,
    subject: str,
    content: str,
    unsubscribe_token: str = "",
    template_name: str = "newsletter.html",
) -> bool:
    """Envoie un email de newsletter via Microsoft Graph.

    Args:
        to_email: Adresse email du destinataire.
        subject: Sujet de l'email.
        content: Contenu HTML de l'email.
        unsubscribe_token: Token de désinscription pour générer le lien.
        template_name: Nom du template HTML à utiliser (par défaut newsletter.html).

    Returns:
        bool: True si l'envoi a réussi, False sinon.

    Raises:
        ValueError: Si la configuration Graph est invalide.
        requests.HTTPError: Si l'appel Graph échoue.
    """
    try:
        unsubscribe_url = (
            f"{FRONTEND_URL}/unsubscribe?token={unsubscribe_token}&email={to_email}" if unsubscribe_token else f"{FRONTEND_URL}/unsubscribe"
        )
        html_content = _load_template(
            template_name,
            {"subject": subject, "content": content, "frontend_url": FRONTEND_URL, "unsubscribe_url": unsubscribe_url},
        )

        return _send_graph_email(to_email=to_email, subject=subject, html_body=html_content, from_address=SENDER_EMAIL)

    except Exception as e:
        logger.error("Erreur lors de l'envoi de l'email newsletter: %s", e)
        return False


def send_alert_email(
    rule_name: str,
    metric: str,
    current_value: float,
    threshold: float,
    severity: str,
    message: str,
    window_minutes: int,
    service_filter: str | None = None,
) -> bool:
    """Envoie un email de notification d'alerte à l'administrateur.

    Args:
        rule_name: Nom de la règle d'alerte déclenchée.
        metric: Métrique concernée (error_rate, response_time, etc.).
        current_value: Valeur actuelle qui a déclenché l'alerte.
        threshold: Seuil configuré sur la règle.
        severity: Gravité de l'alerte (warning, critical).
        message: Message descriptif de l'alerte.
        window_minutes: Fenêtre temporelle de la règle.
        service_filter: Service filtré (None = tous les services).

    Returns:
        bool: True si l'envoi a réussi, False sinon.
    """
    if not ADMIN_ALERT_EMAIL:
        logger.warning("[Alerting] Aucun email admin configuré (ADMIN_ALERT_EMAIL / SENDER_EMAIL). Notification email ignorée.")
        return False

    # Couleurs selon la sévérité
    severity_styles = {
        "critical": {"color": "#dc2626", "bg": "#fef2f2"},
        "warning": {"color": "#d97706", "bg": "#fffbeb"},
    }
    styles = severity_styles.get(severity, severity_styles["warning"])

    # Labels des métriques
    metric_labels = {
        "error_rate": "Taux d'erreurs",
        "response_time": "Temps de réponse moyen",
        "error_count": "Nombre d'erreurs",
        "request_count": "Nombre de requêtes",
    }
    metric_units = {"error_rate": "%", "response_time": " ms", "error_count": "", "request_count": ""}
    metric_label = metric_labels.get(metric, metric)
    unit = metric_units.get(metric, "")

    subject = f"[{severity.upper()}] {rule_name} — {metric_label}: {current_value:.1f}{unit}"

    try:
        html_content = _load_template(
            "alert.html",
            {
                "subject": subject,
                "severity": severity,
                "severity_color": styles["color"],
                "severity_bg": styles["bg"],
                "rule_name": rule_name,
                "metric": metric_label,
                "current_value": f"{current_value:.1f}{unit}",
                "threshold": f"{threshold}{unit}",
                "window_minutes": str(window_minutes),
                "service": service_filter or "Tous les services",
                "message": message,
                "frontend_url": FRONTEND_URL,
            },
        )

        _send_graph_email(to_email=ADMIN_ALERT_EMAIL, subject=subject, html_body=html_content, save_to_sent=False)
        logger.info("[Alerting] Email d'alerte envoyé à %s pour la règle '%s'", ADMIN_ALERT_EMAIL, rule_name)
        return True

    except Exception as e:
        logger.error("[Alerting] Erreur lors de l'envoi de l'email d'alerte: %s", e)
        return False


def send_scan_alert_email(
    to_email: str,
    url: str,
    subject: str,
    message: str,
    severity: str = "warning",
    alert_type: str = "regression",
) -> bool:
    """Envoie un email d'alerte de scan planifié à un utilisateur.

    Utilisé pour les alertes de régression (score) ou finding critical.

    Args:
        to_email: Adresse du destinataire.
        url: URL scannée.
        subject: Sujet de l'email.
        message: Message descriptif.
        severity: Gravité (warning, critical).
        alert_type: Type d'alerte (regression, critical_finding).

    Returns:
        bool: True si l'envoi a réussi.
    """
    if not to_email or not to_email.strip():
        logger.warning("[ScanAlert] Email destinataire vide. Notification ignorée.")
        return False

    severity_styles = {
        "critical": {"color": "#dc2626", "bg": "#fef2f2"},
        "warning": {"color": "#d97706", "bg": "#fffbeb"},
    }
    styles = severity_styles.get(severity.lower(), severity_styles["warning"])

    try:
        html_content = _load_template(
            "scan_alert.html",
            {
                "subject": subject,
                "severity": severity,
                "severity_color": styles["color"],
                "severity_bg": styles["bg"],
                "url": url,
                "message": message,
                "alert_type": alert_type,
                "frontend_url": FRONTEND_URL,
            },
        )
        _send_graph_email(to_email=to_email.strip(), subject=subject, html_body=html_content, save_to_sent=False)
        logger.info("[ScanAlert] Email envoyé à %s pour %s sur %s", to_email[:20], alert_type, url[:50])
        return True
    except Exception as e:
        logger.error("[ScanAlert] Erreur envoi email: %s", e)
        return False
