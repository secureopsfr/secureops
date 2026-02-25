import Skeleton from "../../components/skeletons/Skeleton";

/**
 * Skeleton de chargement pour la page d'accueil (home).
 * Reproduit la structure : Header, Hero, Logos, Features (3 cards),
 * Testimonials (3 cards), CTA, Footer.
 */
export default function Loading() {
  return (
    <>
      {/* ─── Header skeleton ─── */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[var(--bg)] border-b border-[var(--border)]">
        <div className="max-w-7xl mx-auto flex items-center justify-between px-6 h-16">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <Skeleton width="w-8" height="h-8" rounded="lg" />
            <Skeleton width="w-24" height="h-5" />
          </div>
          {/* Nav links */}
          <div className="hidden md:flex items-center gap-6">
            <Skeleton width="w-16" height="h-4" />
            <Skeleton width="w-12" height="h-4" />
            <Skeleton width="w-16" height="h-4" />
          </div>
          {/* Actions */}
          <div className="flex items-center gap-3">
            <Skeleton width="w-8" height="h-8" rounded="full" />
            <Skeleton width="w-8" height="h-8" rounded="full" />
            <Skeleton width="w-24" height="h-9" rounded="full" />
          </div>
        </div>
      </header>

      {/* ─── Hero section skeleton ─── */}
      <section className="hero-wrapper">
        <div
          className="flex flex-col items-center text-center gap-4"
          style={{ paddingTop: "6rem", paddingBottom: "4rem" }}
        >
          <Skeleton width="w-40" height="h-6" rounded="full" />
          <Skeleton width="w-[480px] max-w-full" height="h-10" />
          <Skeleton width="w-[360px] max-w-full" height="h-10" />
          <Skeleton
            width="w-[500px] max-w-full"
            height="h-5"
            className="mt-2"
          />
          <div className="flex gap-4 mt-4">
            <Skeleton width="w-36" height="h-10" rounded="full" />
            <Skeleton width="w-36" height="h-10" rounded="full" />
          </div>
        </div>
      </section>

      {/* ─── Logos bar skeleton ─── */}
      <section className="landing-section">
        <div className="flex justify-center gap-8 flex-wrap">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} width="w-24" height="h-5" />
          ))}
        </div>
      </section>

      {/* ─── Features section skeleton (3 cards) ─── */}
      <section className="landing-section">
        <div className="flex flex-col items-center text-center mb-8">
          <Skeleton width="w-64" height="h-7" className="mb-3" />
          <Skeleton width="w-96 max-w-full" height="h-4" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto px-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="p-6 rounded-xl border border-[var(--border)] bg-[var(--color-surface-subtle)]"
            >
              <Skeleton width="w-3/4" height="h-5" className="mb-3" />
              <Skeleton width="w-full" height="h-3" className="mb-1.5" />
              <Skeleton width="w-full" height="h-3" className="mb-1.5" />
              <Skeleton width="w-2/3" height="h-3" />
            </div>
          ))}
        </div>
      </section>

      {/* ─── Testimonials section skeleton (3 cards) ─── */}
      <section className="landing-section">
        <div className="flex flex-col items-center text-center mb-8">
          <Skeleton width="w-48" height="h-7" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto px-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="p-6 rounded-xl border border-[var(--border)] bg-[var(--color-surface-subtle)]"
            >
              <Skeleton width="w-full" height="h-3" className="mb-1.5" />
              <Skeleton width="w-full" height="h-3" className="mb-1.5" />
              <Skeleton width="w-3/4" height="h-3" className="mb-4" />
              <Skeleton width="w-32" height="h-3" />
            </div>
          ))}
        </div>
      </section>

      {/* ─── CTA section skeleton ─── */}
      <section className="landing-section">
        <div className="flex flex-col items-center text-center py-12">
          <Skeleton width="w-72" height="h-7" className="mb-4" />
          <Skeleton width="w-96 max-w-full" height="h-4" className="mb-2" />
          <Skeleton width="w-64" height="h-4" className="mb-6" />
          <Skeleton width="w-40" height="h-10" rounded="full" />
        </div>
      </section>
    </>
  );
}
