import { motion } from "framer-motion";
import { ArrowDownLeft, ArrowUpRight, X } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { useI18n } from "../i18n";
import { confidencePct, formatDateTime, senderName } from "../lib/format";
import { INTENT_META } from "../lib/status";
import type { ApplicationDetail as Detail } from "../lib/types";
import { IntentBadge, StatusBadge } from "./StatusBadge";
import { Modal } from "./ui/Modal";
import { Skeleton } from "./ui/Skeleton";

export function ApplicationDetail({
  applicationId,
  onClose,
}: {
  applicationId: number | null;
  onClose: () => void;
}) {
  const { t, lang } = useI18n();
  const [detail, setDetail] = useState<Detail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (applicationId == null) {
      setDetail(null);
      return;
    }
    setLoading(true);
    api
      .application(applicationId)
      .then(setDetail)
      .catch(() => setDetail(null))
      .finally(() => setLoading(false));
  }, [applicationId]);

  return (
    <Modal open={applicationId != null} onClose={onClose} labelledBy="detail-title">
      <div className="sticky top-0 z-10 flex items-start justify-between gap-4 border-b border-border glass px-5 py-4">
        <div>
          {detail ? (
            <>
              <h2 id="detail-title" className="text-lg font-bold">
                {detail.company}
              </h2>
              <p className="text-sm text-muted">{detail.role ?? "—"}</p>
              <div className="mt-2">
                <StatusBadge status={detail.current_status} />
              </div>
            </>
          ) : (
            <Skeleton className="h-12 w-48" />
          )}
        </div>
        <button
          onClick={onClose}
          className="grid h-8 w-8 place-items-center rounded-lg border border-border bg-surface text-muted transition-colors hover:text-fg"
          aria-label={t.detail.close}
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="px-5 py-5">
        <h3 className="mb-4 text-xs font-semibold uppercase tracking-wide text-muted">
          {t.detail.timeline}
        </h3>

        {loading && (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-xl" />
            ))}
          </div>
        )}

        {detail && (
          <ol className="relative ml-1 space-y-4 border-l border-border pl-6">
            {detail.emails.map((email, i) => {
              const meta = INTENT_META[email.effective_intent];
              const outbound = email.direction === "sent";
              return (
                <motion.li
                  key={email.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.04, duration: 0.25 }}
                  className="relative"
                >
                  <span
                    className={`absolute -left-[1.72rem] top-1.5 grid h-3.5 w-3.5 place-items-center rounded-full ring-4 ring-surface ${meta.dot}`}
                  />
                  <div className="rounded-xl border border-border bg-bg p-3.5 transition-shadow hover:shadow-card">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted">
                        {outbound ? (
                          <ArrowUpRight className="h-3.5 w-3.5 text-brand" />
                        ) : (
                          <ArrowDownLeft className="h-3.5 w-3.5" />
                        )}
                        {outbound ? t.detail.sent : t.detail.received} · {senderName(email.sender)}
                      </span>
                      <span className="text-xs text-muted">{formatDateTime(email.received_at, lang)}</span>
                    </div>
                    <p className="mt-1.5 text-sm font-medium">{email.subject}</p>
                    <p className="mt-1 line-clamp-2 text-xs text-muted">{email.body_snippet}</p>

                    <div className="mt-3 flex flex-wrap items-center gap-3">
                      <IntentBadge intent={email.effective_intent} />
                      <div className="flex items-center gap-1.5">
                        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-2">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${Math.round(email.confidence * 100)}%`, background: meta.hex }}
                          />
                        </div>
                        <span className="text-[11px] text-muted">{confidencePct(email.confidence)}</span>
                      </div>
                      {email.manual_override && (
                        <span className="rounded bg-brand/10 px-1.5 py-0.5 text-[10px] font-semibold text-brand">
                          ✎ {t.detail.correct}
                        </span>
                      )}
                    </div>
                  </div>
                </motion.li>
              );
            })}
          </ol>
        )}
      </div>
    </Modal>
  );
}
