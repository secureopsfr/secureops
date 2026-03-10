"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Header from "../../../../components/ui/Header";
import Footer from "../../../../components/ui/Footer";
import { useLanguage } from "../../../../components/LanguageProvider";
import { getDocsList } from "../../../../services/docsService";
import type { DocPageRecord } from "../../../../services/docsService";
import { localePath, type Locale } from "../../../../i18n/config";
import { FileText } from "lucide-react";
import LoadingScreen from "../../../../components/LoadingScreen";

export default function ScannerDocsPage() {
  const params = useParams();
  const locale = (params?.locale as string) || "fr";
  const lp = (path: string) => localePath(locale as Locale, path);
  const { t } = useLanguage();
  const [docs, setDocs] = useState<DocPageRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDocsList()
      .then((res) => setDocs(res.docs))
      .catch(() => setError("Impossible de charger la documentation"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Header />
      <main
        id="main"
        className="min-h-screen py-6 w-full flex justify-center scanner-page"
      >
        <div className="w-full max-w-[1400px] px-8">
          <div className="text-center max-w-2xl mx-auto mb-8">
            <h1 className="page-title mb-2">{t("scanner.docs.title")}</h1>
            <p className="text-[var(--color-text-muted)]">
              {t("scanner.docs.intro")}
            </p>
          </div>

          {loading ? (
            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
              <LoadingScreen
                variant="section"
                message={t("scanner.docs.loading")}
              />
            </div>
          ) : error ? (
            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-12 text-center">
              <p className="text-[rgb(var(--danger))]">{error}</p>
            </div>
          ) : docs.length === 0 ? (
            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-12 text-center">
              <FileText className="w-12 h-12 text-[var(--muted)] mx-auto mb-4 opacity-40" />
              <p className="text-[var(--color-text-muted)]">
                {t("scanner.docs.empty")}
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {docs.map((doc) => (
                <Link
                  key={doc.slug}
                  href={lp(`/scanner/docs/${doc.slug}`)}
                  className="flex items-center gap-4 p-6 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[rgb(var(--primary))] hover:bg-[rgba(var(--primary),0.05)] transition-colors no-underline h-full min-h-[120px]"
                >
                  <div className="w-10 h-10 rounded-lg bg-[rgba(var(--primary),0.1)] flex items-center justify-center flex-shrink-0">
                    <FileText className="w-5 h-5 text-[rgb(var(--primary))]" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h2 className="text-lg font-semibold text-[var(--text)] mb-1 line-clamp-2">
                      {doc.title}
                    </h2>
                    <p className="text-sm text-[var(--color-text-muted)]">
                      <code className="text-xs">{doc.slug}</code>
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
      <Footer locale={locale} />
    </>
  );
}
