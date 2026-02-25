import { useState, useRef, useEffect, useCallback, useMemo } from "react";

interface UseDropdownOptions {
  closeDelay?: number;
  isOpen?: boolean;
  setIsOpen?: (isOpen: boolean) => void;
  /** Additional refs to exclude from click-outside detection (e.g. portal menus). */
  excludeRefs?: React.RefObject<HTMLElement | null>[];
}

interface UseDropdownReturn {
  isOpen: boolean;
  isClosing: boolean;
  canHover: boolean;
  dropdownRef: React.RefObject<HTMLDivElement | null>;
  open: () => void;
  close: () => void;
  toggle: () => void;
  mouseHandlers: {
    onMouseEnter?: () => void;
    onMouseLeave?: () => void;
  };
  buttonHandlers: {
    onMouseDown: (e: React.MouseEvent) => void;
    onClick: () => void;
  };
}

/**
 * Hook personnalisé pour gérer la logique de dropdown avec support hover et click outside.
 *
 * @param options - Options de configuration
 * @param options.closeDelay - Délai en ms avant la fermeture (durée de l'animation)
 * @param options.isOpen - État externe d'ouverture (optionnel, pour utiliser avec un contexte)
 * @param options.setIsOpen - Fonction externe pour définir l'état d'ouverture (optionnel)
 * @param options.excludeRefs - Refs additionnels exclus du click-outside (ex: portail)
 * @returns Objet contenant les états, refs et handlers pour le dropdown
 */
export function useDropdown({
  closeDelay = 300,
  isOpen: externalIsOpen,
  setIsOpen: externalSetIsOpen,
  excludeRefs = [],
}: UseDropdownOptions = {}): UseDropdownReturn {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [canHover, setCanHover] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const closeTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const openTimestampRef = useRef<number>(0);

  // Grace period (ms) after opening before allowing hover-close
  const OPEN_GRACE_PERIOD = 150;

  // Utiliser l'état externe si fourni, sinon utiliser l'état interne
  const isOpen = externalIsOpen !== undefined ? externalIsOpen : internalIsOpen;
  const setIsOpen = externalSetIsOpen || setInternalIsOpen;

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (closeTimeoutRef.current) {
        clearTimeout(closeTimeoutRef.current);
      }
    };
  }, []);

  // Fonction pour gérer la fermeture avec animation
  const handleClose = useCallback(() => {
    // Don't start a new close if already closing
    if (closeTimeoutRef.current) return;
    // Don't close if we just opened (grace period for mouse to reach portal menu)
    if (Date.now() - openTimestampRef.current < OPEN_GRACE_PERIOD) return;
    setIsClosing(true);
    closeTimeoutRef.current = setTimeout(() => {
      setIsOpen(false);
      setIsClosing(false);
      closeTimeoutRef.current = null;
    }, closeDelay);
  }, [closeDelay, setIsOpen]);

  // Fonction pour ouvrir le dropdown
  const handleOpen = useCallback(() => {
    // Cancel any pending close
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
    setIsOpen(true);
    setIsClosing(false);
    openTimestampRef.current = Date.now();
  }, [setIsOpen]);

  // Fonction pour basculer l'état ouvert/fermé
  const handleToggle = useCallback(() => {
    if (isOpen && !isClosing) {
      handleClose();
    } else {
      handleOpen();
    }
  }, [isOpen, isClosing, handleOpen, handleClose]);

  // Fermer le dropdown quand on clique à l'extérieur
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (!isOpen || isClosing) return;

      const target = event.target as Node;

      // Check if click is inside the main dropdown ref
      if (dropdownRef.current?.contains(target)) return;

      // Check if click is inside any excluded ref (e.g. portal menu)
      for (const ref of excludeRefs) {
        if (ref.current?.contains(target)) return;
      }

      handleClose();
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, isClosing, handleClose, excludeRefs]);

  // Détecter si l'appareil supporte le hover
  useEffect(() => {
    if (
      typeof window === "undefined" ||
      typeof window.matchMedia !== "function"
    ) {
      setCanHover(false);
      return undefined;
    }

    const mediaQuery = window.matchMedia("(hover: hover)");
    const updateCapability = (event: MediaQueryListEvent) => {
      setCanHover(event.matches);
    };

    setCanHover(mediaQuery.matches);
    mediaQuery.addEventListener("change", updateCapability);
    return () => mediaQuery.removeEventListener("change", updateCapability);
  }, []);

  // Handlers pour les événements de souris sur le conteneur
  const mouseHandlers = useMemo(
    () => ({
      onMouseEnter: canHover ? handleOpen : undefined,
      onMouseLeave: canHover ? handleClose : undefined,
    }),
    [canHover, handleOpen, handleClose],
  );

  // Handlers pour le bouton
  const buttonHandlers = useMemo(
    () => ({
      onMouseDown: (e: React.MouseEvent) => {
        // Empêcher le focus au clic
        e.preventDefault();
      },
      onClick: () => {
        if (!canHover) {
          handleToggle();
        }
      },
    }),
    [canHover, handleToggle],
  );

  return {
    isOpen,
    isClosing,
    canHover,
    dropdownRef,
    open: handleOpen,
    close: handleClose,
    toggle: handleToggle,
    mouseHandlers,
    buttonHandlers,
  };
}
