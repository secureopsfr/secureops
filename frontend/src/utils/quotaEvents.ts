/**
 * Permet de rafraîchir le compteur quota (useQuota) après qu'un job scan/crawl
 * ait été accepté par l'API (quota déjà incrémenté côté gateway).
 */
export const DAILY_QUOTA_CHANGED_EVENT = "immosphere:daily-quota-changed";

export function notifyDailyQuotaChanged(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(DAILY_QUOTA_CHANGED_EVENT));
  }
}
