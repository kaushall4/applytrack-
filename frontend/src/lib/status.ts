import type { LucideIcon } from "lucide-react";
import {
  Award,
  CalendarCheck,
  CheckCircle2,
  Clock,
  FileQuestion,
  Inbox,
  Layers,
  Send,
  XCircle,
} from "lucide-react";

import type { Intent, Status } from "./types";

/**
 * Semantic status meta: badge classes (solid-ish tint), a hex for charts/nodes,
 * and an icon. Colors encode meaning and stay consistent across light/dark:
 *   applied=neutral, received=slate, interview=indigo, next_round=violet,
 *   offer=green, rejection=muted red, ghosted=amber, info_request=teal.
 */
interface StatusMeta {
  badge: string;
  dot: string;
  hex: string;
  icon: LucideIcon;
}

export const STATUS_META: Record<Status, StatusMeta> = {
  application_sent: {
    badge: "bg-slate-100 text-slate-600 ring-slate-200 dark:bg-slate-500/15 dark:text-slate-300 dark:ring-slate-400/20",
    dot: "bg-slate-400",
    hex: "#94a3b8",
    icon: Send,
  },
  application_received: {
    badge: "bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-500/15 dark:text-slate-200 dark:ring-slate-400/20",
    dot: "bg-slate-500",
    hex: "#64748b",
    icon: Inbox,
  },
  info_request: {
    badge: "bg-teal-100 text-teal-700 ring-teal-200 dark:bg-teal-500/15 dark:text-teal-300 dark:ring-teal-400/20",
    dot: "bg-teal-500",
    hex: "#14b8a6",
    icon: FileQuestion,
  },
  interview_invite: {
    badge: "bg-indigo-100 text-indigo-700 ring-indigo-200 dark:bg-indigo-500/15 dark:text-indigo-300 dark:ring-indigo-400/20",
    dot: "bg-indigo-500",
    hex: "#6366f1",
    icon: CalendarCheck,
  },
  next_round: {
    badge: "bg-violet-100 text-violet-700 ring-violet-200 dark:bg-violet-500/15 dark:text-violet-300 dark:ring-violet-400/20",
    dot: "bg-violet-500",
    hex: "#8b5cf6",
    icon: Layers,
  },
  offer: {
    badge: "bg-emerald-100 text-emerald-700 ring-emerald-200 dark:bg-emerald-500/15 dark:text-emerald-300 dark:ring-emerald-400/20",
    dot: "bg-emerald-500",
    hex: "#10b981",
    icon: Award,
  },
  rejection: {
    badge: "bg-rose-100 text-rose-600 ring-rose-200 dark:bg-rose-500/12 dark:text-rose-300 dark:ring-rose-400/20",
    dot: "bg-rose-500",
    hex: "#f43f5e",
    icon: XCircle,
  },
  ghosted: {
    badge: "bg-amber-100 text-amber-700 ring-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:ring-amber-400/20",
    dot: "bg-amber-500",
    hex: "#f59e0b",
    icon: Clock,
  },
};

/** Intents reuse the status palette; not-application-related is muted. */
export const INTENT_META: Record<Intent, StatusMeta> = {
  application_sent: STATUS_META.application_sent,
  application_received: STATUS_META.application_received,
  interview_invite: STATUS_META.interview_invite,
  next_round: STATUS_META.next_round,
  rejection: STATUS_META.rejection,
  offer: STATUS_META.offer,
  info_request: STATUS_META.info_request,
  not_application_related: {
    badge: "bg-slate-100 text-slate-500 ring-slate-200 dark:bg-slate-600/15 dark:text-slate-400 dark:ring-slate-500/20",
    dot: "bg-slate-300",
    hex: "#cbd5e1",
    icon: CheckCircle2,
  },
};

export const ALL_STATUSES: Status[] = [
  "application_sent",
  "application_received",
  "info_request",
  "interview_invite",
  "next_round",
  "offer",
  "rejection",
  "ghosted",
];

export const ALL_INTENTS: Intent[] = [
  "application_sent",
  "application_received",
  "interview_invite",
  "next_round",
  "info_request",
  "offer",
  "rejection",
  "not_application_related",
];
