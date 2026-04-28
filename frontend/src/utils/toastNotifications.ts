import { toast } from "react-hot-toast";

/** Traducteur utilisé pour les messages de repli des toasts (langue courante). */
let toastTranslator: ((key: string) => string) | null = null;

export function setToastTranslator(fn: (key: string) => string): void {
  toastTranslator = fn;
}

export function getToastT(): (key: string) => string {
  return toastTranslator ?? ((k) => k);
}

interface ToastExtraOptions {
  duration?: number;
  position?:
    | "top-left"
    | "top-center"
    | "top-right"
    | "bottom-left"
    | "bottom-center"
    | "bottom-right";
  id?: string;
  className?: string;
}

const BASE_OPTIONS = {
  duration: 4500,
  position: "bottom-right" as const,
};

const withToastClass = (variantClass: string, className?: string) =>
  ["secureops-toast", variantClass, className].filter(Boolean).join(" ");

export const showSuccessToast = (
  message: string,
  options: ToastExtraOptions = {},
) =>
  toast.success(message || getToastT()("admin.common.successDefault"), {
    ...BASE_OPTIONS,
    ...options,
    className: withToastClass("secureops-toast--success", options.className),
  });

export const showErrorToast = (
  message: string,
  options: ToastExtraOptions = {},
) =>
  toast.error(message || getToastT()("admin.common.errorDefault"), {
    ...BASE_OPTIONS,
    duration: options.duration ?? 5500,
    ...options,
    className: withToastClass("secureops-toast--error", options.className),
  });

export const showWarningToast = (
  message: string,
  options: ToastExtraOptions = {},
) =>
  toast(message || getToastT()("admin.common.infoDefault"), {
    ...BASE_OPTIONS,
    ...options,
    className: withToastClass("secureops-toast--warning", options.className),
    icon: "!",
  });
