"""Pipeline intrusif : liste ordonnée des checks Phase A, B, C.

Structure des checks :
  checks/frontend/  — tests HTML/DOM uniquement (scan_type=frontend)
  checks/backend/   — tests APIs/protocoles uniquement (scan_type=backend)
  checks/both/      — tests agnostiques (s'adaptent selon scan_type)

Chaque fonction a la signature :
    async def run(url: str, *, scan_type: str, credentials: ScanCredentials | None) -> list[Finding]
"""

from __future__ import annotations

from app.services.intrusive.checks.backend.api_schema_abuse.check import run as run_api_schema_abuse
from app.services.intrusive.checks.backend.graphql_abuse.check import run as run_graphql_abuse
from app.services.intrusive.checks.backend.graphql_subscriptions.check import run as run_graphql_subscriptions
from app.services.intrusive.checks.backend.grpc_abuse.check import run as run_grpc_abuse

# ── Backend uniquement ─────────────────────────────────────────────────────────
from app.services.intrusive.checks.backend.mass_assignment.check import run as run_mass_assignment
from app.services.intrusive.checks.both.auth_bruteforce.check import run as run_auth_bruteforce
from app.services.intrusive.checks.both.business_logic.check import run as run_business_logic
from app.services.intrusive.checks.both.cache_poisoning.check import run as run_cache_poisoning
from app.services.intrusive.checks.both.command_injection.check import run as run_command_injection
from app.services.intrusive.checks.both.cors_actif.check import run as run_cors_actif
from app.services.intrusive.checks.both.csrf.check import run as run_csrf
from app.services.intrusive.checks.both.dos_p0.check import run as run_dos_p0
from app.services.intrusive.checks.both.host_header.check import run as run_host_header
from app.services.intrusive.checks.both.idor.check import run as run_idor
from app.services.intrusive.checks.both.idor_complet.check import run as run_idor_complet
from app.services.intrusive.checks.both.insecure_deserialization.check import run as run_insecure_deserialization
from app.services.intrusive.checks.both.lfi_rfi.check import run as run_lfi_rfi
from app.services.intrusive.checks.both.methodes_http.check import run as run_methodes_http
from app.services.intrusive.checks.both.nosqli.check import run as run_nosqli
from app.services.intrusive.checks.both.oauth_oidc.check import run as run_oauth_oidc
from app.services.intrusive.checks.both.object_storage.check import run as run_object_storage

# ── Les deux (both) ────────────────────────────────────────────────────────────
from app.services.intrusive.checks.both.open_redirect.check import run as run_open_redirect
from app.services.intrusive.checks.both.path_traversal.check import run as run_path_traversal
from app.services.intrusive.checks.both.race_conditions.check import run as run_race_conditions
from app.services.intrusive.checks.both.request_smuggling.check import run as run_request_smuggling
from app.services.intrusive.checks.both.service_mesh.check import run as run_service_mesh
from app.services.intrusive.checks.both.session_fixation.check import run as run_session_fixation
from app.services.intrusive.checks.both.sqli.check import run as run_sqli
from app.services.intrusive.checks.both.ssrf.check import run as run_ssrf
from app.services.intrusive.checks.both.ssti.check import run as run_ssti
from app.services.intrusive.checks.both.upload_abuse.check import run as run_upload_abuse
from app.services.intrusive.checks.both.websocket_authz.check import run as run_websocket_authz
from app.services.intrusive.checks.both.xxe.check import run as run_xxe

# ── Frontend uniquement ────────────────────────────────────────────────────────
from app.services.intrusive.checks.frontend.parametres_reflechis.check import run as run_parametres_reflechis

INTRUSIVE_STEPS: tuple[tuple[str, object], ...] = (
    # Phase A — P0 (both)
    ("open_redirect", run_open_redirect),
    ("methodes_http", run_methodes_http),
    ("cors_actif", run_cors_actif),
    # Phase A — P0 (frontend)
    ("parametres_reflechis", run_parametres_reflechis),
    # Phase A — P0 (both suite)
    ("sqli", run_sqli),
    ("path_traversal", run_path_traversal),
    ("csrf", run_csrf),
    ("idor", run_idor),
    ("command_injection", run_command_injection),
    ("nosqli", run_nosqli),
    ("dos_p0", run_dos_p0),
    # Phase B — P0 suite (both)
    ("auth_bruteforce", run_auth_bruteforce),
    ("session_fixation", run_session_fixation),
    ("upload_abuse", run_upload_abuse),
    ("idor_complet", run_idor_complet),
    # Phase B — P1 (backend)
    ("mass_assignment", run_mass_assignment),
    ("graphql_abuse", run_graphql_abuse),
    ("api_schema_abuse", run_api_schema_abuse),
    # Phase B — P1 (both)
    ("ssrf", run_ssrf),
    ("xxe", run_xxe),
    ("ssti", run_ssti),
    ("insecure_deserialization", run_insecure_deserialization),
    ("lfi_rfi", run_lfi_rfi),
    # Phase C — P2 (both)
    ("host_header", run_host_header),
    ("cache_poisoning", run_cache_poisoning),
    ("request_smuggling", run_request_smuggling),
    ("race_conditions", run_race_conditions),
    ("business_logic", run_business_logic),
    ("websocket_authz", run_websocket_authz),
    # Phase C — P3 (both)
    ("oauth_oidc", run_oauth_oidc),
    ("object_storage", run_object_storage),
    ("service_mesh", run_service_mesh),
    # Phase C — P3 (backend)
    ("graphql_subscriptions", run_graphql_subscriptions),
    ("grpc_abuse", run_grpc_abuse),
)
