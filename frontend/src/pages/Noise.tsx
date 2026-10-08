import { motion } from "framer-motion";
import { MailX } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { IntentBadge } from "../components/StatusBadge";
import { EmptyState } from "../components/ui/EmptyState";
import { TableSkeleton } from "../components/ui/Skeleton";
import { useToast } from "../components/ui/Toast";
import { useI18n } from "../i18n";
import { formatDateTime, senderName } from "../lib/format";
import type { EmailItem } from "../lib/types";

export function Noise() {
  const { t, lang } = useI18n();
  const { notify } = useToast();
  const [emails, setEmails] = useState<EmailItem[] | null>(null);

  useEffect(() => {
    api
      .noise()
      .then(setEmails)
      .catch((err) => {
        notify(err instanceof Error ? err.message : t.errors.load, "error");
        setEmails([]);
      });
  }, [notify, t.errors.load]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold tracking-tight">{t.noise.title}</h1>
        <p className="text-sm text-muted">{t.noise.subtitle}</p>
      </div>

      {emails === null ? (
        <TableSkeleton />
      ) : emails.length === 0 ? (
        <EmptyState icon={MailX} title={t.noise.empty} />
      ) : (
        <div className="space-y-2">
          {emails.map((email, i) => (
            <motion.div
              key={email.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(i, 12) * 0.02, duration: 0.25 }}
              className="flex items-center justify-between gap-3 rounded-xl border border-border bg-surface p-3.5 shadow-card"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{email.subject}</p>
                <p className="truncate text-xs text-muted">
                  {senderName(email.sender)} · {formatDateTime(email.received_at, lang)}
                </p>
              </div>
              <IntentBadge intent={email.effective_intent} withIcon={false} />
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
