"""Router pour la gestion des pages de documentation (admin + lecture publique).

Convention de nommage des fichiers :
  {slug}.{lang}.html  — version localisée (ex: scan-passif.fr.html)
  {slug}.html         — fichier legacy sans suffixe de langue (compatibilité)

Chaîne de fallback pour une requête lang=en sur le slug "scan-passif" :
  1. scan-passif.en.html   (version anglaise)
  2. scan-passif.fr.html   (version française de repli)
  3. scan-passif.html      (legacy sans langue)
"""

import os
import re
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.utils.auth import require_admin_user

# Dépendance admin réutilisée (évite B008: function call in default)
_require_admin = Depends(require_admin_user)

# Répertoire de stockage des docs (HTML)
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "docs")

_SUPPORTED_LANGS: frozenset[str] = frozenset({"fr", "en"})
_DEFAULT_LANG = "fr"
_LANG_QUERY = Query(default=_DEFAULT_LANG, max_length=2)

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


def _validate_slug(slug: str) -> str:
    """Valide et normalise un slug. Lève HTTPException si invalide."""
    if not slug or not slug.strip():
        raise HTTPException(status_code=400, detail="Le slug ne peut pas être vide")
    base = slug.strip().lower()
    if not re.match(r"^[a-zA-Z0-9_-]+$", base):
        raise HTTPException(
            status_code=400,
            detail="Le slug ne doit contenir que lettres, chiffres, tirets et underscores",
        )
    return base


def _validate_lang(lang: str) -> str:
    """Normalise et valide la langue. Retourne _DEFAULT_LANG si inconnue."""
    normalized = lang.strip().lower()[:2] if lang else _DEFAULT_LANG
    return normalized if normalized in _SUPPORTED_LANGS else _DEFAULT_LANG


def _resolve_doc_path(slug: str, lang: str) -> str | None:
    """Résout le chemin du fichier doc avec fallback par langue.

    Chaîne de résolution :
      1. {slug}.{lang}.html   — version localisée demandée
      2. {slug}.fr.html       — repli français (si lang != fr)
      3. {slug}.html          — fichier legacy sans suffixe de langue

    Returns:
        str: Chemin absolu résolu, ou None si aucun fichier trouvé.
    """
    real_dir = os.path.realpath(DOCS_DIR)
    candidates = [f"{slug}.{lang}.html"]
    if lang != _DEFAULT_LANG:
        candidates.append(f"{slug}.{_DEFAULT_LANG}.html")
    candidates.append(f"{slug}.html")

    for filename in candidates:
        file_path = os.path.join(DOCS_DIR, filename)
        real_path = os.path.realpath(file_path)
        # Sécurité path-traversal
        if not real_path.startswith(real_dir):
            continue
        if os.path.isfile(file_path):
            return file_path
    return None


def safe_doc_path(slug: str, lang: str = _DEFAULT_LANG, *, must_exist: bool = True) -> str:
    """Construit et valide le chemin d'une page doc avec support multilingue.

    Raises:
        HTTPException 400: slug invalide.
        HTTPException 404: si must_exist et aucun fichier trouvé.
    """
    base = _validate_slug(slug)
    normalized_lang = _validate_lang(lang)

    if not must_exist:
        # Pour la création : on veut le chemin du fichier localisé cible
        filename = f"{base}.{normalized_lang}.html"
        file_path = os.path.join(DOCS_DIR, filename)
        real_path = os.path.realpath(file_path)
        real_dir = os.path.realpath(DOCS_DIR)
        if not real_path.startswith(real_dir):
            raise HTTPException(status_code=403, detail="Accès interdit")
        return file_path

    resolved = _resolve_doc_path(base, normalized_lang)
    if resolved is None:
        raise HTTPException(status_code=404, detail=f"Page doc '{slug}' non trouvée")
    return resolved


def _extract_title_from_html(content: str) -> str:
    """Extrait le premier h1 ou titre du contenu HTML, sinon slug par défaut."""
    import re as re_mod

    m = re_mod.search(r"<h1[^>]*>(.*?)</h1>", content, re_mod.DOTALL | re_mod.IGNORECASE)
    if m:
        raw = m.group(1).strip()
        raw = re_mod.sub(r"<[^>]+>", "", raw).strip()
        return raw[:200] if raw else "Sans titre"
    return "Sans titre"


def _slug_from_filename(filename: str) -> str | None:
    """Extrait le slug depuis un nom de fichier localisé ou legacy.

    Exemples :
      scan-passif.fr.html  → scan-passif
      scan-passif.en.html  → scan-passif
      scan-passif.html     → scan-passif
      other.txt            → None
    """
    if not filename.endswith(".html"):
        return None
    name = filename[:-5]  # retire .html
    # Format localisé : {slug}.{lang}
    parts = name.rsplit(".", 1)
    if len(parts) == 2 and parts[1] in _SUPPORTED_LANGS:
        return parts[0]
    # Legacy sans langue
    return name


def _list_docs(lang: str = _DEFAULT_LANG) -> List[Dict]:
    """Liste les pages doc disponibles, dédupliquées par slug, dans la langue demandée."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    normalized_lang = _validate_lang(lang)

    # Collecte tous les slugs uniques présents sur le disque
    slugs_seen: set[str] = set()
    for entry in os.scandir(DOCS_DIR):
        if not entry.is_file():
            continue
        slug = _slug_from_filename(entry.name)
        if slug:
            slugs_seen.add(slug)

    docs: List[Dict] = []
    for slug in sorted(slugs_seen):
        resolved = _resolve_doc_path(slug, normalized_lang)
        if resolved is None:
            continue
        stat = os.stat(resolved)
        with open(resolved, "r", encoding="utf-8") as f:
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

    return docs


# ── Endpoints lecture (publics) ───────────────────────────────────────
# Documentation accessible à tous (gateway PUBLIC_EXACT/PREFIX).


@router.get("/docs")
async def list_docs(lang: str = _LANG_QUERY) -> Dict:
    """Liste les pages de documentation (public).

    - lang : code ISO 639-1 de la langue souhaitée (fr, en). Défaut : fr.
      Fallback automatique vers la version française si la traduction est absente.
    """
    docs = _list_docs(lang)
    return {"docs": docs, "total": len(docs)}


@router.get("/docs/{slug}")
async def get_doc(
    slug: str,
    lang: str = _LANG_QUERY,
) -> DocPageContent:
    """Récupère le contenu d'une page doc dans la langue demandée.

    - lang : code ISO 639-1 (fr, en). Défaut : fr.
      Fallback automatique vers fr puis legacy .html si la traduction est absente.
    """
    file_path = safe_doc_path(slug, lang)

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
async def update_doc(
    slug: str,
    body: DocPageUpdateRequest,
    lang: str = _LANG_QUERY,
    _: dict = _require_admin,
) -> Dict:
    """Met à jour une page doc dans la langue spécifiée (admin)."""
    file_path = safe_doc_path(slug, lang)

    content = body.content.strip()
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"message": f"Page '{slug}' ({lang}) mise à jour avec succès"}


@router.post("/docs")
async def create_doc(
    body: DocPageCreateRequest,
    lang: str = _LANG_QUERY,
    _: dict = _require_admin,
) -> Dict:
    """Crée une nouvelle page doc dans la langue spécifiée (admin).

    Le fichier est créé avec le suffixe de langue : {slug}.{lang}.html
    """
    os.makedirs(DOCS_DIR, exist_ok=True)

    normalized_lang = _validate_lang(lang)
    base = _validate_slug(body.slug)

    filename = f"{base}.{normalized_lang}.html"
    file_path = os.path.join(DOCS_DIR, filename)

    real_path = os.path.realpath(file_path)
    real_dir = os.path.realpath(DOCS_DIR)
    if not real_path.startswith(real_dir):
        raise HTTPException(status_code=403, detail="Accès interdit")

    if os.path.exists(file_path):
        raise HTTPException(status_code=409, detail=f"La page '{base}' ({normalized_lang}) existe déjà")

    html_lang = normalized_lang
    content = body.content.strip() if body.content else ""
    if not content:
        content = f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body>
<h1>{body.title or base}</h1>
<p>Contenu à rédiger.</p>
</body>
</html>"""
    elif not content.lower().startswith("<!doctype") and not content.lower().startswith("<html"):
        content = f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body>
<h1>{body.title or base}</h1>
{content}
</body>
</html>"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {"message": f"Page '{base}' ({normalized_lang}) créée avec succès", "slug": base}


@router.delete("/docs/{slug}")
async def delete_doc(
    slug: str,
    lang: str = _LANG_QUERY,
    _: dict = _require_admin,
) -> Dict:
    """Supprime une page doc dans la langue spécifiée (admin).

    Si lang n'est pas précisé, supprime la version française par défaut.
    """
    file_path = safe_doc_path(slug, lang)
    os.remove(file_path)
    return {"message": f"Page '{slug}' ({lang}) supprimée avec succès"}
