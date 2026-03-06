"use client";

import React from "react";

interface CheckboxProps {
  label: string | React.ReactNode;
  checked: boolean;
  onChange: (checked: boolean) => void;
  dataTestId?: string;
  disabled?: boolean;
  accentColor?: string;
}

const Checkbox: React.FC<CheckboxProps> = ({
  label,
  checked,
  onChange,
  dataTestId,
  disabled = false,
  accentColor,
}) => {
  return (
    <label
      style={{
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        gap: "0.5rem",
        fontSize: "0.875rem",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.6 : 1,
      }}
    >
      <div
        className="relative inline-flex items-center"
        style={{ width: "16px", height: "16px", flexShrink: 0 }}
      >
        <input
          type="checkbox"
          checked={checked}
          onChange={disabled ? undefined : (e) => onChange(e.target.checked)}
          disabled={disabled}
          data-testid={dataTestId}
          style={{
            position: "absolute",
            width: "16px",
            height: "16px",
            margin: 0,
            padding: 0,
            opacity: 0,
            cursor: disabled ? "not-allowed" : "pointer",
            zIndex: 10,
            appearance: "none",
            WebkitAppearance: "none",
            MozAppearance: "none",
          }}
        />
        <div
          style={{
            width: "16px",
            height: "16px",
            borderWidth: "2px",
            borderStyle: "solid",
            borderRadius: "3px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.2s",
            ...(checked
              ? accentColor
                ? {
                    borderColor: accentColor,
                    backgroundColor: accentColor,
                  }
                : {
                    backgroundColor: "rgb(80, 160, 255)",
                    borderColor: "rgb(80, 160, 255)",
                  }
              : {
                  borderColor: "var(--color-checkbox-border)",
                  backgroundColor: "transparent",
                }),
            ...(disabled ? { opacity: 0.5 } : {}),
          }}
        >
          {checked && (
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              style={{
                display: "block",
                color: "var(--color-btn-primary-text)",
              }}
            >
              <path
                d="M3.5 6.5L5 8L8.5 4.5"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </div>
      </div>
      {label && (
        <span
          className={
            disabled ? "text-[var(--muted)] opacity-60" : "text-[var(--text)]"
          }
        >
          {label}
        </span>
      )}
    </label>
  );
};

export default Checkbox;
