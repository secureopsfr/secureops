"""Router pour l'upload et la galerie d'images (admin)."""

from typing import Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.schemas.common import make_pagination_meta
from app.services.image_upload import ImageUploadService

# Variables pour éviter les appels de fonction dans les arguments par défaut (B008)
DEFAULT_FILE = File(...)
DEFAULT_FORM_NONE = Form(None)
DEFAULT_SORT_DATE = Query("date", description="Champ de tri (date, name, size)")
DEFAULT_SORT_DESC = Query("desc", description="Ordre de tri (asc, desc)")
DEFAULT_QUERY_50 = Query(50, ge=1, le=500, description="Nombre d'images par page")
DEFAULT_QUERY_0 = Query(0, ge=0, description="Décalage pour la pagination")

router = APIRouter()

# Instance du service
image_service = ImageUploadService()


class ImageUploadResponse(BaseModel):
    """Schéma de réponse pour l'upload d'image."""

    filename: str
    url: str
    message: str


class ErrorResponse(BaseModel):
    """Schéma de réponse pour les erreurs."""

    error: str
    detail: Optional[str] = None


@router.get("/images")
async def list_images(
    sort_by: str = DEFAULT_SORT_DATE,
    sort_order: str = DEFAULT_SORT_DESC,
    limit: int = DEFAULT_QUERY_50,
    offset: int = DEFAULT_QUERY_0,
) -> Dict:
    """
    Liste les images uploadées avec pagination (admin uniquement).

    Args:
        sort_by: Champ de tri (date, name, size)
        sort_order: Ordre de tri (asc, desc)
        limit: Nombre d'images par page
        offset: Décalage pour la pagination

    Returns:
        dict: {images: [...], total, page, per_page, total_pages}
    """
    try:
        all_images = image_service.list_images(sort_by=sort_by, sort_order=sort_order)
        total = len(all_images)
        paginated_images = all_images[offset : offset + limit]  # noqa: E203
        return {
            "images": paginated_images,
            **make_pagination_meta(total=total, limit=limit, offset=offset),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération: {str(e)}")


@router.get("/images/stats")
async def image_gallery_stats() -> Dict:
    """
    Retourne les statistiques de la galerie (admin uniquement).

    Returns:
        dict: total, total_size, by_extension
    """
    try:
        return image_service.get_gallery_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.delete("/images/{filename}")
async def delete_image(filename: str) -> Dict:
    """
    Supprime une image uploadée (admin uniquement).

    Args:
        filename: Nom du fichier à supprimer

    Returns:
        dict: Message de confirmation
    """
    try:
        return image_service.delete_image(filename)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")


@router.post(
    "/upload-image",
    response_model=ImageUploadResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def upload_image(
    file: UploadFile = DEFAULT_FILE,
    slug: Optional[str] = DEFAULT_FORM_NONE,
) -> ImageUploadResponse:
    """
    Upload une nouvelle image (admin uniquement).

    Args:
        file: Fichier image à uploader (JPG, PNG, GIF, WebP).
        slug: Slug optionnel pour le nom du fichier (sinon UUID).

    Returns:
        ImageUploadResponse: Détails de l'image uploadée.

    Raises:
        HTTPException: Erreur 400 si fichier invalide, 500 en cas d'erreur serveur.
    """
    try:
        result = await image_service.upload_image(file, slug)
        return ImageUploadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {str(e)}")


@router.post("/images/generate-thumbnails")
async def generate_thumbnails() -> Dict:
    """
    Génère les thumbnails manquants pour toutes les images existantes (admin uniquement).

    Returns:
        dict: Nombre de thumbnails générés, ignorés et erreurs.
    """
    try:
        return image_service.generate_all_thumbnails()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
