/**
 * Skeleton du Header — reproduit la structure et le positionnement du Header réel.
 * Utilise les mêmes classes CSS (.nav, .nav-links, .nav-cta) pour un alignement identique.
 */

import Skeleton from "./Skeleton";

export default function HeaderSkeleton() {
  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 bg-[var(--bg)] border-b border-[var(--border)]"
      style={{ height: "var(--header-height)" }}
    >
      <div className="nav">
        {/* Logo : image 40x40 + texte SecureOps */}
        <div className="logo flex items-center gap-2">
          <Skeleton width="w-10" height="h-10" rounded="lg" />
          <Skeleton width="w-24" height="h-5" className="hidden md:block" />
        </div>
        {/* Liens de navigation (centrés) */}
        <nav className="nav-links hidden md:flex items-center gap-6">
          <Skeleton width="w-14" height="h-4" />
          <Skeleton width="w-16" height="h-4" />
          <Skeleton width="w-12" height="h-4" />
          <Skeleton width="w-16" height="h-4" />
        </nav>
        {/* CTA : icônes + boutons */}
        <div className="nav-cta flex items-center gap-2">
          <div className="hidden md:flex md:gap-2 md:items-center">
            <Skeleton width="w-8" height="h-8" rounded="full" />
            <Skeleton width="w-8" height="h-8" rounded="full" />
            <Skeleton width="w-24" height="h-9" rounded="full" />
            <Skeleton width="w-24" height="h-9" rounded="full" />
          </div>
          <Skeleton
            width="w-10"
            height="h-10"
            rounded="full"
            className="md:hidden"
          />
        </div>
      </div>
    </header>
  );
}
