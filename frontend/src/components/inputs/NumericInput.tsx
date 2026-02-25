"use client";

import React, { useEffect, useState } from "react";
import { formatNumberWithSpaces } from "../../utils/numberFormatter";

interface NumericInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  value?: string | number;
  onValueChange?: (value: string) => void;
  onNumberChange?: (value: number | null) => void;
  min?: number;
  max?: number;
  placeholder?: string;
  unit?: string;
  hasError?: boolean;
  onLimitExceeded?: (formattedLimit: string) => void;
  allowDecimal?: boolean;
  maxDecimals?: number;
}

function NumericInput({
  id,
  name,
  value,
  onValueChange,
  onNumberChange,
  min,
  max,
  placeholder,
  unit,
  className = "",
  inputMode = "numeric",
  hasError = false,
  onLimitExceeded,
  allowDecimal = false,
  maxDecimals = 0,
  ...rest
}: NumericInputProps) {
  const [internalValue, setInternalValue] = useState(value?.toString() || "");

  useEffect(() => {
    setInternalValue(value?.toString() || "");
  }, [value]);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const rawValue = event.target.value;

    if (!allowDecimal) {
      const cleaned = rawValue.replace(/[^\d]/g, "");

      if (cleaned === "") {
        setInternalValue("");
        if (onValueChange) {
          onValueChange("");
        }
        if (onNumberChange) {
          onNumberChange(null);
        }
        return;
      }

      let numericValue = parseInt(cleaned, 10);

      if (
        typeof min === "number" &&
        !Number.isNaN(numericValue) &&
        numericValue < min
      ) {
        numericValue = min;
      }

      let clampedByMax = false;
      if (
        typeof max === "number" &&
        !Number.isNaN(numericValue) &&
        numericValue > max
      ) {
        numericValue = max;
        clampedByMax = true;
      }

      const formatted = formatNumberWithSpaces(numericValue);

      setInternalValue(formatted);

      if (onValueChange) {
        onValueChange(formatted);
      }

      if (onNumberChange) {
        onNumberChange(numericValue);
      }

      if (clampedByMax && onLimitExceeded) {
        const formattedLimit = unit ? `${formatted} ${unit}` : formatted;
        onLimitExceeded(formattedLimit);
      }

      return;
    }

    const withoutSpaces = rawValue.replace(/\s/g, "");
    const hadTrailingSeparator = /[.,]$/.test(withoutSpaces);
    let cleaned = withoutSpaces.replace(/[^\d.,]/g, "");
    cleaned = cleaned.replace(",", ".");

    if (cleaned === "") {
      setInternalValue("");
      if (onValueChange) {
        onValueChange("");
      }
      if (onNumberChange) {
        onNumberChange(null);
      }
      return;
    }

    const parts = cleaned.split(".");
    let integerPart = parts[0] || "";
    const decimalPartRaw = parts.length > 1 ? parts.slice(1).join("") : "";
    let decimalPart =
      maxDecimals > 0 && decimalPartRaw.length > 0
        ? decimalPartRaw.slice(0, maxDecimals)
        : decimalPartRaw;

    let numericValue = parseFloat(
      decimalPart !== ""
        ? `${integerPart || "0"}.${decimalPart}`
        : integerPart || "0",
    );

    if (!Number.isFinite(numericValue)) {
      numericValue = 0;
    }

    if (typeof min === "number" && numericValue < min) {
      numericValue = min;
    }

    let clampedByMax = false;
    let maxString = null;

    if (typeof max === "number" && numericValue > max) {
      numericValue = max;
      clampedByMax = true;
      maxString = maxDecimals > 0 ? max.toFixed(maxDecimals) : max.toString();
      const maxParts = maxString.split(".");
      integerPart = maxParts[0] || "";
      decimalPart = maxParts.length > 1 ? maxParts[1] : "";
    }

    const formattedInteger = integerPart
      ? formatNumberWithSpaces(parseInt(integerPart, 10))
      : "0";
    let formatted = formattedInteger;

    if (maxDecimals > 0) {
      if (decimalPart !== "") {
        formatted = `${formattedInteger}.${decimalPart}`;
      } else if (hadTrailingSeparator) {
        // L'utilisateur vient de taper un séparateur décimal: on garde le point
        formatted = `${formattedInteger}.`;
      }
    }

    setInternalValue(formatted);

    if (onValueChange) {
      onValueChange(formatted);
    }

    if (onNumberChange) {
      onNumberChange(numericValue);
    }

    if (clampedByMax && onLimitExceeded) {
      const limitString =
        maxString ||
        (maxDecimals > 0
          ? numericValue.toFixed(maxDecimals)
          : numericValue.toString());
      const formattedLimit = unit ? `${limitString} ${unit}` : limitString;
      onLimitExceeded(formattedLimit);
    }
  };

  const baseClasses =
    "w-full rounded-lg bg-[var(--color-surface-input)] px-4 py-2.5 text-base text-[var(--text)] focus:outline-none border transition-colors";

  const borderClasses = hasError
    ? "border-2 border-[rgb(var(--danger))] focus:border-[rgb(var(--danger))] focus:ring-0"
    : "border border-[var(--border)] focus:border-[rgba(var(--primary),0.5)] focus:ring-2 focus:ring-[rgba(var(--primary),0.1)]";

  const paddingClasses = unit ? "pr-10" : "";

  return (
    <div className="relative">
      <input
        id={id}
        name={name}
        type="text"
        inputMode={inputMode}
        value={internalValue}
        onChange={handleChange}
        placeholder={placeholder}
        className={`${baseClasses} ${borderClasses} ${paddingClasses} ${className}`}
        {...rest}
      />
      {unit && (
        <span className="pointer-events-none absolute inset-y-0 right-2 text-sm flex items-center text-[var(--muted)]">
          {unit}
        </span>
      )}
    </div>
  );
}

export default NumericInput;
