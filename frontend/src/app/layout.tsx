import React from "react";

/**
 * Root layout – pass-through shell.
 * <html> and <body> are rendered in [locale]/layout.tsx so that
 * the `lang` attribute is set server-side for SEO.
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
