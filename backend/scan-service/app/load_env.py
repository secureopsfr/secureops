"""Charge le .env à la racine du scan-service avant toute config (pytest, uvicorn)."""

from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parents[1] / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
