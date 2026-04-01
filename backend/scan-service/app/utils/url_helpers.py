"""Re-export des helpers URL depuis common + alias locaux."""

from common.url_helpers import (
    build_http_url,
    build_https_url,
    build_url_with_path,
    extract_host_from_url,
    extract_port_from_url,
    get_host_from_url,
    get_https_port_from_url,
    get_scan_base_url,
    location_redirects_to_https,
    registered_domain_from_url,
)

# Alias historique utilisé par le scan multi / preflight
registered_domain = registered_domain_from_url

__all__ = [
    "build_http_url",
    "build_https_url",
    "build_url_with_path",
    "extract_host_from_url",
    "extract_port_from_url",
    "get_host_from_url",
    "get_https_port_from_url",
    "get_scan_base_url",
    "location_redirects_to_https",
    "registered_domain",
    "registered_domain_from_url",
]
