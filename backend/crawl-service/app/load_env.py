"""Charge le .env à la racine du crawl-service avant toute config (pytest, uvicorn)."""

from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parents[1] / ".env"


def ensure_env_loaded() -> None:
    """Charge le fichier .env local s'il existe."""
    if _env_path.exists():
        load_dotenv(_env_path)
