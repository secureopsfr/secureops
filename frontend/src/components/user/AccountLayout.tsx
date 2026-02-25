"use client";

import React, { useLayoutEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import TableOfContents from "../TableOfContents";
import { useLanguage } from "../LanguageProvider";

interface AccountLayoutProps {
  children: React.ReactNode;
}

const SECTIONS = [
  { id: "profile", key: "account.sections.profile" },
  { id: "security", key: "account.sections.security" },
  { id: "settings", key: "account.sections.settings" },
  { id: "subscription", key: "account.sections.subscription" },
  { id: "privacy", key: "account.sections.privacy" },
] as const;

/**
 * Layout component for the account page.
 * Handles: fixed logo, sidebar table-of-contents, scrollable content area,
 * and the body overflow / padding-top overrides.
 */
export default function AccountLayout({ children }: AccountLayoutProps) {
  const { t, lp } = useLanguage();

  const userSections = SECTIONS.map((s) => ({ id: s.id, title: t(s.key) }));

  const scrollToSection = useCallback((sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      const container = document.getElementById("user-sections-container");
      if (container) {
        const offset = 20;
        const targetTop = element.offsetTop - offset;
        container.scrollTo({ top: targetTop, behavior: "smooth" });
      }
    }
  }, []);

  // Prevent horizontal scroll & remove body padding-top before first paint
  useLayoutEffect(() => {
    document.body.style.overflowX = "hidden";
    document.documentElement.style.overflowX = "hidden";
    document.body.style.paddingTop = "0";

    return () => {
      document.body.style.overflowX = "";
      document.documentElement.style.overflowX = "";
      document.body.style.paddingTop = "";
    };
  }, []);

  return (
    <>
      {/* Fixed logo */}
      <div className="fixed-logo">
        <Link href={lp("/")} className="logo">
          <Image src="/logo.png" alt="SecureOps Logo" width={40} height={40} />
          <span className="logo-brand hidden md:inline">
            Secure<span>Ops</span>
          </span>
        </Link>
      </div>

      <div className="fixed inset-0 bg-theme overflow-hidden">
        <div className="flex flex-row h-full">
          {/* Sidebar (20% desktop, hidden on mobile) */}
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
            <div className="pt-4">
              <TableOfContents
                sections={userSections}
                onSectionClick={scrollToSection}
                containerId="user-sections-container"
                title=""
              />
            </div>
          </div>

          {/* Scrollable content area : pleine largeur mobile, 80% desktop */}
          <div className="flex flex-col h-full w-full md:w-[80%] md:ml-[20%]">
            <div
              id="user-sections-container"
              className="flex-1 overflow-y-auto min-h-0 w-full flex justify-center"
            >
              <div className="space-y-4 md:space-y-6 pt-6 w-full px-8">
                {children}
                <div className="h-[1px]" aria-hidden="true" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
