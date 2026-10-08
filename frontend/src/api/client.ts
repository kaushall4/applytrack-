import type {
  AccountStatus,
  Application,
  ApplicationDetail,
  EmailItem,
  Intent,
  Language,
  Stats,
  Status,
  SyncResult,
} from "../lib/types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(`/api${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError("Network error — is the backend running?", 0);
  }

  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`;
    try {
      const body = await resp.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON error body — keep generic message */
    }
    throw new ApiError(detail, resp.status);
  }

  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export interface ApplicationFilters {
  status?: Status | "";
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

  // Sync
  sync: (full = false) =>
    request<SyncResult>(`/sync?full=${full}`, { method: "POST" }),

  // Applications
  stats: () => request<Stats>("/applications/stats"),
  applications: (filters: ApplicationFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.set("status", filters.status);
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
