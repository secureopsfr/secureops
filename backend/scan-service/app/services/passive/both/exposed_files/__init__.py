"""Vérifications fichiers sensibles exposés (roadmap §3.4)."""

from app.services.passive.both.exposed_files.checks import run_exposed_files_checks
from app.services.passive.both.path_checks import PathCheckResult, PathFinding

# Alias pour rétrocompatibilité
ExposedEndpoint = PathFinding
ExposedFilesCheckResult = PathCheckResult

__all__ = ["ExposedEndpoint", "ExposedFilesCheckResult", "run_exposed_files_checks"]
