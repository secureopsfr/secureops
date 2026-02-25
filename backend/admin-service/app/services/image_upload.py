"""Service de gestion de l'upload d'images pour les emails/newsletters."""

import os
import uuid
from datetime import datetime, timezone
from io import BytesIO
from typing import Dict, List, Optional

from common.logging_config import get_logger
from fastapi import HTTPException, UploadFile
from PIL import Image

logger = get_logger(__name__)

# Répertoire de stockage des images uploadées
UPLOAD_IMAGE_DIR = os.getenv(
    "UPLOAD_IMAGE_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "images", "uploads"),
)

# Sous-répertoire pour les thumbnails
THUMBNAIL_DIR = os.path.join(UPLOAD_IMAGE_DIR, "thumbnails")

# Dimensions des thumbnails (carré, pour la galerie admin)
THUMBNAIL_SIZE = (200, 200)

# Extensions images autorisées
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _ensure_thumbnail(filename: str) -> Optional[str]:
    """Génère un thumbnail pour une image si celui-ci n'existe pas déjà.

    Args:
        filename: Nom du fichier image source.

    Returns:
        Chemin relatif du thumbnail (ex: ``/images/uploads/thumbnails/xxx.jpg``)
        ou ``None`` si la génération échoue.
    """
    source_path = os.path.join(UPLOAD_IMAGE_DIR, filename)
    thumb_path = os.path.join(THUMBNAIL_DIR, filename)

    if os.path.isfile(thumb_path):
        return f"/images/uploads/thumbnails/{filename}"

    if not os.path.isfile(source_path):
        return None

    try:
        os.makedirs(THUMBNAIL_DIR, exist_ok=True)
        with Image.open(source_path) as img:
            # Convertir en RGB si nécessaire (pour les PNG avec transparence → JPEG)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)
            # Sauvegarder en JPEG pour les thumbnails (meilleur ratio taille/qualité)
            ext = os.path.splitext(filename)[1].lower()
            if ext in (".png", ".webp", ".gif"):
                # Garder le format d'origine pour ces formats
                img.save(thumb_path, quality=80, optimize=True)
            else:
                img.save(thumb_path, "JPEG", quality=80, optimize=True)
        return f"/images/uploads/thumbnails/{filename}"
    except Exception:
        logger.warning("Impossible de générer le thumbnail pour %s", filename)
        return None


def _delete_thumbnail(filename: str) -> None:
    """Supprime le thumbnail associé à une image, s'il existe."""
    thumb_path = os.path.join(THUMBNAIL_DIR, filename)
    if os.path.isfile(thumb_path):
        os.remove(thumb_path)


class ImageUploadService:
    """Service de gestion de l'upload et de la galerie d'images."""

    def list_images(self, sort_by: str = "date", sort_order: str = "desc") -> List[Dict]:
        """
        Liste toutes les images uploadées avec leurs métadonnées.

        Args:
            sort_by: Champ de tri (date, name, size).
            sort_order: Ordre de tri (asc, desc).

        Returns:
            list[dict]: Liste des images avec filename, url, thumbnail_url, size, created_at.
        """
        os.makedirs(UPLOAD_IMAGE_DIR, exist_ok=True)

        images = []
        for entry in os.scandir(UPLOAD_IMAGE_DIR):
            if not entry.is_file():
                continue
            ext = os.path.splitext(entry.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue

            stat = entry.stat()
            thumb_url = _ensure_thumbnail(entry.name)
            images.append(
                {
                    "filename": entry.name,
                    "url": f"/images/uploads/{entry.name}",
                    "thumbnail_url": thumb_url or f"/images/uploads/{entry.name}",
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )

        # Tri
        sort_key_map = {
            "date": lambda img: img["created_at"],
            "name": lambda img: img["filename"].lower(),
            "size": lambda img: img["size"],
        }
        key_fn = sort_key_map.get(sort_by, sort_key_map["date"])
        images.sort(key=key_fn, reverse=(sort_order == "desc"))

        return images

    def get_gallery_stats(self) -> Dict:
        """Retourne les statistiques de la galerie d'images.

        Returns:
            dict: total, total_size, by_extension.
        """
        os.makedirs(UPLOAD_IMAGE_DIR, exist_ok=True)

        total = 0
        total_size = 0
        by_ext: Dict[str, int] = {}

        for entry in os.scandir(UPLOAD_IMAGE_DIR):
            if not entry.is_file():
                continue
            ext = os.path.splitext(entry.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue

            total += 1
            total_size += entry.stat().st_size
            by_ext[ext] = by_ext.get(ext, 0) + 1

        return {
            "total": total,
            "total_size": total_size,
            "by_extension": by_ext,
        }

    def delete_image(self, filename: str) -> Dict:
        """
        Supprime une image uploadée et son thumbnail.

        Args:
            filename: Nom du fichier à supprimer.

        Returns:
            dict: Message de confirmation.

        Raises:
            HTTPException: Si le fichier n'existe pas ou si le nom est invalide.
        """
        # Sécurité : empêcher la traversée de répertoires
        if "/" in filename or "\\" in filename or ".." in filename:
            raise HTTPException(status_code=400, detail="Nom de fichier invalide")

        file_path = os.path.join(UPLOAD_IMAGE_DIR, filename)
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="Image introuvable")

        os.remove(file_path)
        _delete_thumbnail(filename)
        return {"message": f"Image '{filename}' supprimée avec succès"}

    async def upload_image(self, file: UploadFile, slug: Optional[str] = None) -> dict:
        """
        Upload une nouvelle image et génère un thumbnail.

        Args:
            file: Fichier image à uploader.
            slug: Slug optionnel pour le nom du fichier (sinon UUID).

        Returns:
            dict: Détails de l'image uploadée (filename, url, thumbnail_url, message).

        Raises:
            HTTPException: Si le fichier est invalide ou trop volumineux.
        """
        # Vérifier le type de fichier
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Type de fichier non autorisé. Types acceptés: {', '.join(allowed_types)}",
            )

        # Vérifier la taille du fichier (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail="Fichier trop volumineux. Taille maximale: 5MB")

        # Créer le nom de fichier
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
        if slug:
            unique_filename = f"{slug}{file_extension}"
        else:
            unique_filename = f"{uuid.uuid4()}{file_extension}"

        # Créer le répertoire de destination s'il n'existe pas
        os.makedirs(UPLOAD_IMAGE_DIR, exist_ok=True)

        file_path = os.path.join(UPLOAD_IMAGE_DIR, unique_filename)

        # Vérifier qu'une image avec le même nom n'existe pas déjà
        if os.path.exists(file_path):
            raise HTTPException(
                status_code=409,
                detail=f"Une image avec le nom '{unique_filename}' existe déjà. Veuillez choisir un autre nom.",
            )

        # Sauvegarder le fichier original
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # Générer le thumbnail
        thumb_url = _generate_thumbnail_from_bytes(content, unique_filename)

        # URL de l'image (relative, sera servie par le StaticFiles mount)
        image_url = f"/images/uploads/{unique_filename}"

        return {
            "filename": unique_filename,
            "url": image_url,
            "thumbnail_url": thumb_url or image_url,
            "message": "Image uploadée avec succès",
        }

    def generate_all_thumbnails(self) -> Dict:
        """Génère les thumbnails manquants pour toutes les images existantes.

        Returns:
            dict: Nombre de thumbnails générés et ignorés.
        """
        os.makedirs(UPLOAD_IMAGE_DIR, exist_ok=True)

        generated = 0
        skipped = 0
        errors = 0

        for entry in os.scandir(UPLOAD_IMAGE_DIR):
            if not entry.is_file():
                continue
            ext = os.path.splitext(entry.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue

            thumb_path = os.path.join(THUMBNAIL_DIR, entry.name)
            if os.path.isfile(thumb_path):
                skipped += 1
                continue

            result = _ensure_thumbnail(entry.name)
            if result:
                generated += 1
            else:
                errors += 1

        return {
            "generated": generated,
            "skipped": skipped,
            "errors": errors,
            "message": f"{generated} thumbnail(s) généré(s), {skipped} déjà existant(s), {errors} erreur(s)",
        }


def _generate_thumbnail_from_bytes(content: bytes, filename: str) -> Optional[str]:
    """Génère un thumbnail directement depuis les bytes de l'image uploadée.

    Args:
        content: Contenu brut de l'image.
        filename: Nom du fichier pour le thumbnail.

    Returns:
        Chemin relatif du thumbnail ou ``None`` si la génération échoue.
    """
    try:
        os.makedirs(THUMBNAIL_DIR, exist_ok=True)
        thumb_path = os.path.join(THUMBNAIL_DIR, filename)

        with Image.open(BytesIO(content)) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)
            ext = os.path.splitext(filename)[1].lower()
            if ext in (".png", ".webp", ".gif"):
                img.save(thumb_path, quality=80, optimize=True)
            else:
                img.save(thumb_path, "JPEG", quality=80, optimize=True)
        return f"/images/uploads/thumbnails/{filename}"
    except Exception:
        logger.warning("Impossible de générer le thumbnail pour %s", filename)
        return None
