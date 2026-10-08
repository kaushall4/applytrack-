import { AnimatePresence } from "framer-motion";
import { ListChecks } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { ReviewCard } from "../components/ReviewCard";
import { EmptyState } from "../components/ui/EmptyState";
import { TableSkeleton } from "../components/ui/Skeleton";
import { useToast } from "../components/ui/Toast";
import { useI18n } from "../i18n";
import type { EmailItem } from "../lib/types";

export function Review() {
  const { t } = useI18n();
  const { notify } = useToast();
  const [emails, setEmails] = useState<EmailItem[] | null>(null);

  useEffect(() => {
    api
      .needsReview()
      .then(setEmails)
      .catch((err) => {
        notify(err instanceof Error ? err.message : t.errors.load, "error");
        setEmails([]);
      });
  }, [notify, t.errors.load]);

  const resolve = (id: number) =>
    setEmails((prev) => (prev ? prev.filter((e) => e.id !== id) : prev));

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold tracking-tight">{t.review.title}</h1>
        <p className="text-sm text-muted">{t.review.subtitle}</p>
      </div>

      {emails === null ? (
        <TableSkeleton />
      ) : emails.length === 0 ? (
        <EmptyState icon={ListChecks} title={t.review.empty} />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          <AnimatePresence mode="popLayout">
            {emails.map((email) => (
              <ReviewCard key={email.id} email={email} onResolved={resolve} />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
