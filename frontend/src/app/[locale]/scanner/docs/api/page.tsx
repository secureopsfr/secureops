"use client";

import { useParams } from "next/navigation";
import Header from "../../../../../components/ui/Header";
import Footer from "../../../../../components/ui/Footer";
import { useLanguage } from "../../../../../components/LanguageProvider";
import { FileText } from "lucide-react";
import Link from "next/link";
import { localePath, type Locale } from "../../../../../i18n/config";
import { getApiBaseUrl } from "../../../../../utils/apiClient";

export default function ScannerApiDocPage() {
  const params = useParams();
  const locale = (params?.locale as string) || "fr";
  const { t } = useLanguage();
  const lp = (path: string) => localePath(locale as Locale, path);
  const baseUrl =
    typeof window !== "undefined"
      ? getApiBaseUrl()
      : process.env.NEXT_PUBLIC_GATEWAY_URL || "https://api.secureops.io";

  return (
    <>
      <Header />
      <main
        id="main"
        className="min-h-screen py-6 w-full flex justify-center scanner-page"
      >
        <div className="w-full max-w-[900px] px-8">
          <div className="text-center max-w-2xl mx-auto mb-8">
            <h1 className="page-title mb-2">{t("scanner.docsApi.title")}</h1>
            <p className="text-[var(--color-text-muted)]">
              {t("scanner.docsApi.intro")}
            </p>
          </div>
          <div className="scanner-doc-content space-y-8">
            <section>
              <h2 className="text-xl font-semibold text-[var(--text)] mb-4">
                {t("scanner.docsApi.authTitle")}
              </h2>
              <p className="text-[var(--color-text-muted)] mb-4">
                {t("scanner.docsApi.authDesc")}
              </p>
              <ul className="list-disc list-inside text-[var(--color-text-muted)] space-y-2 mb-4">
                <li>
                  <code className="bg-[var(--color-surface)] px-1.5 py-0.5 rounded text-sm">
                    X-API-Key: sk_xxx...
                  </code>
                </li>
                <li>
                  <code className="bg-[var(--color-surface)] px-1.5 py-0.5 rounded text-sm">
                    Authorization: Bearer sk_xxx...
                  </code>
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-[var(--text)] mb-4">
                {t("scanner.docsApi.scanFakeTitle")}
              </h2>
              <p className="text-[var(--color-text-muted)] mb-4">
                {t("scanner.docsApi.scanFakeDesc")}
              </p>
              <pre className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 overflow-x-auto text-sm font-mono">
                <code>
                  {`curl -X POST "${baseUrl}/scan/api/scan/async" \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"url":"https://example.com","scan_type":"backend","input":{}}'`}
                </code>
              </pre>
              <p className="text-sm text-[var(--color-text-muted)] mt-2">
                {t("scanner.docsApi.scanFakeResponse")}
              </p>
            </section>

            <section>
              <h2 className="text-xl font-semibold text-[var(--text)] mb-4">
                {t("scanner.docsApi.keysTitle")}
              </h2>
              <p className="text-[var(--color-text-muted)] mb-4">
                {t("scanner.docsApi.keysDesc")}
              </p>
              <Link
                href={lp("/scanner/cles-api")}
                className="inline-flex items-center gap-2 text-[rgb(var(--primary))] hover:underline"
              >
                <FileText className="w-4 h-4" />
                {t("scanner.clesApi.title")}
              </Link>
            </section>
          </div>
        </div>
      </main>
      <Footer locale={locale} />
    </>
  );
}
