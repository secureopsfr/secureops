"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  Copy,
  ExternalLink,
  Loader2,
  Shield,
} from "lucide-react";
import { useLanguage } from "../LanguageProvider";
import {
  createDomainChallenge,
  deleteDomainVerification,
  listDomainVerifications,
  verifyDomain,
  type DomainVerificationChallengeResponse,
  type DomainVerificationItem,
} from "../../services/domainVerificationService";
import { GenericButton } from "../buttons";

interface Props {
  scanUrl: string;
  t: (key: string) => string;
}

export default function DomainVerificationSection({ scanUrl, t }: Props) {
  const { lp } = useLanguage();
  const [list, setList] = useState<DomainVerificationItem[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [challenge, setChallenge] =
    useState<DomainVerificationChallengeResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshList = useCallback(async () => {
    setLoadingList(true);
    setError(null);
    try {
      const rows = await listDomainVerifications();
      setList(rows);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  const handleGenerate = async () => {
    const u = scanUrl.trim();
    if (!u) {
      setError(t("scanner.domainVerificationNeedUrl"));
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const c = await createDomainChallenge(u);
      setChallenge(c);
      await refreshList();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const handleVerify = async () => {
    const domain = challenge?.domain;
    if (!domain) return;
    setBusy(true);
    setError(null);
    try {
      await verifyDomain(domain);
      setChallenge(null);
      await refreshList();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const copyText = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      setError(t("scanner.domainVerificationCopyFailed"));
    }
  };

  const handleDelete = async (id: string) => {
    setBusy(true);
    setError(null);
    try {
      await deleteDomainVerification(id);
      await refreshList();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-lg border border-[rgba(var(--primary),0.25)] bg-[rgba(var(--primary),0.06)] px-4 py-3 space-y-3">
      <div className="flex items-start gap-2">
        <Shield className="w-5 h-5 shrink-0 text-[rgb(var(--primary))] mt-0.5" />
        <div className="space-y-1 min-w-0">
          <h3 className="text-sm font-semibold text-[var(--text)]">
            {t("scanner.domainVerificationTitle")}
          </h3>
          <p className="text-xs text-[var(--muted)] leading-relaxed">
            {t("scanner.domainVerificationIntro")}
          </p>
          <p className="text-xs mt-1.5">
            <Link
              href={lp("/scanner/docs/verification-dns")}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[rgb(var(--primary))] hover:underline font-medium"
            >
              {t("scanner.domainVerificationDocLink")}
              <ExternalLink
                className="w-3.5 h-3.5 shrink-0 opacity-80"
                aria-hidden
              />
            </Link>
          </p>
        </div>
      </div>

      {error && (
        <p className="text-xs text-[rgb(var(--danger))]" role="alert">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <GenericButton
          type="button"
          variant="secondary"
          disabled={busy}
          loading={busy}
          loadingLabel={t("scanner.domainVerificationGenerate")}
          label={t("scanner.domainVerificationGenerate")}
          onClick={() => void handleGenerate()}
        />
        {challenge && !challenge.already_verified && challenge.txt_value ? (
          <GenericButton
            type="button"
            variant="primary"
            disabled={busy}
            loading={busy}
            loadingLabel={t("scanner.domainVerificationVerify")}
            label={t("scanner.domainVerificationVerify")}
            onClick={() => void handleVerify()}
          />
        ) : null}
      </div>

      {challenge && (
        <div className="text-xs space-y-2 font-mono bg-[var(--surface)] rounded-md p-3 border border-[var(--border)]">
          {challenge.already_verified ? (
            <p className="flex items-center gap-1.5 text-[rgb(var(--success))]">
              <CheckCircle2 className="w-4 h-4" />
              {t("scanner.domainVerificationAlreadyOk")}
            </p>
          ) : (
            <>
              <div>
                <span className="text-[var(--muted)] block mb-0.5">
                  {t("scanner.domainVerificationTxtName")}
                </span>
                <div className="flex items-center gap-1 flex-wrap">
                  <code className="break-all">{challenge.txt_name}</code>
                  <button
                    type="button"
                    className="p-1 rounded hover:bg-[rgba(var(--primary),0.12)]"
                    aria-label={t("scanner.domainVerificationCopy")}
                    onClick={() => void copyText(challenge.txt_name)}
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              <div>
                <span className="text-[var(--muted)] block mb-0.5">
                  {t("scanner.domainVerificationTxtValue")}
                </span>
                <div className="flex items-center gap-1 flex-wrap">
                  <code className="break-all">{challenge.txt_value}</code>
                  <button
                    type="button"
                    className="p-1 rounded hover:bg-[rgba(var(--primary),0.12)]"
                    aria-label={t("scanner.domainVerificationCopy")}
                    onClick={() => void copyText(challenge.txt_value)}
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      <div>
        <p className="text-xs font-medium text-[var(--text)] mb-1.5">
          {t("scanner.domainVerificationListTitle")}
        </p>
        {loadingList ? (
          <Loader2 className="w-4 h-4 animate-spin text-[var(--muted)]" />
        ) : list.length === 0 ? (
          <p className="text-xs text-[var(--muted)]">
            {t("scanner.domainVerificationEmpty")}
          </p>
        ) : (
          <ul className="space-y-1.5">
            {list.map((row) => (
              <li
                key={row.id}
                className="flex flex-wrap items-center justify-between gap-2 text-xs border border-[var(--border)] rounded px-2 py-1.5"
              >
                <span className="font-medium">{row.domain}</span>
                <span className="text-[var(--muted)]">
                  {t("scanner.domainVerificationExpires")}{" "}
                  {new Date(row.expires_at).toLocaleDateString()}
                </span>
                <button
                  type="button"
                  className="text-[rgb(var(--danger))] hover:underline"
                  disabled={busy}
                  onClick={() => void handleDelete(row.id)}
                >
                  {t("scanner.domainVerificationRemove")}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
