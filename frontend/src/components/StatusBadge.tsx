import { useI18n } from "../i18n";
import { INTENT_META, STATUS_META } from "../lib/status";
import type { Intent, Status } from "../lib/types";
import { Badge } from "./ui/Badge";

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
