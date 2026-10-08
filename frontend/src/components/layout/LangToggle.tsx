import { useI18n } from "../../i18n";
import type { Language } from "../../lib/types";

export function LangToggle() {
  const { lang, setLang } = useI18n();
  const langs: Language[] = ["de", "en"];

  return (
    <div className="flex items-center rounded-lg border border-border bg-surface p-0.5">
      {langs.map((l) => (
        <button
          key={l}
          onClick={() => setLang(l)}
          aria-pressed={lang === l}
          className={`rounded-md px-2 py-1 text-xs font-semibold transition-colors ${
            lang === l ? "bg-brand text-brand-fg" : "text-muted hover:text-fg"
          }`}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
