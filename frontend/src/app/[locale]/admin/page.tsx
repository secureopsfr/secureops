"use client";

/** Évite le prerender en CI : page admin authentifiée, logique runtime uniquement. */
export const dynamic = "force-dynamic";

import { useEffect, useState } from "react";
import {
  BarChart3,
  Eye,
  Mail,
  Send,
  Users,
  FileText,
  Bell,
  GalleryHorizontalEnd,
  LayoutDashboard,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import nextDynamic from "next/dynamic";
import AdminGuard from "../../../components/admin/AdminGuard";
import AdminHeader from "../../../components/admin/AdminHeader";
import { AdminInlineLoading } from "../../../components/admin/AdminSectionLoading";
import { useLanguage } from "../../../components/LanguageProvider";

// Lazy loading des composants admin via next/dynamic (ssr: false pour réduire le bundle initial)
const AdminOverview = nextDynamic(
  () => import("../../../components/admin/AdminOverview"),
  {
    loading: () => <AdminInlineLoading />,
    ssr: false,
  },
);
const UserManagement = nextDynamic(
  () => import("../../../components/admin/UserManagement"),
  {
    loading: () => <AdminInlineLoading />,
    ssr: false,
  },
);
const ApiMetrics = nextDynamic(
  () => import("../../../components/admin/ApiMetrics"),
  {
    loading: () => <AdminInlineLoading />,
    ssr: false,
  },
);
const SiteAnalytics = nextDynamic(
  () => import("../../../components/admin/SiteAnalytics"),
  {
    loading: () => <AdminInlineLoading />,
    ssr: false,
  },
);
const ContactManagement = nextDynamic(
  () => import("../../../components/admin/ContactManagement"),
  {
    loading: () => <AdminInlineLoading />,
    ssr: false,
  },
);
const MailManagement = nextDynamic(
  () => import("../../../components/admin/MailManagement"),
  {
    loading: () => <AdminInlineLoading />,
    ssr: false,
  },
);
const ImageGallery = nextDynamic(
  () => import("../../../components/admin/ImageGallery"),
  {
    loading: () => <AdminInlineLoading />,
    ssr: false,
  },
);
const AuditLog = nextDynamic(
  () => import("../../../components/admin/AuditLog"),
  {
    loading: () => <AdminInlineLoading message="Chargement de la section..." />,
    ssr: false,
  },
);
const AlertingDashboard = nextDynamic(
  () => import("../../../components/admin/AlertingDashboard"),
  {
    loading: () => <AdminInlineLoading />,
    ssr: false,
  },
);

const MOBILE_BREAKPOINT = 768;

export default function AdminPage() {
  const { t, lp } = useLanguage();
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [showMobileWarning, setShowMobileWarning] = useState<boolean | null>(
    null,
  );

  const tabs = [
    { id: "overview", label: t("admin.tabs.overview"), icon: LayoutDashboard },
    { id: "users", label: t("admin.tabs.users"), icon: Users },
    { id: "metrics", label: t("admin.tabs.apiMetrics"), icon: BarChart3 },
    { id: "analytics", label: t("admin.tabs.siteMetrics"), icon: Eye },
    { id: "contact", label: t("admin.tabs.contact"), icon: Mail },
    { id: "emails", label: t("admin.tabs.emails"), icon: Send },
    {
      id: "gallery",
      label: t("admin.tabs.gallery"),
      icon: GalleryHorizontalEnd,
    },
    { id: "audit", label: t("admin.tabs.audit"), icon: FileText },
    { id: "alerts", label: t("admin.tabs.alerts"), icon: Bell },
  ];

  // Empêcher le scroll horizontal et supprimer le padding-top du body
  useEffect(() => {
    document.body.style.overflowX = "hidden";
    document.documentElement.style.overflowX = "hidden";
    document.body.style.paddingTop = "0";

    return () => {
      document.body.style.overflowX = "";
      document.documentElement.style.overflowX = "";
      document.body.style.paddingTop = "";
    };
  }, []);

  // Afficher l’avertissement mobile une fois la largeur connue (client)
  useEffect(() => {
    const isMobile =
      typeof window !== "undefined" && window.innerWidth < MOBILE_BREAKPOINT;
    setShowMobileWarning(isMobile);
  }, []);

  return (
    <AdminGuard>
      <>
        {/* Popup d’avertissement sur mobile */}
        {showMobileWarning === true && (
          <div
            className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            role="alertdialog"
            aria-labelledby="admin-mobile-warning-title"
            aria-describedby="admin-mobile-warning-desc"
          >
            <div className="bg-[var(--bg)] border border-[var(--color-border)] rounded-xl shadow-xl max-w-sm w-full p-6 text-center">
              <h2
                id="admin-mobile-warning-title"
                className="text-lg font-semibold text-[var(--color-text)] mb-3"
              >
                {t("admin.mobileWarningTitle")}
              </h2>
              <p
                id="admin-mobile-warning-desc"
                className="text-[var(--color-text-muted)] text-sm leading-relaxed mb-6"
              >
                {t("admin.mobileWarningMessage")}
              </p>
              <button
                type="button"
                onClick={() => setShowMobileWarning(false)}
                className="btn btn-primary w-full"
              >
                {t("admin.mobileWarningContinue")}
              </button>
            </div>
          </div>
        )}
        {/* Logo et nom en haut à gauche */}
        <div className="fixed-logo">
          <Link href={lp("/")} className="logo">
            <Image
              src="/logo.png"
              alt="SecureOps Logo"
              width={40}
              height={40}
            />
            <span className="logo-brand">
              Secure<span>Ops</span>
            </span>
          </Link>
        </div>

        <div className="min-h-screen bg-theme" style={{ paddingTop: 0 }}>
          <div className="flex flex-col min-h-screen w-full">
            {/* Zone de contenu scrollable */}
            <div
              id="admin-content-container"
              className="flex-1 overflow-y-auto min-h-0 w-full flex justify-center pt-20"
            >
              <div className="space-y-6 pb-8 w-full max-w-[1400px] px-8">
                <AdminHeader />

                {/* Onglets */}
                <div className="text-center mb-8">
                  <nav
                    className="inline-flex gap-2 flex-wrap justify-center"
                    aria-label="Tabs"
                  >
                    {tabs.map((tab) => {
                      const isActive = activeTab === tab.id;
                      return (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          style={{
                            padding: "0.5rem 1rem",
                            background: isActive
                              ? "rgba(var(--primary), 0.2)"
                              : "transparent",
                            border: "1px solid var(--border)",
                            borderRadius: "0.5rem",
                            cursor: "pointer",
                            color: isActive
                              ? "rgb(var(--primary))"
                              : "var(--text)",
                            fontWeight: isActive ? "bold" : "normal",
                            transition: "all 0.2s",
                          }}
                          onMouseEnter={(e) => {
                            if (!isActive) {
                              e.currentTarget.style.background =
                                "var(--color-surface-input)";
                            }
                          }}
                          onMouseLeave={(e) => {
                            if (!isActive) {
                              e.currentTarget.style.background = "transparent";
                            }
                          }}
                        >
                          {tab.label}
                        </button>
                      );
                    })}
                  </nav>
                </div>

                {/* Contenu des onglets — lazy loading géré par next/dynamic */}
                {activeTab === "overview" && (
                  <AdminOverview onNavigate={setActiveTab} />
                )}
                {activeTab === "users" && <UserManagement />}
                {activeTab === "metrics" && <ApiMetrics />}
                {activeTab === "analytics" && <SiteAnalytics />}
                {activeTab === "contact" && <ContactManagement />}
                {activeTab === "emails" && <MailManagement />}
                {activeTab === "gallery" && <ImageGallery />}
                {activeTab === "audit" && <AuditLog />}
                {activeTab === "alerts" && <AlertingDashboard />}
              </div>
            </div>
          </div>
        </div>
      </>
    </AdminGuard>
  );
}
