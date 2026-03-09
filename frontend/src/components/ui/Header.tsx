"use client";

import { useState, useCallback, useEffect } from "react";
import { signOut } from "aws-amplify/auth";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { Sun, Moon, Globe, Menu, X } from "lucide-react";
import { showSuccessToast } from "../../utils/toastNotifications";
import { GenericButton } from "../buttons";
import { useTheme } from "../ThemeProvider";
import { useLanguage } from "../LanguageProvider";
import type { Language } from "../LanguageProvider";

import logger from "../../utils/logger";
import { useAuthUser } from "../../hooks/useAuthUser";

export default function Header() {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, t, lp } = useLanguage();
  const { isAuthenticated, isLoading, recheck } = useAuthUser({
    listenToAuthEvents: true,
  });
  const [menuOpen, setMenuOpen] = useState(false);
  const [closing, setClosing] = useState(false);

  const DRAWER_CLOSE_DURATION_MS = 250;

  const closeMenu = useCallback(() => {
    if (closing) return;
    setClosing(true);
    setTimeout(() => {
      setMenuOpen(false);
      setClosing(false);
    }, DRAWER_CLOSE_DURATION_MS);
  }, [closing]);

  useEffect(() => {
    if (!menuOpen) return;
    const onEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeMenu();
    };
    document.addEventListener("keydown", onEscape);
    return () => document.removeEventListener("keydown", onEscape);
  }, [menuOpen, closeMenu]);

  const navLinks = [
    { label: t("header.home"), href: lp("/") },
    ...(isAuthenticated
      ? [{ label: t("header.scanner"), href: lp("/scanner") }]
      : []),
    { label: t("header.pricing"), href: lp("/tarifs") },
    { label: t("header.contact"), href: lp("/contact") },
  ];

  const handleSignOut = async () => {
    try {
      sessionStorage.removeItem("justLoggedIn");

      Object.keys(localStorage).forEach((key) => {
        if (
          key.startsWith("CognitoIdentityServiceProvider") ||
          key.includes("amplify") ||
          key.includes("aws-amplify")
        ) {
          localStorage.removeItem(key);
        }
      });

      Object.keys(sessionStorage).forEach((key) => {
        if (
          key.startsWith("CognitoIdentityServiceProvider") ||
          key.includes("amplify") ||
          key.includes("aws-amplify")
        ) {
          sessionStorage.removeItem(key);
        }
      });

      await signOut();

      localStorage.setItem("auth:signOut", Date.now().toString());
      localStorage.removeItem("auth:signOut");

      window.dispatchEvent(new CustomEvent("auth:signOut"));

      recheck();
      showSuccessToast(t("header.signOutSuccess"));
      router.push(lp("/"));
    } catch (err) {
      logger.error(t("header.signOutError"), err);
      recheck();
      router.push(lp("/"));
    }
  };

  const toggleLanguage = () => {
    const newLang: Language = language === "en" ? "fr" : "en";
    setLanguage(newLang);
  };

  const langLabel = language === "en" ? "FR" : "EN";
  const themeLabel =
    theme === "dark" ? t("header.lightMode") : t("header.darkMode");

  return (
    <header className={menuOpen ? "z-[50]" : undefined}>
      <div className="nav">
        <Link href={lp("/")} className="logo">
          <Image src="/logo.png" alt="SecureOps Logo" width={40} height={40} />
          <span className="hidden md:inline">
            Secure<span style={{ color: "rgb(var(--primary))" }}>Ops</span>
          </span>
        </Link>
        <nav className="nav-links hidden md:flex">
          {navLinks.map((link) => (
            <Link key={link.href} href={link.href}>
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="nav-cta flex items-center gap-2 justify-self-end">
          <div className="hidden md:flex md:gap-2 md:items-center">
            {!isLoading && !isAuthenticated && (
              <>
                <button
                  onClick={toggleLanguage}
                  className="btn btn-secondary p-2 rounded-full"
                  style={{ cursor: "pointer" }}
                  aria-label={
                    language === "en" ? "Switch to French" : "Passer en anglais"
                  }
                  title={langLabel}
                >
                  <Globe className="w-4 h-4" />
                </button>
                <button
                  onClick={toggleTheme}
                  className="btn btn-secondary p-2 rounded-full"
                  style={{ cursor: "pointer" }}
                  aria-label={
                    theme === "dark"
                      ? t("header.switchToLight")
                      : t("header.switchToDark")
                  }
                  title={themeLabel}
                >
                  {theme === "dark" ? (
                    <Sun className="w-4 h-4" />
                  ) : (
                    <Moon className="w-4 h-4" />
                  )}
                </button>
              </>
            )}
            {!isLoading &&
              (isAuthenticated ? (
                <>
                  <GenericButton
                    label={t("header.myAccount")}
                    href={lp("/mon-compte")}
                    variant="secondary"
                  />
                  <GenericButton
                    label={t("header.signOut")}
                    onClick={handleSignOut}
                    variant="primary"
                  />
                </>
              ) : (
                <>
                  <GenericButton
                    label={t("header.signIn")}
                    href={lp("/connexion")}
                    variant="secondary"
                  />
                  <GenericButton
                    label={t("header.signUp")}
                    href={lp("/inscription")}
                    variant="primary"
                  />
                </>
              ))}
          </div>
          <button
            type="button"
            onClick={menuOpen ? closeMenu : () => setMenuOpen(true)}
            className="md:hidden btn btn-secondary p-2.5 rounded-full"
            aria-label={menuOpen ? t("header.closeMenu") : t("header.openMenu")}
          >
            {menuOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      {/* Volet mobile */}
      {(menuOpen || closing) && (
        <>
          <div
            className={`fixed inset-0 z-30 bg-black/50 backdrop-blur-sm md:hidden transition-opacity duration-[250ms] ${
              closing ? "opacity-0" : "opacity-100"
            }`}
            aria-hidden
            onClick={closeMenu}
          />
          <div
            className={`header-drawer-panel fixed top-0 right-0 bottom-0 z-40 w-[min(320px,85vw)] bg-[var(--bg)] border-l border-[var(--color-border)] shadow-xl flex flex-col md:hidden ${
              closing ? "header-drawer-panel--closing" : ""
            }`}
            role="dialog"
            aria-modal="true"
            aria-label={t("header.menu")}
          >
            <div className="flex items-center justify-between p-4 border-b border-[var(--color-border)] shrink-0">
              <span className="font-semibold text-[var(--color-text)]">
                {t("header.menu")}
              </span>
              <button
                type="button"
                onClick={closeMenu}
                className="p-2 rounded-full hover:bg-[var(--color-surface)] transition-colors"
                aria-label={t("header.closeMenu")}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex flex-col gap-1 p-4 overflow-y-auto">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={closeMenu}
                  className="py-3 px-4 rounded-lg text-[var(--color-text)] hover:bg-[var(--color-surface)] transition-colors"
                >
                  {link.label}
                </Link>
              ))}
              <div className="h-px bg-[var(--color-border)] my-2" />
              {!isLoading && !isAuthenticated && (
                <div className="flex gap-2 py-2">
                  <button
                    onClick={() => {
                      toggleLanguage();
                    }}
                    className="btn btn-secondary p-2 rounded-full"
                    aria-label={langLabel}
                    title={langLabel}
                  >
                    <Globe className="w-4 h-4" />
                  </button>
                  <button
                    onClick={toggleTheme}
                    className="btn btn-secondary p-2 rounded-full"
                    aria-label={themeLabel}
                    title={themeLabel}
                  >
                    {theme === "dark" ? (
                      <Sun className="w-4 h-4" />
                    ) : (
                      <Moon className="w-4 h-4" />
                    )}
                  </button>
                </div>
              )}
              {!isLoading &&
                (isAuthenticated ? (
                  <div className="flex flex-col gap-2 pt-2">
                    <Link
                      href={lp("/mon-compte")}
                      onClick={closeMenu}
                      className="btn btn-secondary text-center"
                    >
                      {t("header.myAccount")}
                    </Link>
                    <button
                      type="button"
                      onClick={() => {
                        closeMenu();
                        handleSignOut();
                      }}
                      className="btn btn-primary"
                    >
                      {t("header.signOut")}
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col gap-2 pt-2">
                    <Link
                      href={lp("/connexion")}
                      onClick={closeMenu}
                      className="btn btn-secondary text-center"
                    >
                      {t("header.signIn")}
                    </Link>
                    <Link
                      href={lp("/inscription")}
                      onClick={closeMenu}
                      className="btn btn-primary text-center"
                    >
                      {t("header.signUp")}
                    </Link>
                  </div>
                ))}
            </div>
          </div>
        </>
      )}
    </header>
  );
}
