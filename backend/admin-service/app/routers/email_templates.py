"""Router pour la gestion des templates d'emails (admin)."""

import os
import re
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Répertoire de stockage des templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "templates", "emails")

router = APIRouter()


# ── Schémas Pydantic ──────────────────────────────────────────────


class TemplateRecord(BaseModel):
    """Schéma d'un template email."""

    filename: str
    size: int
    updated_at: str


class TemplateContent(BaseModel):
    """Schéma pour le contenu d'un template."""

    filename: str
    content: str
    size: int
    updated_at: str


class TemplateUpdateRequest(BaseModel):
    """Schéma pour la mise à jour d'un template."""

    content: str


class TemplateCreateRequest(BaseModel):
    """Schéma pour la création d'un template."""

    filename: str
    content: str = ""


# ── Helpers ───────────────────────────────────────────────────────


def safe_template_path(filename: str, *, must_exist: bool = True) -> str:
    """Construit et valide le chemin d'un template.

    - Vérifie que le chemin résolu reste dans TEMPLATES_DIR (path traversal).
    - Si *must_exist* est True, vérifie que le fichier existe.

    Returns:
        str: Chemin absolu validé vers le template.

    Raises:
        HTTPException 403: si le chemin résolu sort de TEMPLATES_DIR.
        HTTPException 404: si must_exist et le fichier n'existe pas.
    """
    file_path = os.path.join(TEMPLATES_DIR, filename)

    real_path = os.path.realpath(file_path)
    real_dir = os.path.realpath(TEMPLATES_DIR)
    if not real_path.startswith(real_dir):
        raise HTTPException(status_code=403, detail="Accès interdit")

    if must_exist and not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"Template '{filename}' non trouvé")

    return file_path


# ── Endpoints ─────────────────────────────────────────────────────


@router.get("/templates")
async def list_templates() -> Dict:
    """Liste les templates d'emails disponibles."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)

    templates: List[Dict] = []
    for entry in os.scandir(TEMPLATES_DIR):
        if not entry.is_file():
            continue
        ext = os.path.splitext(entry.name)[1].lower()
        if ext != ".html":
            continue

        stat = entry.stat()
        templates.append(
            {
                "filename": entry.name,
                "size": stat.st_size,
                "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )

    templates.sort(key=lambda t: t["filename"])
    return {"templates": templates, "total": len(templates)}


@router.get("/templates/{filename}")
async def get_template(filename: str) -> TemplateContent:
    """Récupère le contenu d'un template email."""
    file_path = safe_template_path(filename)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    stat = os.stat(file_path)
    return TemplateContent(
        filename=filename,
        content=content,
        size=stat.st_size,
        updated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    )


@router.put("/templates/{filename}")
async def update_template(filename: str, body: TemplateUpdateRequest) -> Dict:
    """Met à jour le contenu d'un template email."""
    file_path = safe_template_path(filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(body.content)

    return {"message": f"Template '{filename}' mis à jour avec succès"}


# Contenu par défaut pour les nouveaux templates
_DEFAULT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{subject}}</title>
    <style>img { max-width: 100%; height: auto; }</style>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; background-color: #f8f9fa;">
        <h1 style="color: #333; margin: 0; font-size: 24px;">{{subject}}</h1>
    </div>

    <div style="background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        {{content}}
    </div>

    <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
        <p style="margin: 0; color: #7f8c8d; font-size: 14px;">
            <a href="{{unsubscribe_url}}" style="color: #3498db;">Se désabonner</a>
        </p>
    </div>
</body>
</html>"""


@router.post("/templates")
async def create_template(body: TemplateCreateRequest) -> Dict:
    """Crée un nouveau template email."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)

    filename = body.filename.strip()

    # Ajouter .html si manquant
    if not filename.lower().endswith(".html"):
        filename = f"{filename}.html"

    # Valider le nom de fichier (alphanum, tirets, underscores)
    base_name = os.path.splitext(filename)[0]
    if not re.match(r"^[a-zA-Z0-9_-]+$", base_name):
        raise HTTPException(
            status_code=400,
            detail="Le nom du template ne doit contenir que des lettres, chiffres, tirets et underscores",
        )

    file_path = safe_template_path(filename, must_exist=False)

    if os.path.exists(file_path):
        raise HTTPException(status_code=409, detail=f"Le template '{filename}' existe déjà")

    content = body.content if body.content else _DEFAULT_TEMPLATE

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"message": f"Template '{filename}' créé avec succès", "filename": filename}


@router.delete("/templates/{filename}")
async def delete_template(filename: str) -> Dict:
    """Supprime un template email."""
    file_path = safe_template_path(filename)

    os.remove(file_path)
    return {"message": f"Template '{filename}' supprimé avec succès"}
