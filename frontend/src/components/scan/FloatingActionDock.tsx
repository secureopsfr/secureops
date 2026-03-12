"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import type { ReactNode } from "react";
import { GenericButton } from "../buttons";

const BOTTOM_DEFAULT = 20;
const BOTTOM_ABOVE_FOOTER = 220;

interface FloatingActionDockAction {
  key: string;
  label: string;
  variant: "primary" | "secondary" | "outline" | "danger";
  onClick: () => void;
  icon?: ReactNode;
  iconPosition?: "left" | "right";
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
}

interface FloatingActionDockProps {
  actions: FloatingActionDockAction[];
  ariaLabel: string;
}

export default function FloatingActionDock({
  actions,
  ariaLabel,
}: FloatingActionDockProps) {
  const [bottom, setBottom] = useState(BOTTOM_DEFAULT);

  useEffect(() => {
    const footer = document.getElementById("site-footer");
    if (!footer) return;

    const updateBottom = (): void => {
      const rect = footer.getBoundingClientRect();
      const footerVisible = rect.top < window.innerHeight;
      setBottom(footerVisible ? BOTTOM_ABOVE_FOOTER : BOTTOM_DEFAULT);
    };

    const observer = new IntersectionObserver(updateBottom, {
      threshold: 0,
      rootMargin: "0px",
    });
    observer.observe(footer);

    const throttledUpdate = (): void => {
      requestAnimationFrame(updateBottom);
    };
    window.addEventListener("scroll", throttledUpdate, { passive: true });
    window.addEventListener("resize", throttledUpdate);
    updateBottom();

    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", throttledUpdate);
      window.removeEventListener("resize", throttledUpdate);
    };
  }, []);

  if (typeof document === "undefined" || actions.length === 0) {
    return null;
  }

  return createPortal(
    <div
      className="fixed right-6 z-[9998] flex items-center gap-2 shadow-lg transition-all duration-200"
      style={{ position: "fixed", bottom }}
      aria-label={ariaLabel}
    >
      {actions.map((action) => (
        <GenericButton
          key={action.key}
          type={action.type ?? "button"}
          label={action.label}
          variant={action.variant}
          onClick={action.onClick}
          icon={action.icon}
          iconPosition={action.iconPosition}
          disabled={action.disabled}
        />
      ))}
    </div>,
    document.body,
  );
}
