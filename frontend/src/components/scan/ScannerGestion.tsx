"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useLanguage } from "../LanguageProvider";
import ScanHistoryBlock from "./ScanHistoryBlock";
import ScheduledScansBlock from "./ScheduledScansBlock";
import AlertHistoryBlock from "./AlertHistoryBlock";
import ScanResults from "./ScanResults";
import ScannerEvolutionChart from "./ScannerEvolutionChart";
import type { ScanResult } from "../../services/scanService";

export default function ScannerGestion() {
  const { t, lp } = useLanguage();
  const router = useRouter();
  const [selectedResult, setSelectedResult] = useState<ScanResult | null>(null);
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);
  const [scheduleRefreshTrigger, setScheduleRefreshTrigger] = useState(0);

  const handleSelectScan = (result: ScanResult, id?: string) => {
    setSelectedResult(result);
    setSelectedScanId(id ?? null);
  };

  const handleNewScan = () => {
    setSelectedResult(null);
    setSelectedScanId(null);
    router.push(lp("/scanner/analyses"));
  };

  if (selectedResult) {
    return (
      <ScanResults
        result={selectedResult}
        scanId={selectedScanId}
        onNewScan={handleNewScan}
      />
    );
  }

  return (
    <div className="[&>section+section]:-mt-3">
      <section>
        <ScannerEvolutionChart />
      </section>
      <section>
        <ScheduledScansBlock refreshTrigger={scheduleRefreshTrigger} />
      </section>
      <section>
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-1 min-w-0">
            <ScanHistoryBlock onSelectScan={handleSelectScan} />
          </div>
          <div className="flex-1 min-w-0">
            <AlertHistoryBlock />
          </div>
        </div>
      </section>
    </div>
  );
}
