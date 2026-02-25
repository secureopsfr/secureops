import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pas de trailing slash pour éviter contenu dupliqué (SEO)
  trailingSlash: false,

  // Configuration pour éviter l'avertissement sur le workspace root
  // Note: Le warning sur les lockfiles multiples est normal si vous avez un monorepo

  async headers() {
    // CSP : limite les sources de scripts/styles/connexions pour atténuer XSS et injection.
    // À affiner selon les domaines réels (Cognito, gateway, analytics). Voir docs/SEO-AUDIT.md.
    const isDev = process.env.NODE_ENV === "development";
    const connectSrc = [
      "'self'",
      "https://challenges.cloudflare.com",
      "https://*.amazoncognito.com",
      "https:",
      ...(isDev ? ["http://localhost:8000", "http://127.0.0.1:8000"] : []),
    ].join(" ");
    const csp = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://challenges.cloudflare.com",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob: https:",
      "font-src 'self'",
      `connect-src ${connectSrc}`,
      "frame-src 'self' https://challenges.cloudflare.com https://*.amazoncognito.com",
      "base-uri 'self'",
      "form-action 'self'",
      "frame-ancestors 'none'",
    ].join("; ");

    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: csp },
          // Empêche l'affichage du site dans un iframe (clickjacking)
          { key: "X-Frame-Options", value: "DENY" },
          // Empêche le navigateur de deviner le type MIME (MIME sniffing)
          { key: "X-Content-Type-Options", value: "nosniff" },
          // Contrôle les informations envoyées dans le header Referer
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          // Désactive les API navigateur non utilisées
          {
            key: "Permissions-Policy",
            value:
              "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
          },
          // Force HTTPS pendant 1 an, incluant les sous-domaines
          {
            key: "Strict-Transport-Security",
            value: "max-age=31536000; includeSubDomains; preload",
          },
          // Bloque le chargement si une attaque XSS est détectée (navigateurs legacy)
          { key: "X-XSS-Protection", value: "1; mode=block" },
          // Empêche le téléchargement de ressources cross-origin non autorisées
          { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
          // Isole le contexte de navigation (protection contre Spectre)
          {
            key: "Cross-Origin-Embedder-Policy",
            value: "credentialless",
          },
          // Empêche le chargement de ressources cross-origin non autorisées
          {
            key: "Cross-Origin-Resource-Policy",
            value: "same-origin",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
