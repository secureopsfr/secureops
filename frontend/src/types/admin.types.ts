/**
 * Types centralisés pour les services d'administration.
 * Centralise toutes les interfaces et types liés à l'admin pour éviter la duplication.
 */

// ========== Utilisateurs ==========

export interface UserRecord {
  id: string;
  cognito_sub: string;
  email: string;
  created_at: string | null;
  subscription_id: string | null;
  plan: string;
  status: string;
  stripe_customer_id: string | null;
  newsletter_enabled: boolean;
  notifications_enabled: boolean;
  current_period_end: string | null;
  updated_at: string | null;
  cognito_groups?: string[];
  cognito_status?: string | null;
  cognito_enabled?: boolean;
  [key: string]: unknown;
}

export interface UsersResponse {
  users: UserRecord[];
  total: number;
}

export interface UsersStatsResponse {
  total_users: number;
  recent_users_7d: number;
  plans: Record<string, number>;
  statuses: Record<string, number>;
  newsletter_subscribers: number;
  notification_subscribers: number;
}

// ========== Abonnements ==========

export interface SubscriptionRecord {
  id: string;
  user_id: string;
  email: string | null;
  plan: string;
  status: string;
  stripe_customer_id: string | null;
  current_period_end: string | null;
  newsletter_enabled: boolean;
  notifications_enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
  [key: string]: unknown;
}

export interface SubscriptionStatsResponse {
  total_subscriptions: number;
  plans: Record<string, number>;
  statuses: Record<string, number>;
  premium_count: number;
  stripe_count: number;
  recent_subscriptions_7d: number;
  expiring_soon_30d: number;
  conversion_rate: number;
  churn_rate: number;
  monthly_history: Array<{ month: string; free: number; premium: number }>;
}

// ========== Messages de contact ==========

export interface ContactMessageRecord {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  subject: string;
  message: string;
  status: string;
  created_at: string;
  updated_at: string;
  [key: string]: unknown;
}

// ========== Emails & Newsletter ==========

export interface EmailRecord {
  id: number;
  subject: string;
  content: string;
  status?: string;
  created_at?: string;
  sent_at?: string;
  scheduled_at?: string;
  [key: string]: unknown;
}

export interface SubscriberRecord {
  email: string;
  subscribed_at?: string;
  [key: string]: unknown;
}

// ========== Médias ==========

export interface ImageRecord {
  filename: string;
  url: string;
  thumbnail_url?: string;
  size: number;
  created_at: string;
}

export interface ImageGalleryResponse {
  images: ImageRecord[];
  total: number;
}

export interface ImageGalleryStats {
  total: number;
  total_size: number;
  by_extension: Record<string, number>;
}

// ========== Templates d'emails ==========

export interface TemplateRecord {
  filename: string;
  size: number;
  updated_at: string;
}

export interface TemplateListResponse {
  templates: TemplateRecord[];
  total: number;
}

export interface TemplateContent {
  filename: string;
  content: string;
  size: number;
  updated_at: string;
}

// ========== Analytics ==========

export interface TimeSeriesPoint {
  timestamp: string;
  count: number;
  avgMs: number | null;
}

export interface PageViewSummary {
  page: string;
  views: number;
  uniqueVisitors: number;
  avgDurationMs: number | null;
  bounceCount: number;
}

export interface PageViewsSummaryResponse {
  pages: PageViewSummary[];
  totalViews: number;
  totalUniqueVisitors: number;
  avgPagesPerSession: number | null;
  avgSessionDurationMs: number | null;
  bounceRate: number | null;
}

export interface ReferrerSummary {
  referrer: string;
  count: number;
  uniqueVisitors: number;
}

export interface TrafficTimeSeriesPoint {
  timestamp: string;
  views: number;
  uniqueVisitors: number;
}

export interface DeviceBreakdown {
  deviceType: string;
  count: number;
  percentage: number;
}

export interface GeoCountryBreakdown {
  country: string;
  count: number;
  percentage: number;
}

export interface GeoBreakdownResponse {
  countries: GeoCountryBreakdown[];
}

// ========== Audit Logs ==========

export interface AuditLogEntry {
  id: string;
  admin_email: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string | null;
  [key: string]: unknown;
}

export interface AuditStatsResponse {
  total_actions: number;
  by_action: Record<string, number>;
  by_entity: Record<string, number>;
  top_admins: Array<{ email: string; count: number }>;
}

// ========== Alerting ==========

export interface AlertRuleRecord {
  id: string;
  name: string;
  metric: string;
  condition: string;
  threshold: number;
  window_minutes: number;
  service_filter: string | null;
  notify_email: boolean;
  enabled: boolean;
  cooldown_minutes: number;
  created_at: string | null;
  updated_at: string | null;
  [key: string]: unknown;
}

export interface AlertEventRecord {
  id: string;
  rule_id: string | null;
  rule_name: string;
  metric: string;
  current_value: number;
  threshold: number;
  severity: string;
  message: string;
  acknowledged: boolean;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  created_at: string | null;
  [key: string]: unknown;
}

export interface AlertSummaryResponse {
  unacknowledged: number;
  recent_24h: number;
  critical: number;
  active_rules: number;
}

// ========== API Responses génériques ==========

export interface ApiResponse<T = unknown> {
  success: boolean;
  error?: string;
  message?: string;
  data?: T;
  metrics?: T[];
  total?: number;
  [key: string]: unknown;
}
