import { motion } from "framer-motion";
import { KeyRound, RefreshCw } from "lucide-react";

import { useI18n } from "../i18n";
import { cn } from "../lib/utils";

export function SessionExpiredBanner({
  email,
  busy,
  onReconnect,
}: {
  email: string | null;
  busy: boolean;
  onReconnect: () => void;
}) {
  const { t } = useI18n();

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      role="alert"
      className="mb-6 flex flex-wrap items-center gap-4 rounded-2xl border border-amber-500/30 bg-amber-50 p-4 dark:bg-amber-500/10"
    >
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-amber-500/15 text-amber-600 dark:text-amber-300">
        <KeyRound className="h-5 w-5" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-amber-900 dark:text-amber-100">{t.session.title}</p>
        <p className="mt-0.5 text-xs text-amber-800/80 dark:text-amber-200/80">
          {t.session.body}
          {email && <span className="font-medium"> ({email})</span>}
        </p>
        {busy && <p className="mt-1 text-xs text-amber-800/80 dark:text-amber-200/80">{t.session.hint}</p>}
      </div>
      <button
        onClick={onReconnect}
        disabled={busy}
        className="inline-flex items-center gap-1.5 rounded-xl bg-amber-500 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-opacity hover:opacity-90 disabled:opacity-60"
      >
        <RefreshCw className={cn("h-4 w-4", busy && "animate-spin")} />
        {busy ? t.header.reconnecting : t.header.reconnect}
      </button>
    </motion.div>
  );
}
