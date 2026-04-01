/**
 * Vérification DNS (TXT) des domaines pour les scans non passifs.
 */

import {
  fetchWithAuth,
  fetchJsonWithAuth,
  getApiBaseUrl,
  handleFetchError,
} from "../utils/apiClient";

export interface DomainVerificationChallengeResponse {
  domain: string;
  txt_name: string;
  txt_value: string;
  challenge_expires_at: string;
  already_verified: boolean;
}

export interface DomainVerificationItem {
  id: string;
  domain: string;
  verified_at: string;
  expires_at: string;
}

const base = () => `${getApiBaseUrl()}/user/api/user/domain-verifications`;

export function createDomainChallenge(
  url: string,
): Promise<DomainVerificationChallengeResponse> {
  return fetchJsonWithAuth<DomainVerificationChallengeResponse>(
    `${base()}/challenges`,
    {
      method: "POST",
      body: JSON.stringify({ url }),
    },
    "Impossible de créer le challenge DNS",
  );
}

export async function verifyDomain(domain: string): Promise<void> {
  const res = await fetchWithAuth(`${base()}/verify`, {
    method: "POST",
    body: JSON.stringify({ domain }),
  });
  if (!res.ok) {
    await handleFetchError(res, "Vérification DNS échouée");
  }
}

export function listDomainVerifications(): Promise<DomainVerificationItem[]> {
  return fetchJsonWithAuth<DomainVerificationItem[]>(
    `${base()}`,
    { method: "GET" },
    "Impossible de lister les domaines vérifiés",
  );
}

export async function deleteDomainVerification(id: string): Promise<void> {
  const res = await fetchWithAuth(`${base()}/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    await handleFetchError(res, "Impossible de supprimer la vérification");
  }
}
