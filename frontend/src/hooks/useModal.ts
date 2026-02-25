/**
 * Hook personnalisé pour gérer l'état d'une modal.
 * Simplifie l'ouverture/fermeture et la gestion des données de modal.
 */

import { useState, useCallback } from "react";

interface UseModalReturn<T> {
  isOpen: boolean;
  data: T | null;
  open: (modalData?: T) => void;
  close: () => void;
  setData: (data: T | null) => void;
}

export function useModal<T = unknown>(): UseModalReturn<T> {
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState<T | null>(null);

  const open = useCallback((modalData?: T) => {
    if (modalData !== undefined) {
      setData(modalData);
    }
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    // Délai pour laisser l'animation de fermeture se terminer
    setTimeout(() => setData(null), 200);
  }, []);

  const updateData = useCallback((newData: T | null) => {
    setData(newData);
  }, []);

  return {
    isOpen,
    data,
    open,
    close,
    setData: updateData,
  };
}
