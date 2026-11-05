import type { Language } from "./types";

const LOCALE: Record<Language, string> = { de: "de-CH", en: "en-GB" };

/** Readable mail excerpt: decodes entities, drops inline-image and link leftovers. */
export function cleanExcerpt(text: string): string {
  // An inert parsed document: nothing in the mail text can run or load here.
  const decoded = new DOMParser().parseFromString(text, "text/html").body.textContent ?? "";
  return decoded
    .replace(/\[cid:[^\]]*\]/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function formatDate(iso: string | null, lang: Language): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString(LOCALE[lang], {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function formatDateTime(iso: string | null, lang: Language): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(LOCALE[lang], {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function relativeTime(iso: string | null, lang: Language): string {
  if (!iso) return "—";
  const diffMs = Date.now() - new Date(iso).getTime();
  const days = Math.round(diffMs / 86_400_000);
  const rtf = new Intl.RelativeTimeFormat(LOCALE[lang], { numeric: "auto" });
  if (Math.abs(days) < 1) return rtf.format(0, "day");
  if (Math.abs(days) < 30) return rtf.format(-days, "day");
  return rtf.format(-Math.round(days / 30), "month");
}

export function confidencePct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

/** Extract a friendly display name from a raw "Name <email>" sender string. */
export function senderName(raw: string): string {
  const match = raw.match(/^\s*"?([^"<]+?)"?\s*</);
  if (match) return match[1].trim();
  return raw.replace(/[<>]/g, "").trim();
}
