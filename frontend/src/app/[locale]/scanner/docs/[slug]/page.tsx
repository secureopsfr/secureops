"use client";

import "./scanner-doc.css";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import Header from "../../../../../components/ui/Header";
import { useDocBlockReveal } from "../../../../../hooks/useDocBlockReveal";
import Footer from "../../../../../components/ui/Footer";
import { useLanguage } from "../../../../../components/LanguageProvider";
import { getDocBySlug } from "../../../../../services/docsService";
import { FileText } from "lucide-react";

export default function ScannerDocDetailPage() {
  const params = useParams();
  const slug = params?.slug as string;
  const locale = (params?.locale as string) || "fr";
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
