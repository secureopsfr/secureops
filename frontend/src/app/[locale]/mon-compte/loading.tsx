import Skeleton from "../../../components/ui/skeletons/Skeleton";
import AccountPageSkeleton from "../../../components/ui/skeletons/AccountPageSkeleton";

/**
 * Skeleton de chargement pour la page Mon Compte.
 * Reproduit la structure : Logo fixe, Sidebar (table of contents),
 * Zone principale avec les sections de compte en skeleton.
 */
export default function Loading() {
  return (
    <>
      {/* ─── Fixed logo skeleton ─── */}
      <div className="fixed-logo">
        <div className="flex items-center gap-2">
          <Skeleton width="w-10" height="h-10" rounded="lg" />
          <Skeleton width="w-28" height="h-5" className="hidden md:block" />
        </div>
      </div>

      <div className="fixed inset-0 bg-theme overflow-hidden">
        <div className="flex flex-row h-full">
          {/* ─── Sidebar skeleton (20%) ─── */}
          <div
            className="hidden md:block fixed top-0 left-0 z-10 shrink-0 overflow-y-auto overflow-x-hidden"
            style={{
              width: "20%",
              minWidth: "250px",
              backgroundColor: "var(--color-sidebar)",
              height: "100vh",
              borderRight: "1px solid var(--color-border)",
              paddingTop: "80px",
            }}
          >
            <div className="pt-4 px-6 space-y-3">
              {/* Table of contents items */}
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 py-2">
                  <Skeleton
                    width="w-3"
                    height="h-3"
                    rounded="full"
                    className="flex-shrink-0"
                  />
                  <Skeleton
                    width={
                      i === 0
                        ? "w-16"
                        : i === 1
                          ? "w-20"
                          : i === 2
                            ? "w-24"
                            : i === 3
                              ? "w-28"
                              : "w-32"
                    }
                    height="h-4"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* ─── Main content : pleine largeur mobile, 80% desktop ─── */}
          <div className="flex flex-col h-full w-full md:w-[80%] md:ml-[20%]">
            <div className="flex-1 overflow-y-auto min-h-0 w-full flex justify-center">
              <div className="space-y-4 md:space-y-6 w-full">
                <AccountPageSkeleton />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
