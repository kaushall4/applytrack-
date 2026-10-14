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

/** Small marker shown next to the status: "Gespräch geführt" / "Interviewed". */
export function InterviewedTag() {
  const { t } = useI18n();
  return (
    <span
      title={t.table.interviewedHint}
      className="inline-flex items-center gap-1 rounded-full border border-indigo-300/70 px-2 py-0.5 text-[11px] font-medium text-indigo-600 dark:border-indigo-400/30 dark:text-indigo-300"
    >
      <CalendarCheck className="h-3 w-3" />
      {t.table.interviewedTag}
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
