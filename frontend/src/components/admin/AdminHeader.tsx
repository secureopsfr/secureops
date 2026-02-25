"use client";

import AdminInfo from "./AdminInfo";
import { useLanguage } from "../LanguageProvider";

/**
 * En-tête simple pour la page d'administration.
 */
export default function AdminHeader() {
  const { t } = useLanguage();

  return (
    <div style={{ textAlign: "center", marginBottom: "2rem" }}>
      <h1 style={{ margin: 0, marginBottom: "0.5rem" }}>
        {t("admin.header.title")}
      </h1>
      <p style={{ margin: 0 }}>{t("admin.header.description")}</p>
      <div
        style={{
          marginTop: "0.75rem",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <AdminInfo />
      </div>
    </div>
  );
}
