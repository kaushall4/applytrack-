import type {
  AccountStatus,
  Application,
  ApplicationDetail,
  EmailItem,
  Intent,
  Language,
  MobileStatus,
  Stats,
  StatusFilter,
  SyncResult,
} from "../lib/types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    /** Machine-readable reason, e.g. "session_expired" or "pairing_required". */
    readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// --- Phone pairing ---------------------------------------------------------
// The phone receives the secret key once through the QR code (`/?key=…`); it is
// kept on the device and sent with every request. The PC itself needs no key.
const KEY_STORAGE = "applytrack.key";
const KEY_HEADER = "X-ApplyTrack-Key";

function readKey(): string | null {
  try {
    return localStorage.getItem(KEY_STORAGE);
  } catch {
    return null;
  }
}

const isStandalone = () =>
  window.matchMedia?.("(display-mode: standalone)").matches ||
  (navigator as Navigator & { standalone?: boolean }).standalone === true;

export function storePairingKey(key: string): void {
  try {
    localStorage.setItem(KEY_STORAGE, key);
  } catch {
    /* storage blocked — pairing will not survive a restart */
  }
  pointManifestAtKey(key);
}

// An app added to the iPhone home screen gets storage separate from Safari, so
// the key has to travel inside its start URL: the manifest is requested with
// the key and the server answers with `start_url: /?key=…`.
function pointManifestAtKey(key: string): void {
  const link = document.querySelector<HTMLLinkElement>('link[rel="manifest"]');
  if (link) link.href = `/manifest.webmanifest?key=${encodeURIComponent(key)}`;
}

/** Pick up the key from the pairing link (`/?key=…`) and keep it on the device. */
export function capturePairingKey(): void {
  const url = new URL(window.location.href);
  const key = url.searchParams.get("key");
  if (key) {
    storePairingKey(key);
    // In Safari the key stays in the address bar on purpose: "Add to Home
    // Screen" may use the current URL as the app's start page. Inside the
    // installed app it is no longer needed there.
    if (isStandalone()) {
      url.searchParams.delete("key");
      window.history.replaceState(null, "", url.pathname + url.search + url.hash);
    }
    return;
  }
  const stored = readKey();
  if (stored) pointManifestAtKey(stored);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const key = readKey();
  if (key) headers[KEY_HEADER] = key;

  let resp: Response;
  try {
    resp = await fetch(`/api${path}`, { headers, ...init });
  } catch {
    throw new ApiError("Network error — is the backend running?", 0);
  }

  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`;
    let code: string | undefined;
    try {
      const body = await resp.json();
      if (body?.detail) detail = body.detail;
      if (typeof body?.code === "string") code = body.code;
    } catch {
      /* non-JSON error body — keep generic message */
    }
    throw new ApiError(detail, resp.status, code);
  }

  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export interface ApplicationFilters {
  status?: StatusFilter;
  language?: Language | "";
  sort?: string;
  order?: "asc" | "desc";
}

export const api = {
  // Account
  accountStatus: () => request<AccountStatus>("/account"),
  connect: (email_address: string) =>
    request<AccountStatus>("/account/connect", {
      method: "POST",
      body: JSON.stringify({ email_address }),
    }),
  disconnect: () =>
    request<{ message: string }>("/account/disconnect", { method: "POST" }),

  // Phone app (PC only)
  mobileStatus: () => request<MobileStatus>("/mobile"),
  enableMobile: () => request<MobileStatus>("/mobile/enable", { method: "POST" }),
  pair: (code: string) =>
    request<{ key: string }>("/pair", { method: "POST", body: JSON.stringify({ code }) }),

  // Sync
  sync: (full = false) =>
    request<SyncResult>(`/sync?full=${full}`, { method: "POST" }),

  // Applications
  stats: () => request<Stats>("/applications/stats"),
  applications: (filters: ApplicationFilters = {}) => {
    const params = new URLSearchParams();
    // "interviewed" = every application that had an interview, whatever came after;
    // "awaiting" = still waiting for an answer. Both are server-side stages.
    if (filters.status === "interviewed") params.set("stage", "interview");
    else if (filters.status === "awaiting") params.set("stage", "awaiting");
    else if (filters.status) params.set("status", filters.status);
    if (filters.language) params.set("language", filters.language);
    if (filters.sort) params.set("sort", filters.sort);
    if (filters.order) params.set("order", filters.order);
    const qs = params.toString();
    return request<Application[]>(`/applications${qs ? `?${qs}` : ""}`);
  },
  application: (id: number) => request<ApplicationDetail>(`/applications/${id}`),

  // Emails
  needsReview: () => request<EmailItem[]>("/emails/needs-review"),
  noise: () => request<EmailItem[]>("/emails/noise"),
  override: (emailId: number, intent: Intent | null) =>
    request<EmailItem>(`/emails/${emailId}/override`, {
      method: "PATCH",
      body: JSON.stringify({ intent }),
    }),
};
