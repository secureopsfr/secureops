/**
 * Point d'entrée unifié pour tous les services d'administration.
 * Les sous-services sont des modules avec des fonctions exportées :
 * un simple spread suffit pour les agréger.
 */

import * as adminUsers from "./adminUsersService";
import * as adminSubscriptions from "./adminSubscriptionsService";
import * as adminContact from "./adminContactService";
import * as adminMedia from "./adminMediaService";
import * as adminAnalytics from "./adminAnalyticsService";
import * as adminMetrics from "./adminMetricsService";
import * as adminEmails from "./adminEmailsService";
import * as adminAudit from "./adminAuditService";
import * as adminAlerts from "./adminAlertsService";

// Réexporter tous les types depuis le dossier centralisé
export * from "../../types";

/**
 * Service d'administration unifié.
 * Pour ajouter un nouveau sous-service : 1 import + 1 spread.
 */
const adminService = {
  ...adminUsers,
  ...adminSubscriptions,
  ...adminContact,
  ...adminMedia,
  ...adminAnalytics,
  ...adminMetrics,
  ...adminEmails,
  ...adminAudit,
  ...adminAlerts,
};

export default adminService;
