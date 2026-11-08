import { CalendarCheck, Hourglass } from "lucide-react";

import { useI18n } from "../i18n";
import { INTENT_META, STATUS_META } from "../lib/status";
import type { Application, Intent, Status } from "../lib/types";
import { Badge } from "./ui/Badge";

const INTERVIEW_STATUSES: Status[] = ["interview_invite", "next_round", "offer"];

const QUIET_AFTER_DAYS = 14;

/** Days since the last mail of an interview process that has gone quiet, else null. */
// eslint-disable-next-line react-refresh/only-export-components
export function quietDays(
  app: Pick<Application, "current_status" | "last_event_at">,
  now: Date = new Date(),
): number | null {
  if (app.current_status !== "interview_invite" && app.current_status !== "next_round") return null;
  if (!app.last_event_at) return null;
  const days = Math.floor((now.getTime() - new Date(app.last_event_at).getTime()) / 86_400_000);
  return days >= QUIET_AFTER_DAYS ? days : null;
}

/** "Seit 19 Tagen still" next to an interview that hasn't been answered. */
export function QuietTag({ app }: { app: Pick<Application, "current_status" | "last_event_at"> }) {
  const { t } = useI18n();
  const days = quietDays(app);
  if (days === null) return null;
  return (
    <span
      title={t.table.quietHint}
      className="inline-flex items-center gap-1 whitespace-nowrap rounded-full border border-dashed border-muted/50 px-2 py-0.5 text-[11px] font-medium text-muted"
    >
      <Hourglass className="h-3 w-3" />
      {t.table.quietTag(days)}
    </span>
  );
}

/** An interview happened, but the status no longer says so (e.g. rejected afterwards). */
// eslint-disable-next-line react-refresh/only-export-components
export function hadPastInterview(app: Pick<Application, "reached_interview" | "current_status">) {
  return app.reached_interview && !INTERVIEW_STATUSES.includes(app.current_status);
}

type RoundInfo = Pick<Application, "reached_interview" | "current_status" | "interview_rounds">;

/**
 * Marker next to the status that keeps the interview history visible:
 * "Gespräch geführt" after a past interview, "2. Runde erreicht" once a job got
 * past the first round — also when it ended in a rejection.
 */
export function InterviewedTag({ app }: { app: RoundInfo }) {
  const { t } = useI18n();
  const rounds = app.interview_rounds ?? 0;
  const label =
    rounds >= 2 ? t.table.roundTag(rounds) : hadPastInterview(app) ? t.table.interviewedTag : null;
  if (!label) return null;
  return (
    <span
      title={rounds >= 2 ? t.table.advancedHint : t.table.interviewedHint}
      className="inline-flex items-center gap-1 whitespace-nowrap rounded-full border border-brand/35 px-2 py-0.5 text-[11px] font-medium text-brand"
    >
      <CalendarCheck className="h-3 w-3" />
      {label}
    </span>
  );
}

export function StatusBadge({ status, withIcon = true }: { status: Status; withIcon?: boolean }) {
  const { t } = useI18n();
  const meta = STATUS_META[status];
  const Icon = meta.icon;
  return (
    <Badge className={meta.badge}>
      {withIcon && <Icon className="h-3 w-3" strokeWidth={2.4} />}
      {t.status[status]}
    </Badge>
  );
}

export function IntentBadge({ intent, withIcon = true }: { intent: Intent; withIcon?: boolean }) {
  const { t } = useI18n();
  const meta = INTENT_META[intent];
  const Icon = meta.icon;
  return (
    <Badge className={meta.badge}>
      {withIcon && <Icon className="h-3 w-3" strokeWidth={2.4} />}
      {t.intent[intent]}
    </Badge>
  );
}
