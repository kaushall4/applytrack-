import { Mail, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { useI18n } from "../i18n";
import type { AccountStatus } from "../lib/types";
import { Modal } from "./ui/Modal";
import { useToast } from "./ui/Toast";

export function ConnectAccount({
  open,
  defaultEmail,
  onClose,
  onConnected,
}: {
  open: boolean;
  /** Last connected address, prefilled so reconnecting needs no typing. */
  defaultEmail?: string | null;
  onClose: () => void;
  onConnected: (account: AccountStatus) => void;
}) {
  const { t } = useI18n();
  const { notify } = useToast();
  const [email, setEmail] = useState(defaultEmail ?? "");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (open && defaultEmail) setEmail((current) => current || defaultEmail);
  }, [open, defaultEmail]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setBusy(true);
    try {
      const account = await api.connect(email.trim());
      onConnected(account);
      onClose();
    } catch (err) {
      notify(err instanceof Error ? err.message : t.errors.generic, "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} labelledBy="connect-title">
      <form onSubmit={submit} className="p-6">
        <div className="mb-4 grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-brand to-violet-400 text-brand-fg shadow-sm">
          <Mail className="h-6 w-6" />
        </div>
        <h2 id="connect-title" className="text-lg font-bold">
          {t.connect.title}
        </h2>
        <p className="mt-2 text-sm text-muted">{t.connect.description}</p>

        <div className="relative mt-4">
          <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t.connect.placeholder}
            autoFocus
            className="h-11 w-full rounded-xl border border-border bg-bg pl-9 pr-3.5 text-sm outline-none focus:ring-2 focus:ring-brand/40"
          />
        </div>

        <button
          type="submit"
          disabled={busy || !email.trim()}
          className="mt-4 flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-brand text-sm font-semibold text-brand-fg shadow-sm hover:opacity-90 disabled:opacity-60"
        >
          {busy ? t.connect.connecting : t.connect.submit}
        </button>

        <p className="mt-3 flex items-center gap-1.5 text-xs text-muted">
          <ShieldCheck className="h-3.5 w-3.5 shrink-0 text-emerald-500" />
          {t.connect.note}
        </p>
      </form>
    </Modal>
  );
}
