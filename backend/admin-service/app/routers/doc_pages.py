"""Router pour la gestion des pages de documentation (admin + lecture publique)."""

import os
import re
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.utils.auth import require_admin_user

# Dépendance admin réutilisée (évite B008: function call in default)
_require_admin = Depends(require_admin_user)

# Répertoire de stockage des docs (HTML)
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "docs")

router = APIRouter()


# ── Schémas Pydantic ──────────────────────────────────────────────


class DocPageRecord(BaseModel):
    """Schéma d'une page doc."""

    slug: str
    title: str
    size: int
    updated_at: str


class DocPageContent(BaseModel):
    """Schéma pour le contenu d'une page doc."""

    slug: str
    title: str
    content: str
    size: int
    updated_at: str


class DocPageUpdateRequest(BaseModel):
    """Schéma pour la mise à jour d'une page doc."""

    title: str
    content: str


class DocPageCreateRequest(BaseModel):
    """Schéma pour la création d'une page doc."""

    slug: str
    title: str
    content: str = ""


# ── Helpers ───────────────────────────────────────────────────────


def _slug_to_filename(slug: str) -> str:
    """Convertit un slug en nom de fichier (.html)."""
    if not slug or not slug.strip():
        raise HTTPException(status_code=400, detail="Le slug ne peut pas être vide")
    base = slug.strip().lower()
    if not re.match(r"^[a-zA-Z0-9_-]+$", base):
        raise HTTPException(
            status_code=400,
            detail="Le slug ne doit contenir que lettres, chiffres, tirets et underscores",
        )
    return f"{base}.html"


def _filename_to_slug(filename: str) -> str:
    """Extrait le slug du nom de fichier."""
    return os.path.splitext(filename)[0]


def _extract_title_from_html(content: str) -> str:
    """Extrait le premier h1 ou titre du contenu HTML, sinon slug par défaut."""
    import re as re_mod

    m = re_mod.search(r"<h1[^>]*>(.*?)</h1>", content, re_mod.DOTALL | re_mod.IGNORECASE)
    if m:
        raw = m.group(1).strip()
        # Enlever les balises HTML internes
        raw = re_mod.sub(r"<[^>]+>", "", raw).strip()
        return raw[:200] if raw else "Sans titre"
    return "Sans titre"


def safe_doc_path(slug: str, *, must_exist: bool = True) -> str:
    """Construit et valide le chemin d'une page doc.

    - Vérifie que le chemin résolu reste dans DOCS_DIR (path traversal).
    - Si *must_exist* est True, vérifie que le fichier existe.

    Returns:
        str: Chemin absolu validé vers le fichier doc.

    Raises:
        HTTPException 400: slug invalide.
        HTTPException 403: si le chemin résolu sort de DOCS_DIR.
        HTTPException 404: si must_exist et le fichier n'existe pas.
    """
    filename = _slug_to_filename(slug)
    file_path = os.path.join(DOCS_DIR, filename)

    real_path = os.path.realpath(file_path)
    real_dir = os.path.realpath(DOCS_DIR)
    if not real_path.startswith(real_dir):
        raise HTTPException(status_code=403, detail="Accès interdit")

    if must_exist and not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"Page doc '{slug}' non trouvée")

    return file_path


def _list_docs() -> List[Dict]:
    """Liste les pages doc disponibles (slugs, titres, tailles)."""
    os.makedirs(DOCS_DIR, exist_ok=True)

    docs: List[Dict] = []
    for entry in os.scandir(DOCS_DIR):
        if not entry.is_file() or not entry.name.endswith(".html"):
            continue

        slug = _filename_to_slug(entry.name)
        stat = entry.stat()
        with open(entry.path, "r", encoding="utf-8") as f:
            content = f.read()
        title = _extract_title_from_html(content)

        docs.append(
            {
                "slug": slug,
                "title": title,
                "size": stat.st_size,
                "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )

    docs.sort(key=lambda d: d["slug"])
    return docs


# ── Endpoints lecture (publics) ───────────────────────────────────────
# Documentation accessible à tous (gateway PUBLIC_EXACT/PREFIX).


@router.get("/docs")
async def list_docs() -> Dict:
    """Liste les pages de documentation (public)."""
    docs = _list_docs()
    return {"docs": docs, "total": len(docs)}


@router.get("/docs/{slug}")
async def get_doc(slug: str) -> DocPageContent:
    """Récupère le contenu d'une page doc (utilisateur authentifié)."""
    file_path = safe_doc_path(slug)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    stat = os.stat(file_path)
    title = _extract_title_from_html(content)

    return DocPageContent(
        slug=slug,
        title=title,
        content=content,
        size=stat.st_size,
        updated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    )


@router.put("/docs/{slug}")
async def update_doc(slug: str, body: DocPageUpdateRequest, _: dict = _require_admin) -> Dict:
    """Met à jour une page doc (admin)."""
    file_path = safe_doc_path(slug)

    content = body.content.strip()
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"message": f"Page '{slug}' mise à jour avec succès"}


@router.post("/docs")
async def create_doc(body: DocPageCreateRequest, _: dict = _require_admin) -> Dict:
    """Crée une nouvelle page doc (admin)."""
    os.makedirs(DOCS_DIR, exist_ok=True)

    slug = body.slug.strip().lower()
    if not slug:
        raise HTTPException(status_code=400, detail="Le slug ne peut pas être vide")

    filename = _slug_to_filename(slug)
    file_path = os.path.join(DOCS_DIR, filename)

    real_path = os.path.realpath(file_path)
    real_dir = os.path.realpath(DOCS_DIR)
    if not real_path.startswith(real_dir):
        raise HTTPException(status_code=403, detail="Accès interdit")

    if os.path.exists(file_path):
        raise HTTPException(status_code=409, detail=f"La page '{slug}' existe déjà")

    content = body.content.strip() if body.content else ""
    if not content:
        content = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body>
<h1>{body.title or slug}</h1>
<p>Contenu à rédiger.</p>
</body>
</html>"""
    elif not content.lower().startswith("<!doctype") and not content.lower().startswith("<html"):
        content = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body>
<h1>{body.title or slug}</h1>
{content}
</body>
</html>"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"message": f"Page '{slug}' créée avec succès", "slug": slug}


@router.delete("/docs/{slug}")
async def delete_doc(slug: str, _: dict = _require_admin) -> Dict:
    """Supprime une page doc (admin)."""
    file_path = safe_doc_path(slug)
    os.remove(file_path)
    return {"message": f"Page '{slug}' supprimée avec succès"}
