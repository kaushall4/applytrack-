import { Plug } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { api } from "../api/client";
import { ApplicationDetail } from "../components/ApplicationDetail";
import { ApplicationsTable } from "../components/ApplicationsTable";
import { StatCards } from "../components/StatCards";
import { StatusDonut } from "../components/StatusDonut";
import { EmptyState } from "../components/ui/EmptyState";
import { StatCardsSkeleton, TableSkeleton } from "../components/ui/Skeleton";
import { useToast } from "../components/ui/Toast";
import { useI18n } from "../i18n";
import type { Application, Language, Stats, Status } from "../lib/types";

export function Dashboard({ onConnect }: { onConnect: () => void }) {
  const { t } = useI18n();
  const { notify } = useToast();

  const [stats, setStats] = useState<Stats | null>(null);
  const [apps, setApps] = useState<Application[] | null>(null);
  const [allApps, setAllApps] = useState<Application[]>([]);
  const [statusFilter, setStatusFilter] = useState<Status | "">("");
  const [languageFilter, setLanguageFilter] = useState<Language | "">("");
  const [selected, setSelected] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const [s, a] = await Promise.all([
        api.stats(),
        api.applications({ status: statusFilter, language: languageFilter }),
      ]);
      setStats(s);
      setApps(a);
      // Keep an unfiltered snapshot for the distribution chart.
      if (!statusFilter && !languageFilter) setAllApps(a);
    } catch (err) {
      notify(err instanceof Error ? err.message : t.errors.load, "error");
      setApps([]);
    }
  }, [statusFilter, languageFilter, notify, t.errors.load]);

  useEffect(() => {
    void load();
  }, [load]);

  const isEmpty = apps !== null && apps.length === 0 && !statusFilter && !languageFilter;

  return (
    <div className="space-y-6">
      {stats ? <StatCards stats={stats} /> : <StatCardsSkeleton />}

      {apps === null ? (
        <TableSkeleton />
      ) : isEmpty ? (
        <EmptyState
          icon={Plug}
          title={t.empty.title}
          body={t.empty.body}
          action={
            <button
              onClick={onConnect}
              className="inline-flex items-center gap-1.5 rounded-xl bg-brand px-4 py-2 text-sm font-medium text-brand-fg shadow-sm hover:opacity-90"
            >
              <Plug className="h-4 w-4" />
              {t.header.connect}
            </button>
          }
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">{allApps.length > 0 && <StatusDonut applications={allApps} />}</div>
          <div className="lg:col-span-2">
            <ApplicationsTable
              applications={apps}
              statusFilter={statusFilter}
              languageFilter={languageFilter}
              onStatusFilter={setStatusFilter}
              onLanguageFilter={setLanguageFilter}
              onSelect={(a) => setSelected(a.id)}
            />
          </div>
        </div>
      )}

      <ApplicationDetail applicationId={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
