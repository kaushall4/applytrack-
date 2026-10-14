import { RefreshCw, Smartphone } from "lucide-react";

import { useI18n } from "../i18n";

/** Shown on a phone that opened ApplyTrack without (or with an old) pairing key. */
export function PairingRequired() {
  const { t } = useI18n();
  return (
    <div className="mx-auto mt-16 flex max-w-sm flex-col items-center gap-4 rounded-2xl border border-border bg-surface p-6 text-center shadow-sm">
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-brand/15 text-brand">
        <Smartphone className="h-6 w-6" />
      </span>
      <h1 className="text-base font-semibold">{t.phone.pairTitle}</h1>
      <p className="text-sm text-muted">{t.phone.pairBody}</p>
      <button
        onClick={() => window.location.reload()}
        className="flex items-center gap-1.5 rounded-xl border border-border bg-surface px-3 py-1.5 text-sm font-medium hover:bg-surface-2"
      >
        <RefreshCw className="h-4 w-4" />
        {t.phone.retry}
      </button>
    </div>
  );
}
