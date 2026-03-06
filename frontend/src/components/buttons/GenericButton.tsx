"use client";

import React from "react";
import { useLanguage } from "../LanguageProvider";

interface Option {
  value: string;
  label: string;
  disabled?: boolean;
}

interface GenericButtonProps {
  label: string;
  onClick?: () => void;
  href?: string;
  options?: Option[];
  selectedValue?: string;
  onChange?: (value: string) => void;
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  width?: string;
  height?: string;
  disabled?: boolean;
  loading?: boolean;
  loadingLabel?: string;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  className?: string;
  fullWidth?: boolean;
  type?: "button" | "submit" | "reset";
  style?: React.CSSProperties;
}

// Spinner de chargement (défini hors du composant pour éviter les re-créations)
const LoadingSpinner = ({ variant }: { variant: string }) => {
  const spinnerColor =
    variant === "primary" ? "var(--color-btn-primary-text)" : "currentColor";
  return (
    <span
      className="inline-flex items-center mr-2 flex-shrink-0"
      style={{
        display: "inline-flex",
        alignItems: "center",
        marginRight: "0.5rem",
      }}
    >
      <svg
        className="h-5 w-5"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        style={{
          display: "inline-block",
          animation: "spin 1s linear infinite",
          color: spinnerColor,
        }}
      >
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke={spinnerColor}
          strokeOpacity="0.25"
          strokeWidth="4"
          fill="none"
        ></circle>
        <path
          fill={spinnerColor}
          fillOpacity="0.75"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>
    </span>
  );
};

/**
 * Composant bouton générique basé sur le DropdownSelector
 * Peut fonctionner comme un bouton simple ou un dropdown selon les props
 */
const GenericButton: React.FC<GenericButtonProps> = ({
  label,
  onClick,
  href,
  options = [],
  selectedValue,
  onChange,
  variant = "primary",
  size = "md",
  width,
  height,
  disabled = false,
  loading = false,
  loadingLabel,
  icon,
  iconPosition = "left",
  className = "",
  fullWidth = false,
  type = "button",
  style,
}) => {
  const { t } = useLanguage();
  // Déterminer si c'est un dropdown ou un bouton simple
  const isDropdown = options.length > 0 && onChange;

  // Utiliser les classes CSS existantes pour primary/secondary/outline
  const useCssClasses =
    variant === "primary" || variant === "secondary" || variant === "outline";

  // Styles de base selon la variante adaptés au thème sombre
  const variantStyles = {
    primary: useCssClasses
      ? "btn btn-primary"
      : "bg-gradient-to-r from-[rgb(var(--secondary))] to-[rgb(var(--primary))] text-[var(--color-btn-primary-text)] hover:opacity-90 border-transparent",
    secondary: useCssClasses
      ? "btn btn-secondary"
      : "bg-[var(--color-surface-input)] text-[var(--text)] hover:bg-[var(--color-surface-hover)] border-[var(--border)]",
    outline: useCssClasses
      ? "btn btn-secondary"
      : "bg-[var(--color-surface-input)] text-[var(--text)] hover:bg-[var(--color-surface-hover)] border-[var(--border)]",
    ghost:
      "bg-transparent text-[var(--text)] hover:bg-[var(--color-surface-input)] border-transparent",
    danger:
      "btn bg-[rgb(var(--danger))] text-white hover:opacity-90 border-transparent shadow-[0_10px_25px_rgba(var(--danger),0.35)]",
  };

  // Styles de taille (seulement si on n'utilise pas les classes CSS)
  const sizeStyles = {
    sm: { container: "h-7", text: "text-xs", padding: "px-2" },
    md: { container: "h-8", text: "text-sm", padding: "px-3" },
    lg: { container: "h-10", text: "text-base", padding: "px-4" },
  };

  // Déterminer les dimensions
  const containerHeight = useCssClasses
    ? ""
    : height || sizeStyles[size].container;
  const containerWidth = useCssClasses
    ? ""
    : width || (fullWidth ? "w-full" : "w-auto");

  // Classes de base du bouton
  const baseClasses =
    useCssClasses || variant === "danger"
      ? `${variantStyles[variant]} ${disabled ? "opacity-50 cursor-not-allowed" : ""} ${className}`
      : `
      group relative inline-flex items-center justify-center
      border rounded-full
      font-medium whitespace-nowrap
      transition-all duration-200
      ${variantStyles[variant]}
      ${containerHeight}
      ${containerWidth}
      ${sizeStyles[size].text}
      ${sizeStyles[size].padding}
      ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
      ${className}
    `
          .trim()
          .replace(/\s+/g, " ");

  // Pour le mode dropdown
  if (isDropdown) {
    const selectedOption = options.find((opt) => opt.value === selectedValue);
    const displayLabel = selectedOption ? selectedOption.label : label;

    return (
      <div className={`${baseClasses} relative`}>
        <div className="flex items-center justify-between w-full">
          {icon && iconPosition === "left" && (
            <span className="mr-2 flex-shrink-0">{icon}</span>
          )}

          <span className="flex-1 truncate">
            {loading ? (loadingLabel ?? t("common.loading")) : displayLabel}
          </span>

          {icon && iconPosition === "right" && !isDropdown && (
            <span className="ml-2 flex-shrink-0">{icon}</span>
          )}

          {/* Flèche dropdown */}
          <svg
            className="w-4 h-4 ml-2 transition-transform duration-300 ease-in-out group-hover:rotate-180 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>

        {/* Menu dropdown */}
        {!disabled && !loading && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-[var(--color-overlay-panel)] backdrop-blur-sm border border-[var(--border)] rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-[1000]">
            {options.map((option) => (
              <div
                key={option.value}
                onClick={() => !option.disabled && onChange?.(option.value)}
                className={`px-3 py-2 text-sm font-medium transition-colors truncate ${
                  option.disabled
                    ? "text-[var(--muted)] opacity-50 cursor-not-allowed"
                    : selectedValue === option.value
                      ? "bg-[rgba(var(--primary),0.2)] text-[rgb(var(--primary))] cursor-pointer"
                      : "hover:bg-[var(--color-surface-input)] text-[var(--text)] cursor-pointer"
                }`}
              >
                {option.label}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Mode bouton simple
  const buttonStyle =
    useCssClasses || variant === "danger"
      ? {
          ...style,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "0.5rem",
        }
      : style;

  const content = loading ? (
    <>
      <LoadingSpinner variant={variant} />
      <span>{loadingLabel ?? t("common.loading")}</span>
    </>
  ) : (
    <>
      {icon && iconPosition === "left" && (
        <span className="mr-2 flex-shrink-0">{icon}</span>
      )}
      <span className="truncate">{label}</span>
      {icon && iconPosition === "right" && (
        <span className="ml-2 flex-shrink-0">{icon}</span>
      )}
    </>
  );

  // Si href est fourni, rendre un lien
  if (href) {
    return (
      <a
        href={href}
        onClick={!disabled && !loading ? onClick : undefined}
        className={baseClasses}
        style={buttonStyle}
        aria-disabled={disabled || loading}
      >
        {content}
      </a>
    );
  }

  // Sinon, rendre un bouton
  return (
    <button
      type={type}
      onClick={!disabled && !loading ? onClick : undefined}
      disabled={disabled || loading}
      className={baseClasses}
      style={buttonStyle}
      form={type === "submit" ? undefined : undefined} // Ne pas spécifier form pour laisser le formulaire parent gérer
    >
      {content}
    </button>
  );
};

export default GenericButton;
