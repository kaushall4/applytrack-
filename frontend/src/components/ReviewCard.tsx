import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { useState } from "react";

import { api } from "../api/client";
import { useI18n } from "../i18n";
import { confidencePct, formatDateTime, senderName } from "../lib/format";
import { ALL_INTENTS, INTENT_META } from "../lib/status";
import type { EmailItem, Intent } from "../lib/types";
import { cn } from "../lib/utils";
import { IntentBadge } from "./StatusBadge";
import { useToast } from "./ui/Toast";

export function ReviewCard({
  email,
  onResolved,
}: {
  email: EmailItem;
  onResolved: (id: number) => void;
}) {
  const { t, lang } = useI18n();
  const { notify } = useToast();
  const [choice, setChoice] = useState<Intent>(email.effective_intent);
  const [busy, setBusy] = useState(false);

  const meta = INTENT_META[email.intent];

  const save = async () => {
    setBusy(true);
    try {
      await api.override(email.id, choice);
      notify(t.toast.overrideSaved, "success");
      onResolved(email.id); // optimistic removal from the queue
    } catch (err) {
      notify(err instanceof Error ? err.message : t.errors.generic, "error");
      setBusy(false);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.25 }}
      className="rounded-2xl border border-border bg-surface p-4 shadow-card"
    >
      <div className="flex items-start gap-3">
        <span className={cn("mt-1 h-2.5 w-2.5 shrink-0 rounded-full", meta.dot)} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="truncate text-xs font-medium text-muted">{senderName(email.sender)}</span>
            <span className="text-[11px] text-muted">{formatDateTime(email.received_at, lang)}</span>
          </div>
          <p className="mt-0.5 truncate text-sm font-medium">{email.subject}</p>
          <p className="mt-1 line-clamp-2 text-xs text-muted">{email.body_snippet}</p>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <IntentBadge intent={email.intent} />
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-500">
              {confidencePct(email.confidence)} · {t.review.lowConfidence}
            </span>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <select
              value={choice}
              onChange={(e) => setChoice(e.target.value as Intent)}
              className="h-9 rounded-lg border border-border bg-bg px-2 text-sm outline-none focus:ring-2 focus:ring-brand/40"
            >
              {ALL_INTENTS.map((i) => (
                <option key={i} value={i}>
                  {t.intent[i]}
                </option>
              ))}
            </select>
            <button
              onClick={save}
              disabled={busy}
              className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-brand px-3 text-sm font-medium text-brand-fg shadow-sm transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              <Check className="h-4 w-4" />
              {t.review.save}
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
