"use client";

import React from "react";

interface ToggleSwitchProps {
  checked: boolean;
  onChange: () => void;
  disabled?: boolean;
  label?: string;
}

const ToggleSwitch: React.FC<ToggleSwitchProps> = ({
  checked,
  onChange,
  disabled = false,
  label,
}) => (
  <label
    className={`relative inline-flex items-center flex-shrink-0 ${disabled ? "cursor-not-allowed" : "cursor-pointer"}`}
    aria-label={label}
  >
    <input
      type="checkbox"
      checked={checked}
      onChange={onChange}
      disabled={disabled}
      className="sr-only peer"
    />
    <div
      className={`w-11 h-6 rounded-full transition-colors duration-200
        peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[rgba(var(--primary),0.2)]
        after:content-[''] after:absolute after:top-[2px] after:left-[2px]
        after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all after:duration-200
        peer-checked:after:translate-x-full
        ${checked ? "bg-[rgb(var(--primary))]" : "bg-[var(--color-checkbox-border)]"}
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
    />
  </label>
);

export default ToggleSwitch;
