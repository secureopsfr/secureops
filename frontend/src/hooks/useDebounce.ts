import { useEffect, useState, useRef, useCallback } from "react";

/**
 * Hook pour débouncer une valeur.
 * Retarde la mise à jour de la valeur jusqu'à ce qu'un certain délai se soit écoulé sans changement.
 *
 * @param value - La valeur à débouncer
 * @param delay - Le délai en millisecondes
 * @returns La valeur débouncée
 *
 * @example
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearchTerm = useDebounce(searchTerm, 500);
 *
 * useEffect(() => {
 *   // Cet effet ne s'exécutera que 500ms après le dernier changement
 *   if (debouncedSearchTerm) {
 *     performSearch(debouncedSearchTerm);
 *   }
 * }, [debouncedSearchTerm]);
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Hook pour débouncer une fonction callback.
 * Retarde l'exécution de la fonction jusqu'à ce qu'un certain délai se soit écoulé sans nouvel appel.
 *
 * @param callback - La fonction à débouncer
 * @param delay - Le délai en millisecondes
 * @returns La fonction débouncée
 *
 * @example
 * const debouncedSearch = useDebouncedCallback((term: string) => {
 *   performSearch(term);
 * }, 500);
 *
 * <input onChange={(e) => debouncedSearch(e.target.value)} />
 */
export function useDebouncedCallback<T extends (...args: unknown[]) => unknown>(
  callback: T,
  delay: number,
): (...args: Parameters<T>) => void {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const debouncedCallback = useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        callback(...args);
      }, delay);
    },
    [callback, delay],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return debouncedCallback;
}
