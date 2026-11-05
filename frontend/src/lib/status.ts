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
 *   applied=stone, received=taupe, interview=sapphire, next_round=amethyst,
 *   offer=emerald, rejection=garnet, ghosted=ochre, info_request=teal.
 */
interface StatusMeta {
  badge: string;
  dot: string;
  hex: string;
  icon: LucideIcon;
}

export const STATUS_META: Record<Status, StatusMeta> = {
  application_sent: {
    badge: "bg-[#B9AE9B]/10 text-[#6F6556] ring-[#B9AE9B]/25 dark:bg-[#B9AE9B]/15 dark:text-[#CFC5B4] dark:ring-[#CFC5B4]/25",
    dot: "bg-[#B9AE9B]",
    hex: "#B9AE9B",
    icon: Send,
  },
  application_received: {
    badge: "bg-[#8E8069]/10 text-[#5F5444] ring-[#8E8069]/25 dark:bg-[#8E8069]/15 dark:text-[#D8CDBB] dark:ring-[#D8CDBB]/25",
    dot: "bg-[#8E8069]",
    hex: "#8E8069",
    icon: Inbox,
  },
  info_request: {
    badge: "bg-[#2F8079]/10 text-[#1F6A65] ring-[#2F8079]/25 dark:bg-[#2F8079]/15 dark:text-[#7FCBC3] dark:ring-[#7FCBC3]/25",
    dot: "bg-[#2F8079]",
    hex: "#2F8079",
    icon: FileQuestion,
  },
  interview_invite: {
    badge: "bg-[#2F5597]/10 text-[#24437F] ring-[#2F5597]/25 dark:bg-[#2F5597]/15 dark:text-[#A4BCEC] dark:ring-[#A4BCEC]/25",
    dot: "bg-[#2F5597]",
    hex: "#2F5597",
    icon: CalendarCheck,
  },
  next_round: {
    badge: "bg-[#74478F]/10 text-[#5F3679] ring-[#74478F]/25 dark:bg-[#74478F]/15 dark:text-[#CDA9E4] dark:ring-[#CDA9E4]/25",
    dot: "bg-[#74478F]",
    hex: "#74478F",
    icon: Layers,
  },
  offer: {
    badge: "bg-[#1F7F5C]/10 text-[#176A4D] ring-[#1F7F5C]/25 dark:bg-[#1F7F5C]/15 dark:text-[#7FD3AE] dark:ring-[#7FD3AE]/25",
    dot: "bg-[#1F7F5C]",
    hex: "#1F7F5C",
    icon: Award,
  },
  rejection: {
    badge: "bg-[#A63D4D]/10 text-[#8E2F3D] ring-[#A63D4D]/25 dark:bg-[#A63D4D]/15 dark:text-[#E8A3AC] dark:ring-[#E8A3AC]/25",
    dot: "bg-[#A63D4D]",
    hex: "#A63D4D",
    icon: XCircle,
  },
  ghosted: {
    badge: "bg-[#C08A2E]/10 text-[#855C12] ring-[#C08A2E]/25 dark:bg-[#C08A2E]/15 dark:text-[#E5C07A] dark:ring-[#E5C07A]/25",
    dot: "bg-[#C08A2E]",
    hex: "#C08A2E",
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
    badge: "bg-[#B9AE9B]/10 text-[#7A7060] ring-[#B9AE9B]/25 dark:bg-[#B9AE9B]/10 dark:text-[#AC9F8C] dark:ring-[#B9AE9B]/20",
    dot: "bg-[#D6CDBD]",
    hex: "#D6CDBD",
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
