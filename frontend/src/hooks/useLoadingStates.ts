import { useState, useCallback } from "react";

/**
 * Hook personnalisé pour gérer plusieurs états de chargement de manière centralisée.
 * Permet d'éviter la prolifération de useState individuels pour chaque état de chargement.
 *
 * @param initialKeys - Les clés des états de chargement à initialiser
 * @returns Un objet contenant l'état de chargement et une fonction pour le mettre à jour
 *
 * @example
 * const { loading, setLoadingState } = useLoadingStates(['main', 'stats', 'detail']);
 *
 * setLoadingState('main', true);
 * // loading.main === true
 *
 * if (loading.stats) { ... }
 */
export function useLoadingStates(initialKeys: string[]) {
  const [loading, setLoading] = useState<Record<string, boolean>>(
    Object.fromEntries(initialKeys.map((key) => [key, false])),
  );

  const setLoadingState = useCallback((key: string, value: boolean) => {
    setLoading((prev) => ({ ...prev, [key]: value }));
  }, []);

  const resetAllLoading = useCallback(() => {
    setLoading((prev) =>
      Object.fromEntries(Object.keys(prev).map((key) => [key, false])),
    );
  }, []);

  return { loading, setLoadingState, resetAllLoading };
}
