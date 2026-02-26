"""Vérifications directory listing (roadmap §3.5)."""

from app.services.directory_listing.checks import run_directory_listing_checks
from app.services.path_checks import PathCheckResult, PathFinding

# Alias pour rétrocompatibilité
DirectoryListingEntry = PathFinding
DirectoryListingCheckResult = PathCheckResult

__all__ = [
    "DirectoryListingCheckResult",
    "DirectoryListingEntry",
    "run_directory_listing_checks",
]
