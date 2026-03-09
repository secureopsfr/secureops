"use client";

import "./scanner-doc.css";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import Header from "../../../../../components/ui/Header";
import { useDocBlockReveal } from "../../../../../hooks/useDocBlockReveal";
import Footer from "../../../../../components/ui/Footer";
import { useLanguage } from "../../../../../components/LanguageProvider";
import { getDocBySlug } from "../../../../../services/docsService";
import { localePath, type Locale } from "../../../../../i18n/config";
import { FileText } from "lucide-react";

export default function ScannerDocDetailPage() {
  const params = useParams();
  const slug = params?.slug as string;
  const locale = (params?.locale as string) || "fr";
  const lp = (path: string) => localePath(locale as Locale, path);
  const { t } = useLanguage();
  const [content, setContent] = useState<string | null>(null);
  const [title, setTitle] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const articleRef = useRef<HTMLElement>(null);
  useDocBlockReveal(articleRef, content);

  useEffect(() => {
    if (!slug) return;
    getDocBySlug(slug)
      .then((doc) => {
        setContent(doc.content);
        setTitle(doc.title);
      })
      .catch(() => setError("Page introuvable"))
      .finally(() => setLoading(false));
  }, [slug]);

  return (
    <>
      <Header />
      <main
        id="main"
        className="min-h-screen py-6 w-full flex justify-center scanner-page"
      >
        <div className="w-full max-w-[900px] px-8">
          <Link
            href={lp("/scanner/docs")}
            className="inline-flex items-center gap-1 text-[rgb(var(--primary))] no-underline hover:underline mb-6"
          >
            ← {t("scanner.docs.backToList")}
          </Link>

          {loading ? (
            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-12 text-center">
              <p className="text-[var(--color-text-muted)]">
                {t("scanner.docs.loading")}
              </p>
            </div>
          ) : error ? (
            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-12 text-center">
              <FileText className="w-12 h-12 text-[var(--muted)] mx-auto mb-4 opacity-40" />
              <p className="text-[rgb(var(--danger))]">{error}</p>
              <Link
                href={lp("/scanner/docs")}
                className="inline-block mt-4 text-[rgb(var(--primary))] hover:underline"
              >
                {t("scanner.docs.backToList")}
              </Link>
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
