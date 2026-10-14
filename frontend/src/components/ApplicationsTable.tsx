import { motion } from "framer-motion";
import { ChevronDown, ChevronUp, Search, X } from "lucide-react";
import { useMemo, useState } from "react";

import { useI18n } from "../i18n";
import { formatDate, relativeTime } from "../lib/format";
import { ALL_STATUSES, STATUS_META } from "../lib/status";
import type { Application, Language, StatusFilter } from "../lib/types";
import { cn } from "../lib/utils";
import { hadPastInterview, InterviewedTag, StatusBadge } from "./StatusBadge";

type SortKey = "company" | "role" | "status" | "first_applied_at" | "last_event_at";

const SORT_FIELD: Record<SortKey, keyof Application> = {
  company: "company",
  role: "role",
  status: "current_status",
  first_applied_at: "first_applied_at",
  last_event_at: "last_event_at",
};

interface Props {
  applications: Application[];
  statusFilter: StatusFilter;
  languageFilter: Language | "";
  onStatusFilter: (s: StatusFilter) => void;
  onLanguageFilter: (l: Language | "") => void;
  onSelect: (app: Application) => void;
}

function Chip({
  active,
  onClick,
  title,
  children,
}: {
  active: boolean;
  onClick: () => void;
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={cn(
        "inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border px-3 py-1.5 text-xs font-medium transition-colors sm:py-1",
        active
          ? "border-brand bg-brand text-brand-fg shadow-sm"
          : "border-border bg-surface text-muted hover:text-fg hover:border-brand/40",
      )}
    >
      {children}
    </button>
  );
}

export function ApplicationsTable({
  applications,
  statusFilter,
  languageFilter,
  onStatusFilter,
  onLanguageFilter,
  onSelect,
}: Props) {
  const { t, lang } = useI18n();
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("last_event_at");
  const [asc, setAsc] = useState(false);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    const field = SORT_FIELD[sort];
    return applications
      .filter((a) => !q || a.company.toLowerCase().includes(q) || (a.role ?? "").toLowerCase().includes(q))
      .sort((a, b) => {
        const av = (a[field] ?? "") as string;
        const bv = (b[field] ?? "") as string;
        const cmp = av < bv ? -1 : av > bv ? 1 : 0;
        return asc ? cmp : -cmp;
      });
  }, [applications, query, sort, asc]);

  const toggleSort = (key: SortKey) => {
    if (sort === key) setAsc((v) => !v);
    else {
      setSort(key);
      setAsc(true);
    }
  };

  const SortHead = ({ k, label, right }: { k: SortKey; label: string; right?: boolean }) => (
    <th className={cn("px-4 py-3", right && "text-right")}>
      <button
        onClick={() => toggleSort(k)}
        className={cn("inline-flex items-center gap-1 font-medium transition-colors hover:text-fg", right && "flex-row-reverse")}
      >
        {label}
        {sort === k ? (
          asc ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />
        ) : (
          <span className="h-3.5 w-3.5" />
        )}
      </button>
    </th>
  );

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-card">
      {/* Filter bar */}
      <div className="space-y-3 border-b border-border p-3.5">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t.table.search}
            className="h-10 w-full rounded-xl border border-border bg-bg pl-9 pr-3 text-sm outline-none transition-shadow focus:ring-2 focus:ring-brand/40"
          />
        </div>
        {/* Swipeable single row on phones, wrapping on larger screens. */}
        <div className="-mx-3.5 flex items-center gap-1.5 overflow-x-auto px-3.5 pb-1 sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0 sm:pb-0">
          <Chip active={statusFilter === ""} onClick={() => onStatusFilter("")}>
            {t.table.all}
          </Chip>
          {statusFilter === "awaiting" && (
            <Chip active onClick={() => onStatusFilter("")}>
              {t.stats.awaiting}
              <X className="h-3 w-3" />
            </Chip>
          )}
          {ALL_STATUSES.map((s) => {
            // The interview chip lists every application that had an interview —
            // also those rejected afterwards — not only the currently open ones.
            const value: StatusFilter = s === "interview_invite" ? "interviewed" : s;
            return (
              <Chip
                key={s}
                active={statusFilter === value}
                title={value === "interviewed" ? t.table.interviewedHint : undefined}
                onClick={() => onStatusFilter(statusFilter === value ? "" : value)}
              >
                <span className={cn("h-2 w-2 rounded-full", STATUS_META[s].dot)} />
                {value === "interviewed" ? t.table.interviewed : t.status[s]}
              </Chip>
            );
          })}
          <span className="mx-1 h-4 w-px bg-border" />
          {(["de", "en"] as Language[]).map((l) => (
            <Chip key={l} active={languageFilter === l} onClick={() => onLanguageFilter(languageFilter === l ? "" : l)}>
              {l.toUpperCase()}
            </Chip>
          ))}
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="px-4 py-12 text-center text-sm text-muted">{t.table.noResults}</div>
      ) : (
        <>
        {/* Phone: one tappable card per application. */}
        <ul className="divide-y divide-border/60 md:hidden">
          {rows.map((a) => (
            <li key={a.id}>
              <button
                onClick={() => onSelect(a)}
                className="flex w-full flex-col gap-1.5 px-4 py-3.5 text-left active:bg-surface-2/70"
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="font-semibold">{a.company}</span>
                  <span className="shrink-0 text-xs text-muted">
                    {relativeTime(a.last_event_at, lang)}
                  </span>
                </div>
                {a.role && <span className="text-sm text-muted">{a.role}</span>}
                <div className="flex flex-wrap items-center gap-1.5">
                  <StatusBadge status={a.current_status} />
                  {hadPastInterview(a) && <InterviewedTag />}
                  <span className="ml-auto text-[11px] text-muted">
                    {t.table.applied} {formatDate(a.first_applied_at, lang)}
                  </span>
                </div>
              </button>
            </li>
          ))}
        </ul>

        {/* Tablet / desktop: sortable table. */}
        <div className="hidden overflow-x-auto md:block">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted">
                <SortHead k="company" label={t.table.company} />
                <SortHead k="role" label={t.table.role} />
                <SortHead k="status" label={t.table.status} />
                <SortHead k="first_applied_at" label={t.table.applied} />
                <SortHead k="last_event_at" label={t.table.lastActivity} />
                <th className="px-4 py-3 text-right">{t.table.language}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a, i) => (
                <motion.tr
                  key={a.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(i, 14) * 0.02, duration: 0.25 }}
                  onClick={() => onSelect(a)}
                  className="group cursor-pointer border-b border-border/50 transition-colors last:border-0 hover:bg-surface-2/70"
                >
                  <td className="px-4 py-3 font-medium">
                    <span className="transition-colors group-hover:text-brand">{a.company}</span>
                  </td>
                  <td className="px-4 py-3 text-muted">{a.role ?? "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <StatusBadge status={a.current_status} />
                      {hadPastInterview(a) && <InterviewedTag />}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted">{formatDate(a.first_applied_at, lang)}</td>
                  <td className="px-4 py-3 text-muted">{relativeTime(a.last_event_at, lang)}</td>
                  <td className="px-4 py-3 text-right">
                    <span className="rounded border border-border px-1.5 py-0.5 text-[10px] font-semibold text-muted">
                      {a.language.toUpperCase()}
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
        </>
      )}
    </div>
  );
}
