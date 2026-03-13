"use client";

import type { ScanHistorySelection } from "../../services/scanHistoryService";
import ScanHistoryBlock from "./ScanHistoryBlock";
import AlertHistoryBlock from "./AlertHistoryBlock";
import ScheduledScansBlock from "./ScheduledScansBlock";

interface ScannerHistoryAlertsSectionProps {
  /** Callback quand l'utilisateur sélectionne un scan dans l'historique. */
  onSelectScan: (selection: ScanHistorySelection) => void;
  /** Filtre optionnel par URL (historique/alertes/suivis limités à cette URL). */
  filterUrl?: string | null;
  /** Filtre optionnel par type de scan (frontend, backend, both). */
  filterScanType?: string | null;
  /** Filtre optionnel par mode de scan (passive, intrusive, destructive, custom). */
  filterScanMode?: string | null;
  /** Filtre optionnel date de début (historique des scans et alertes uniquement). */
  filterDateFrom?: string | null;
  /** Filtre optionnel date de fin (historique des scans et alertes uniquement). */
  filterDateTo?: string | null;
  /** Déclencheur de rafraîchissement pour ScheduledScansBlock (ex. après création). */
  scheduleRefreshTrigger?: number;
  /** Classes supplémentaires pour le conteneur. */
  className?: string;
}

export default function ScannerHistoryAlertsSection({
  onSelectScan,
  filterUrl,
  filterScanType,
  filterScanMode,
  filterDateFrom,
  filterDateTo,
  scheduleRefreshTrigger = 0,
  className = "",
}: ScannerHistoryAlertsSectionProps) {
  return (
    <div
      className={`[&>section+section]:-mt-3 flex flex-col gap-6 ${className}`.trim()}
    >
      <ScheduledScansBlock
        filterUrl={filterUrl}
        filterScanType={filterScanType}
        filterScanMode={filterScanMode}
        refreshTrigger={scheduleRefreshTrigger}
      />
      <div className="flex flex-col lg:flex-row gap-6">
        <div className="flex-1 min-w-0">
          <ScanHistoryBlock
            onSelectScan={onSelectScan}
            filterUrl={filterUrl}
            filterScanType={filterScanType}
            filterScanMode={filterScanMode}
            filterDateFrom={filterDateFrom}
            filterDateTo={filterDateTo}
          />
        </div>
        <div className="flex-1 min-w-0">
          <AlertHistoryBlock
            filterUrl={filterUrl}
            filterScanType={filterScanType}
            filterScanMode={filterScanMode}
          />
        </div>
      </div>
    </div>
  );
}
