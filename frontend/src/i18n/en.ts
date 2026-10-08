import type { Intent, Status } from "../lib/types";

export const en = {
  appName: "ApplyTrack",
  tagline: "Job application tracker",

  nav: {
    dashboard: "Dashboard",
    review: "Needs review",
    noise: "Filtered",
  },

  header: {
    connected: "Connected",
    notConnected: "No account connected",
    connect: "Connect account",
    disconnect: "Disconnect",
    sync: "Sync now",
    syncing: "Syncing…",
    lastSynced: "Last synced",
    toggleTheme: "Toggle theme",
    sessionExpired: "Session expired",
    reconnect: "Reconnect",
    reconnecting: "Waiting for Google…",
  },

  session: {
    title: "Your Gmail connection has expired",
    body: "Google asks for a fresh sign-in from time to time. Reconnect once and syncing continues — your data is unaffected.",
    hint: "A Google window will open — confirm with the same account.",
  },

  stats: {
    total: "Total applications",
    awaiting: "Awaiting response",
    interviews: "Interviews",
    offers: "Offers",
    rejections: "Rejections",
    ghosted: "Ghosted",
  },

  chart: {
    title: "Status distribution",
    total: "Total",
  },

  table: {
    company: "Company",
    role: "Role",
    status: "Status",
    applied: "Applied",
    lastActivity: "Last activity",
    emails: "Emails",
    language: "Language",
    filterStatus: "Status",
    filterLanguage: "Language",
    all: "All",
    search: "Search company or role…",
    sortBy: "Sort by",
    noResults: "No applications match these filters.",
  },

  detail: {
    timeline: "Email timeline",
    intent: "Intent",
    confidence: "Confidence",
    sent: "Sent",
    received: "Received",
    via: "via",
    close: "Close",
    correct: "Correct",
  },

  review: {
    title: "Needs review",
    subtitle: "Low-confidence classifications you can correct.",
    empty: "Nothing to review — every classification is confident.",
    save: "Save",
    saved: "Saved",
    clear: "Clear override",
    lowConfidence: "low confidence",
  },

  noise: {
    title: "Filtered mail",
    subtitle:
      "Newsletters, job alerts, and marketing — kept, but excluded from applications.",
    empty: "No filtered mail yet.",
  },

  connect: {
    title: "Connect a Gmail account",
    description:
      "Enter the Gmail address you use for job hunting. You'll authorize read-only access in Google's consent screen. The typed address only declares intent — access is granted by signing in.",
    placeholder: "you@gmail.com",
    submit: "Connect with Google",
    connecting: "Opening Google…",
    note: "Read-only access. ApplyTrack never modifies or deletes your mail.",
  },

  empty: {
    title: "No applications yet",
    body: "Connect your Gmail account and run a sync, or load the sample data to explore the dashboard.",
  },

  errors: {
    generic: "Something went wrong. Please try again.",
    load: "Could not load data.",
  },

  toast: {
    syncDone: "Sync complete",
    disconnected: "Account disconnected",
    reconnected: "Reconnected — you're signed in again",
    sessionExpired: "Your Gmail connection has expired. Please reconnect.",
    overrideSaved: "Classification updated",
  },

  status: {
    application_sent: "Applied",
    application_received: "Acknowledged",
    info_request: "Info requested",
    interview_invite: "Interview",
    next_round: "Next round",
    rejection: "Rejected",
    offer: "Offer",
    ghosted: "Ghosted",
  } satisfies Record<Status, string>,

  intent: {
    application_sent: "Application sent",
    application_received: "Acknowledgment",
    interview_invite: "Interview invite",
    next_round: "Next round",
    rejection: "Rejection",
    offer: "Offer",
    info_request: "Info request",
    not_application_related: "Not application-related",
  } satisfies Record<Intent, string>,

  lang: { de: "DE", en: "EN" },
};

export type Dict = typeof en;
