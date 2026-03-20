"use client";

import Image from "next/image";
import Link from "next/link";
import { GenericButton } from "../../../components/buttons";
import { PasswordInput } from "../../../components/inputs";
import { useLanguage } from "../../../components/LanguageProvider";

interface LoginFormProps {
  email: string;
  password: string;
  loading: boolean;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  t: (key: string) => string;
}

export default function LoginForm({
  email,
  password,
  loading,
  onEmailChange,
  onPasswordChange,
  onSubmit,
  t,
}: LoginFormProps) {
  const { lp } = useLanguage();

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <Image
            src="/logo.png"
            alt="Logo"
            width={80}
            height={80}
            className="auth-logo"
            priority
          />
          <h2 className="auth-title">{t("auth.login.title")}</h2>
          <p className="auth-subtitle">{t("auth.login.subtitle")}</p>
        </div>

        <div className="space-y-4 flex-1 overflow-y-auto">
          <form onSubmit={onSubmit} className="space-y-3">
            <div>
              <label htmlFor="email" className="label-form">
                {t("auth.login.emailLabel")}
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => onEmailChange(e.target.value)}
                className="auth-input"
                placeholder={t("auth.login.emailPlaceholder")}
                disabled={loading}
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="label-form">
                {t("auth.login.passwordLabel")}
              </label>
              <PasswordInput
                id="password"
                value={password}
                onChange={(e) => onPasswordChange(e.target.value)}
                placeholder="••••••••"
                disabled={loading}
                required
              />
              <div className="flex justify-end mt-1">
                <Link
                  href={lp("/mot-de-passe-oublie")}
                  className="text-xs hover:opacity-80 transition-opacity text-accent"
                >
                  {t("auth.login.forgotPassword")}
                </Link>
              </div>
            </div>

            <GenericButton
              type="submit"
              label={t("auth.login.submitBtn")}
              loading={loading}
              loadingLabel={t("auth.login.loadingBtn")}
              disabled={loading}
              variant="primary"
              className="w-full min-w-[200px]"
            />
          </form>
        </div>

        <div className="auth-footer">
          <p>
            {t("auth.login.noAccount")}{" "}
            <Link
              href={lp("/inscription")}
              className="hover:opacity-80 transition-opacity font-medium text-accent"
            >
              {t("auth.login.signUpLink")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
