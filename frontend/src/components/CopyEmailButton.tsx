"use client";

import { useState, useRef, useEffect } from "react";

interface CopyEmailButtonProps {
  email: string;
  copyLabel: string;
  copiedLabel: string;
  ariaLabel: string;
}

/**
 * Client component — handles clipboard copy interaction for the footer email.
 */
export default function CopyEmailButton({
  email,
  copyLabel,
  copiedLabel,
  ariaLabel,
}: CopyEmailButtonProps) {
  const [isEmailCopied, setIsEmailCopied] = useState(false);
  const copiedTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (copiedTimeoutRef.current) {
        window.clearTimeout(copiedTimeoutRef.current);
        copiedTimeoutRef.current = null;
      }
    };
  }, []);

  const handleCopyEmail = async () => {
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(email);
        setIsEmailCopied(true);
        if (copiedTimeoutRef.current) {
          window.clearTimeout(copiedTimeoutRef.current);
        }
        copiedTimeoutRef.current = window.setTimeout(
          () => setIsEmailCopied(false),
          1500,
        );
        return;
      }

      // Fallback for certain browsers / non-secure contexts
      const textarea = document.createElement("textarea");
      textarea.value = email;
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      textarea.style.top = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);

      setIsEmailCopied(true);
      if (copiedTimeoutRef.current) {
        window.clearTimeout(copiedTimeoutRef.current);
      }
      copiedTimeoutRef.current = window.setTimeout(
        () => setIsEmailCopied(false),
        1500,
      );
    } catch {
      // Don't block UX if copy fails
    }
  };

  return (
    <span className="relative inline-block">
      <button
        type="button"
        onClick={handleCopyEmail}
        className="bg-transparent border-none p-0 text-[rgb(var(--primary))] font-semibold cursor-pointer text-[inherit] font-[inherit]"
        title={copyLabel}
        aria-label={ariaLabel}
      >
        {email}
      </button>
      {isEmailCopied && (
        <span
          role="status"
          aria-live="polite"
          className="absolute top-full left-0 mt-1 inline-flex items-center rounded-lg bg-[rgba(var(--primary),0.15)] border border-[rgba(var(--primary),0.3)] px-2 py-1 text-xs font-semibold text-[rgb(var(--primary))] whitespace-nowrap z-10"
        >
          {copiedLabel}
        </span>
      )}
    </span>
  );
}
