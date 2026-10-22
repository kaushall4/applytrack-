import { CalendarCheck } from "lucide-react";

import { useI18n } from "../i18n";
import { INTENT_META, STATUS_META } from "../lib/status";
import type { Application, Intent, Status } from "../lib/types";
import { Badge } from "./ui/Badge";

const INTERVIEW_STATUSES: Status[] = ["interview_invite", "next_round", "offer"];

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
      className="inline-flex items-center gap-1 rounded-full border border-indigo-300/70 px-2 py-0.5 text-[11px] font-medium text-indigo-600 dark:border-indigo-400/30 dark:text-indigo-300"
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
