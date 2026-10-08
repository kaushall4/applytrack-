// Mirror of the backend Pydantic schemas (kept in sync by hand).

export type Intent =
  | "application_sent"
  | "application_received"
  | "interview_invite"
  | "next_round"
  | "rejection"
  | "offer"
  | "info_request"
  | "not_application_related";

export type Status =
  | "application_sent"
  | "application_received"
  | "info_request"
  | "interview_invite"
  | "next_round"
  | "rejection"
  | "offer"
  | "ghosted";

export type Language = "de" | "en";

export interface EmailItem {
  id: number;
  gmail_id: string;
  thread_id: string;
  direction: "sent" | "received";
  sender: string;
  subject: string;
  body_snippet: string;
  received_at: string;
  intent: Intent;
  effective_intent: Intent;
  confidence: number;
  language: Language;
  classifier_source: string;
  manual_override: Intent | null;
}

export interface Application {
  id: number;
  company: string;
  role: string | null;
  first_applied_at: string | null;
  last_event_at: string | null;
  current_status: Status;
  email_count: number;
  language: Language;
}

export interface ApplicationDetail extends Application {
  emails: EmailItem[];
}

export interface Stats {
  total_applied: number;
  awaiting_response: number;
  interviews: number;
  offers: number;
  rejections: number;
  ghosted: number;
}

export interface AccountStatus {
  connected: boolean;
  /** An account was connected, but Google no longer accepts its token. */
  session_expired?: boolean;
  email_address: string | null;
  last_synced_at: string | null;
}

export interface SyncResult {
  new_emails: number;
  classified: number;
  applications: number;
  message: string;
}
