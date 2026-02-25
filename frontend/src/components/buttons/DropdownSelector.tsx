"use client";

import React, {
  useRef,
  useEffect,
  useState,
  useCallback,
  useMemo,
} from "react";
import { createPortal } from "react-dom";
import { ChevronDown } from "lucide-react";
import { useDropdown } from "../../hooks/useDropdown";

interface Option {
  value: string;
  label: string;
  disabled?: boolean;
}

interface DropdownSelectorProps {
  selectedValue: string;
  onChange: (value: string) => void;
  options: Option[];
  /** Largeur CSS (ex: '13rem', '200px'). Par défaut '12rem'. */
  width?: string;
  className?: string;
  /** Classe appliquée au bouton trigger (ex: 'h-9' pour aligner la hauteur). */
  triggerClassName?: string;
}

/**
 * Composant générique pour les sélecteurs dropdown réutilisables.
 * Le menu s'affiche dans un portail (body) pour ne jamais être coupé par un parent.
 */
const DropdownSelector: React.FC<DropdownSelectorProps> = ({
  selectedValue,
  onChange,
  options = [],
  width = "12rem",
  className = "",
  triggerClassName = "",
}) => {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Memoize excludeRefs so it's stable across renders
  const excludeRefs = useMemo(() => [menuRef], []);

  const {
    isOpen,
    isClosing,
    dropdownRef,
    mouseHandlers,
    buttonHandlers,
    close,
  } = useDropdown({
    closeDelay: 200,
    excludeRefs,
  });

  const [menuPos, setMenuPos] = useState<{
    top: number;
    left: number;
    width: number;
  }>({
    top: 0,
    left: 0,
    width: 0,
  });

  // Track whether the menu has been rendered for at least one frame (for enter animation)
  const [isAnimatedIn, setIsAnimatedIn] = useState(false);

  useEffect(() => {
    if (isOpen && !isClosing) {
      // Wait one frame so the DOM mounts with the "closed" style, then animate to "open"
      const raf = requestAnimationFrame(() => {
        setIsAnimatedIn(true);
      });
      return () => cancelAnimationFrame(raf);
    } else {
      setIsAnimatedIn(false);
    }
  }, [isOpen, isClosing]);

  const selectedOption = options.find((opt) => opt.value === selectedValue);
  const displayLabel = selectedOption ? selectedOption.label : "—";

  const updatePosition = useCallback(() => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setMenuPos({
        top: rect.bottom,
        left: rect.left,
        width: rect.width,
      });
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      updatePosition();
      window.addEventListener("scroll", updatePosition, true);
      window.addEventListener("resize", updatePosition);
      return () => {
        window.removeEventListener("scroll", updatePosition, true);
        window.removeEventListener("resize", updatePosition);
      };
    }
  }, [isOpen, updatePosition]);

  const visible = isOpen || isClosing;

  const menu =
    visible &&
    typeof document !== "undefined" &&
    createPortal(
      <div
        ref={menuRef}
        onMouseEnter={mouseHandlers.onMouseEnter}
        onMouseLeave={mouseHandlers.onMouseLeave}
        style={{
          position: "fixed",
          top: menuPos.top,
          left: menuPos.left,
          width: menuPos.width,
          zIndex: 99999,
          // Invisible bridge between button and menu to prevent hover gap
          paddingTop: 4,
        }}
      >
        <ul
          style={{
            background: "var(--color-dropdown-bg)",
            border: "1px solid var(--border)",
            borderRadius: "0.5rem",
            overflow: "hidden",
            listStyle: "none",
            padding: 0,
            margin: 0,
            fontSize: "0.875rem",
            boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
            // Animation: start collapsed, animate in, animate out on close
            opacity: isClosing ? 0 : isAnimatedIn ? 1 : 0,
            transform: isClosing
              ? "translateY(-6px) scale(0.97)"
              : isAnimatedIn
                ? "translateY(0) scale(1)"
                : "translateY(-6px) scale(0.97)",
            transformOrigin: "top center",
            transition: "opacity 0.2s ease, transform 0.2s ease",
          }}
        >
          {options.map((opt) => (
            <li key={opt.value} style={{ listStyle: "none" }}>
              <button
                type="button"
                disabled={opt.disabled}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  padding: "0.5rem 0.75rem",
                  fontSize: "0.875rem",
                  cursor: opt.disabled ? "not-allowed" : "pointer",
                  transition: "background 0.15s, color 0.15s",
                  background:
                    opt.value === selectedValue
                      ? "rgba(var(--primary), 0.15)"
                      : "transparent",
                  color: opt.disabled
                    ? "var(--muted)"
                    : opt.value === selectedValue
                      ? "rgb(var(--primary))"
                      : "var(--text)",
                  fontWeight: opt.value === selectedValue ? 600 : 400,
                  opacity: opt.disabled ? 0.5 : 1,
                  border: "none",
                }}
                onMouseEnter={(e) => {
                  if (!opt.disabled && opt.value !== selectedValue) {
                    (e.currentTarget as HTMLButtonElement).style.background =
                      "var(--color-surface-input)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!opt.disabled) {
                    (e.currentTarget as HTMLButtonElement).style.background =
                      opt.value === selectedValue
                        ? "rgba(var(--primary), 0.15)"
                        : "transparent";
                  }
                }}
                onClick={() => {
                  if (!opt.disabled) {
                    onChange(opt.value);
                    close();
                  }
                }}
              >
                {opt.label}
              </button>
            </li>
          ))}
        </ul>
      </div>,
      document.body,
    );

  return (
    <div
      ref={dropdownRef}
      className={`relative ${width === "100%" ? "block" : "inline-block"} text-left ${className}`}
      {...mouseHandlers}
    >
      <button
        ref={buttonRef}
        type="button"
        className={triggerClassName}
        style={{
          width,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "var(--color-surface-input)",
          border: "1px solid var(--border)",
          color: "var(--text)",
          borderRadius: "0.5rem",
          padding: "0.5rem 0.75rem",
          fontSize: "0.875rem",
          cursor: "pointer",
          transition: "background 0.15s, border-color 0.15s",
          outline: "none",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "var(--color-surface-input-hover)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = "var(--color-surface-input)";
        }}
        {...buttonHandlers}
      >
        <span
          style={{
            flex: 1,
            textAlign: "left",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            color: "var(--text)",
          }}
        >
          {displayLabel}
        </span>
        <ChevronDown
          style={{
            width: 16,
            height: 16,
            marginLeft: "0.5rem",
            flexShrink: 0,
            color: "var(--muted)",
            transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.25s ease",
          }}
        />
      </button>

      {menu}
    </div>
  );
};

export default DropdownSelector;
