import { Loader2, Smartphone } from "lucide-react";
import { useState, type FormEvent } from "react";

import { api, storePairingKey } from "../api/client";
import { useI18n } from "../i18n";

/** Shown on a phone that opened ApplyTrack without (or with an old) pairing key. */
export function PairingRequired() {
  const { t } = useI18n();
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(false);
    try {
      const { key } = await api.pair(code);
      storePairingKey(key);
      window.location.replace("/");
    } catch {
      setError(true);
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto mt-16 flex max-w-sm flex-col items-center gap-4 rounded-2xl border border-border bg-surface p-6 text-center shadow-sm">
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-brand/15 text-brand">
        <Smartphone className="h-6 w-6" />
      </span>
      <h1 className="text-base font-semibold">{t.phone.pairTitle}</h1>
      <p className="text-sm text-muted">{t.phone.pairBody}</p>

      <form onSubmit={submit} className="flex w-full flex-col gap-2 border-t border-border pt-4">
        <label htmlFor="pair-code" className="text-xs text-muted">
          {t.phone.codePrompt}
        </label>
        <input
          id="pair-code"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={7}
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/[^\d ]/g, ""))}
          placeholder="123 456"
          className="rounded-xl border border-border bg-surface-2 px-3 py-2 text-center font-mono text-2xl tracking-[0.3em] outline-none focus:ring-2 focus:ring-brand"
        />
        {error && <p className="text-xs text-rose-500">{t.phone.codeWrong}</p>}
        <button
          type="submit"
          disabled={busy || code.replace(/\D/g, "").length !== 6}
          className="flex items-center justify-center gap-2 rounded-xl bg-brand px-4 py-2 text-sm font-medium text-brand-fg shadow-sm transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {busy && <Loader2 className="h-4 w-4 animate-spin" />}
          {t.phone.codeSubmit}
        </button>
      </form>
    </div>
  );
}
