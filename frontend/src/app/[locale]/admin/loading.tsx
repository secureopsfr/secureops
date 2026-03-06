import Skeleton, {
  SkeletonButton,
} from "../../../components/ui/skeletons/Skeleton";

/**
 * Skeleton de chargement pour la page Admin.
 * Reproduit la structure : Logo fixe, Header (titre + description),
 * barre de tabs, contenu overview (KPI grid + listes).
 */
export default function Loading() {
  return (
    <>
      {/* ─── Fixed logo skeleton ─── */}
      <div className="fixed-logo">
        <div className="flex items-center gap-2">
          <Skeleton width="w-10" height="h-10" rounded="lg" />
          <Skeleton width="w-28" height="h-5" />
        </div>
      </div>

      <div className="min-h-screen bg-theme" style={{ paddingTop: 0 }}>
        <div className="flex flex-col min-h-screen w-full">
          <div className="flex-1 overflow-y-auto min-h-0 w-full flex justify-center pt-20">
            <div className="space-y-6 pb-8 w-full max-w-[1400px] px-8">
              {/* ─── Admin Header skeleton ─── */}
              <div className="text-center mb-8">
                <div className="flex justify-center mb-2">
                  <Skeleton width="w-72" height="h-8" />
                </div>
                <div className="flex justify-center mb-3">
                  <Skeleton width="w-96 max-w-full" height="h-4" />
                </div>
                {/* Admin info badge */}
                <div className="flex justify-center">
                  <Skeleton width="w-48" height="h-7" rounded="full" />
                </div>
              </div>

              {/* ─── Tabs skeleton ─── */}
              <div className="text-center mb-8">
                <div className="inline-flex gap-2 flex-wrap justify-center">
                  {Array.from({ length: 9 }).map((_, i) => (
                    <Skeleton
                      key={i}
                      width={i === 0 ? "w-24" : i % 3 === 0 ? "w-28" : "w-20"}
                      height="h-9"
                      rounded="lg"
                    />
                  ))}
                </div>
              </div>

              {/* ─── KPI grid skeleton (4 cards) ─── */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div
                    key={i}
                    className="p-5 rounded-xl border border-[var(--border)] bg-[var(--color-surface-subtle)]"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <Skeleton width="w-24" height="h-4" />
                      <Skeleton width="w-5" height="h-5" rounded="md" />
                    </div>
                    <Skeleton width="w-20" height="h-8" className="mb-1" />
                    <Skeleton width="w-16" height="h-3" />
                  </div>
                ))}
              </div>

              {/* ─── Overview list skeleton ─── */}
              <div className="p-6 rounded-xl border border-[var(--border)] bg-[var(--color-surface-subtle)]">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <Skeleton width="w-5" height="h-5" rounded="md" />
                    <Skeleton width="w-48" height="h-6" />
                  </div>
                  <SkeletonButton width="w-28" />
                </div>
                <div className="space-y-3">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-4 rounded-lg border border-[var(--border)] bg-[var(--color-surface-input)]"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <Skeleton width="w-8" height="h-8" rounded="full" />
                        <div className="space-y-1.5 flex-1">
                          <Skeleton width="w-40" height="h-4" />
                          <Skeleton width="w-24" height="h-3" />
                        </div>
                      </div>
                      <Skeleton width="w-20" height="h-6" rounded="full" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
