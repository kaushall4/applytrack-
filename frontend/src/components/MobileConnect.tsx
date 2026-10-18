import { Copy, Loader2, RotateCcw, ShieldAlert, Smartphone, Wifi, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { api } from "../api/client";
import { useI18n } from "../i18n";
import type { MobileStatus } from "../lib/types";
import { useToast } from "./ui/Toast";
import { Modal } from "./ui/Modal";

/** PC-only dialog: switch on phone access and pair the phone via QR code. */
export function MobileConnect({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useI18n();
  const { notify } = useToast();
  const [status, setStatus] = useState<MobileStatus | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    setStatus(null);
    api
      .mobileStatus()
      .then(setStatus)
      .catch((err) => notify(err instanceof Error ? err.message : t.errors.generic, "error"));
  }, [notify, t.errors.generic]);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  const enable = async () => {
    setBusy(true);
    try {
      setStatus(await api.enableMobile());
    } catch (err) {
      notify(err instanceof Error ? err.message : t.errors.generic, "error");
    } finally {
      setBusy(false);
    }
  };

  const copy = async () => {
    if (!status?.url) return;
    try {
      await navigator.clipboard.writeText(status.url);
      notify(t.phone.copied, "success");
    } catch {
      /* clipboard blocked — the link is still selectable */
    }
  };

  return (
    <Modal open={open} onClose={onClose} labelledBy="mobile-title">
      <div className="flex items-start gap-3 border-b border-border p-5">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand/15 text-brand">
          <Smartphone className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <h2 id="mobile-title" className="text-base font-semibold">
            {t.phone.title}
          </h2>
          <p className="mt-1 text-sm text-muted">{t.phone.intro}</p>
        </div>
        <button onClick={onClose} className="text-muted hover:text-fg" aria-label="Close">
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="p-5">
        {!status ? (
          <div className="grid place-items-center py-10 text-muted">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : status.enabled ? (
          <Paired status={status} onCopy={copy} />
        ) : status.restart_required ? (
          <Notice icon={RotateCcw} title={t.phone.restartTitle} body={t.phone.restartBody}>
            <p className="mt-2 flex items-start gap-1.5 text-xs text-muted">
              <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              {t.phone.firewall}
            </p>
          </Notice>
        ) : (
          <div className="flex flex-col items-start gap-3">
            <p className="flex items-start gap-1.5 text-sm text-muted">
              <Wifi className="mt-0.5 h-4 w-4 shrink-0" />
              {t.phone.note}
            </p>
            <button
              onClick={enable}
              disabled={busy}
              className="flex items-center gap-2 rounded-xl bg-brand px-4 py-2 text-sm font-medium text-brand-fg shadow-sm transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Smartphone className="h-4 w-4" />}
              {busy ? t.phone.enabling : t.phone.enable}
            </button>
          </div>
        )}
      </div>
    </Modal>
  );
}

function Paired({ status, onCopy }: { status: MobileStatus; onCopy: () => void }) {
  const { t } = useI18n();

  if (!status.url || !status.qr_svg) {
    return <Notice icon={Wifi} title={t.phone.noNetwork} body={t.phone.firewall} />;
  }

  return (
    <div className="grid gap-6 sm:grid-cols-[auto,1fr]">
      <div className="flex flex-col items-center gap-2">
        <div
          className="w-60 rounded-xl bg-white p-2 shadow-sm ring-1 ring-border [&>svg]:block [&>svg]:h-auto [&>svg]:w-full"
          // QR code generated locally by the backend (segno) — static SVG markup.
          dangerouslySetInnerHTML={{ __html: status.qr_svg }}
        />
      </div>

      <div className="min-w-0 space-y-4 text-sm">
        <div>
          <p className="font-semibold">{t.phone.scan}</p>
          <p className="mt-0.5 text-muted">
            {status.cloud ? t.phone.cloudScanHint : t.phone.scanHint}
          </p>
        </div>
        <div>
          <p className="font-semibold">{t.phone.install}</p>
          <ul className="mt-1 space-y-1 text-muted">
            <li>{t.phone.android}</li>
            <li>{t.phone.iphone}</li>
          </ul>
          <p className="mt-1 text-xs text-muted">{t.phone.iphoneTip}</p>
        </div>
        <p className="text-xs text-muted">{status.cloud ? t.phone.cloudNote : t.phone.note}</p>
      </div>

      <div className="min-w-0 sm:col-span-2">
        <p className="text-xs text-muted">{t.phone.linkLabel}</p>
        <div className="mt-1 flex items-center gap-2 rounded-xl border border-border bg-surface-2/60 p-2">
          <code className="min-w-0 flex-1 select-all truncate text-xs">{status.url}</code>
          <button
            onClick={onCopy}
            className="flex shrink-0 items-center gap-1 rounded-lg border border-border bg-surface px-2 py-1 text-xs font-medium hover:bg-surface-2"
          >
            <Copy className="h-3.5 w-3.5" />
            {t.phone.copy}
          </button>
        </div>
        <p className="mt-2 flex items-start gap-1.5 text-xs text-amber-700 dark:text-amber-300">
          <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          {t.phone.secret}
        </p>
      </div>

      {status.pair_code && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-xl border border-border bg-surface-2/50 p-3 sm:col-span-2">
          <div>
            <p className="text-xs text-muted">{t.phone.codeLabel}</p>
            <p className="font-mono text-2xl font-bold tracking-[0.3em]">
              {status.pair_code.slice(0, 3)} {status.pair_code.slice(3)}
            </p>
          </div>
          <p className="min-w-0 flex-1 text-xs text-muted">{t.phone.codeHint}</p>
        </div>
      )}
    </div>
  );
}

function Notice({
  icon: Icon,
  title,
  body,
  children,
}: {
  icon: typeof Wifi;
  title: string;
  body: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-border bg-surface-2/50 p-4">
      <Icon className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
      <div>
        <p className="text-sm font-semibold">{title}</p>
        <p className="mt-1 text-sm text-muted">{body}</p>
        {children}
      </div>
    </div>
  );
}
