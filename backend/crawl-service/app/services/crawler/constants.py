"""Constantes du module crawler."""

# Script JavaScript injecté dans Playwright pour extraire les liens du DOM.
EXTRACT_LINKS_JS = """
() => {
  const links = [];
  document.querySelectorAll('a[href]').forEach(a => {
    try { links.push({ url: a.href, type: 'page' }); } catch (_) {}
  });
  document.querySelectorAll('form[action]').forEach(f => {
    try { links.push({ url: new URL(f.action, document.baseURI).href, type: 'form' }); } catch (_) {}
  });
  document.querySelectorAll('form').forEach(f => {
    if (!f.action) {
      try { links.push({ url: window.location.href, type: 'form' }); } catch (_) {}
    }
  });
  return links;
}
"""
