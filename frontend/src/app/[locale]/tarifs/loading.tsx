import { HeaderSkeleton } from "../../../components/ui/skeletons";
import Skeleton from "../../../components/ui/skeletons/Skeleton";

/**
 * Skeleton de chargement pour la page Tarifs.
 * Reproduit la structure : Header, Titre + sous-titre, Toggle mensuel/annuel,
 * 3 pricing cards, FAQ (3 cards).
 */
export default function Loading() {
  return (
    <>
      <HeaderSkeleton />

      {/* ─── Pricing section skeleton ─── */}
      <section className="page-section">
        <div className="page-container space-y-8">
          {/* Title + subtitle */}
          <div className="page-header">
            <div className="flex justify-center">
              <Skeleton width="w-64" height="h-9" />
            </div>
            <div className="flex justify-center mt-4">
              <Skeleton width="w-96 max-w-full" height="h-5" />
            </div>
          </div>

          {/* Monthly / Yearly toggle */}
          <div className="flex justify-center">
            <div className="flex gap-1 rounded-lg border border-[var(--border)] p-1 bg-[var(--color-surface-subtle)]">
              <Skeleton width="w-24" height="h-9" rounded="md" />
              <Skeleton width="w-20" height="h-9" rounded="md" />
            </div>
          </div>

          {/* 3 Pricing cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="flex flex-col p-6 rounded-xl border border-[var(--border)] bg-[var(--color-surface-subtle)]"
                style={{
                  borderWidth: i === 1 ? "2px" : "1px",
                  borderColor:
                    i === 1 ? "rgb(var(--primary))" : "var(--border)",
                }}
              >
                {/* Plan name */}
                <Skeleton width="w-28" height="h-6" className="mb-1" />
                {/* Description */}
                <Skeleton width="w-48" height="h-4" className="mb-6" />
                {/* Price */}
                <div className="flex items-center gap-2 mb-6">
                  <Skeleton width="w-16" height="h-10" />
                  <Skeleton width="w-12" height="h-4" />
                </div>
                {/* Features list */}
                <div className="space-y-3 mb-8 flex-1">
                  {Array.from({ length: i === 1 ? 7 : i === 2 ? 8 : 5 }).map(
                    (_, j) => (
                      <div key={j} className="flex items-center gap-3">
                        <Skeleton
                          width="w-5"
                          height="h-5"
                          rounded="full"
                          className="flex-shrink-0"
                        />
                        <Skeleton
                          width={j % 2 === 0 ? "w-3/4" : "w-2/3"}
                          height="h-3.5"
                        />
                      </div>
                    ),
                  )}
                </div>
                {/* CTA button */}
                <Skeleton width="w-full" height="h-10" rounded="full" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FAQ skeleton ─── */}
      <section className="landing-section">
        <div className="flex flex-col items-center text-center mb-8">
          <Skeleton width="w-64" height="h-7" />
        </div>
        <div
          className="grid max-w-5xl mx-auto px-6"
          style={{
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "1.5rem",
          }}
        >
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
    </>
  );
}
