"use client";

import "../[slug]/scanner-doc.css";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import Header from "../../../../../components/ui/Header";
import Footer from "../../../../../components/ui/Footer";
import { useLanguage } from "../../../../../components/LanguageProvider";
import { FileText } from "lucide-react";
import { getDocBySlug } from "../../../../../services/docsService";
import LoadingScreen from "../../../../../components/LoadingScreen";
import { useDocBlockReveal } from "../../../../../hooks/useDocBlockReveal";

export default function ScannerApiDocPage() {
  const params = useParams();
  const locale = (params?.locale as string) || "fr";
  const { t } = useLanguage();
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const articleRef = useRef<HTMLElement>(null);
  useDocBlockReveal(articleRef, content);

  useEffect(() => {
    getDocBySlug("api")
      .then((doc) => {
        setContent(doc.content);
        if (doc.title && typeof document !== "undefined") {
          document.title = `${doc.title} – SecureOps`;
        }
      })
      .catch(() => setError("Page introuvable"))
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
          {loading ? (
            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
              <LoadingScreen
                variant="section"
                message={t("scanner.docs.loading")}
              />
            </div>
          ) : error ? (
            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-12 text-center">
              <FileText className="w-12 h-12 text-[var(--muted)] mx-auto mb-4 opacity-40" />
              <p className="text-[rgb(var(--danger))]">{error}</p>
            </div>
          ) : content ? (
            <article
              ref={articleRef}
              className="scanner-doc-content"
              dangerouslySetInnerHTML={{ __html: content }}
            />
          ) : null}
        </div>
      </main>
      <Footer locale={locale} />
    </>
  );
}
