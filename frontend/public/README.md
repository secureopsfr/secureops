# Assets publics

- **manifest.json** : Manifest PWA statique (fallback, langue FR uniquement). Le manifest **dynamique i18n** est servi par l’API `GET /api/manifest/[locale]` et est utilisé en priorité par l’app (voir `layout.tsx` → `manifest: /api/manifest/${locale}`). Ce fichier peut servir de fallback si l’API est indisponible au chargement initial.
- **favicon.ico, favicon-96x96.png, apple-touch-icon.png, logo.png, logo.svg** : icônes et logos utilisés par l’app et le manifest.
