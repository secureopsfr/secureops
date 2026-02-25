/**
 * Types centralisés pour les utilisateurs et profils.
 */

export interface SubscriptionData {
  plan?: string;
  status?: string;
  newsletter_enabled?: boolean;
  new_features_notifications_enabled?: boolean;
  [key: string]: unknown;
}

export interface UserProfile {
  givenName: string;
  familyName: string;
  email: string;
  phoneNumber: string;
}

export interface ApiResult<T = unknown> {
  success: boolean;
  message?: string;
  error?: string;
  data?: T;
  [key: string]: unknown;
}
