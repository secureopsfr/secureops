/**
 * Calcul des KPI agrégées à partir des métriques de performance API.
 * Utilisé par la page admin et la vue d'ensemble.
 */

export interface ApiKpis {
  totalRequests: number;
  avgMs: number | null;
  successRate: number | null;
  totalErrors: number;
  maxP95: number | null;
  activeRoutes: number;
}

/**
 * Calcule les KPI agrégées à partir d'un tableau de métriques de performance.
 * @param metrics - Tableau de métriques brutes provenant de l'API
 * @returns Les KPI agrégées ou null si pas de données
 */
export function computeApiKpis(
  metrics: Record<string, unknown>[],
): ApiKpis | null {
  if (!metrics || metrics.length === 0) return null;

  const totalRequests = metrics.reduce(
    (sum, m) => sum + ((m.requestCount as number) ?? (m.count as number) ?? 0),
    0,
  );

  // Moyenne pondérée du temps de réponse
  let avgMs: number | null = null;
  if (totalRequests > 0) {
    const totalMs = metrics.reduce((sum, m) => {
      const count = (m.requestCount as number) ?? (m.count as number) ?? 0;
      const avg = (m.avgMs as number) ?? (m.avgDurationMs as number) ?? 0;
      return sum + count * avg;
    }, 0);
    avgMs = totalMs / totalRequests;
  }

  // Taux de succès pondéré
  let successRate: number | null = null;
  if (totalRequests > 0) {
    const totalSuccess = metrics.reduce((sum, m) => {
      const count = (m.requestCount as number) ?? (m.count as number) ?? 0;
      const rate = (m.successRate as number) ?? 0;
      return sum + count * rate;
    }, 0);
    successRate = totalSuccess / totalRequests;
  }

  // Total erreurs
  const totalErrors = metrics.reduce((sum, m) => {
    const count = (m.requestCount as number) ?? (m.count as number) ?? 0;
    const clientErr = (m.clientErrorRate as number) ?? 0;
    const serverErr = (m.serverErrorRate as number) ?? 0;
    return sum + Math.round(count * (clientErr + serverErr));
  }, 0);

  // P95 max
  const p95Values = metrics
    .map((m) => (m.p95Ms as number) ?? null)
    .filter((v): v is number => v !== null);
  const maxP95 = p95Values.length > 0 ? Math.max(...p95Values) : null;

  return {
    totalRequests,
    avgMs,
    successRate,
    totalErrors,
    maxP95,
    activeRoutes: metrics.length,
  };
}
