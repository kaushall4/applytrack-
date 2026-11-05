import { motion } from "framer-motion";
import {
  Award,
  Briefcase,
  CalendarCheck,
  Ghost,
  Hourglass,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useState } from "react";

import { useI18n } from "../i18n";
import type { Stats, StatusFilter } from "../lib/types";
import { cn } from "../lib/utils";

interface StatDef {
  key: keyof Stats;
  labelKey: keyof ReturnType<typeof useStatLabels>;
  icon: LucideIcon;
  tint: string;
  value: string;
}

function useStatLabels() {
  const { t } = useI18n();
  return {
    total: t.stats.total,
    awaiting: t.stats.awaiting,
    interviews: t.stats.interviews,
    offers: t.stats.offers,
    rejections: t.stats.rejections,
    ghosted: t.stats.ghosted,
  };
}

function useCountUp(target: number, duration = 750): number {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(target * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return val;
}

const DEFS: Omit<StatDef, "value">[] = [
  { key: "total_applied", labelKey: "total", icon: Briefcase, tint: "text-brand" },
  { key: "awaiting_response", labelKey: "awaiting", icon: Hourglass, tint: "text-[#8E8069] dark:text-[#CFC5B4]" },
  { key: "interviews", labelKey: "interviews", icon: CalendarCheck, tint: "text-[#2F5597] dark:text-[#A4BCEC]" },
  { key: "offers", labelKey: "offers", icon: Award, tint: "text-[#1F7F5C] dark:text-[#7FD3AE]" },
  { key: "rejections", labelKey: "rejections", icon: XCircle, tint: "text-[#A63D4D] dark:text-[#E8A3AC]" },
  { key: "ghosted", labelKey: "ghosted", icon: Ghost, tint: "text-[#C08A2E] dark:text-[#E5C07A]" },
];

function StatCard({
  def,
  value,
  label,
  index,
  onClick,
  active = false,
  hint,
}: {
  def: Omit<StatDef, "value">;
  value: number;
  label: string;
  index: number;
  onClick?: () => void;
  active?: boolean;
  hint?: string;
}) {
  const display = useCountUp(value);
  const Icon = def.icon;
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.35, ease: "easeOut" }}
      whileHover={{ y: -3 }}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => (e.key === "Enter" || e.key === " ") && onClick() : undefined}
      title={hint}
      className={cn(
        "rounded-2xl border bg-surface p-4 shadow-card sm:p-5",
        onClick && "cursor-pointer transition-[border-color,box-shadow] hover:border-brand/50 hover:shadow-lift",
        active ? "border-brand ring-1 ring-brand" : "border-border",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="eyebrow min-h-[2.75em] leading-snug">{label}</span>
        <Icon className={`h-4 w-4 shrink-0 ${def.tint}`} strokeWidth={1.5} />
      </div>
      <div className="font-display mt-3 text-[2.75rem] font-medium leading-none tabular-nums">
        {display}
      </div>
    </motion.div>
  );
}

// The table filter each card opens.
const CARD_FILTER: Record<keyof Stats, StatusFilter> = {
  total_applied: "",
  awaiting_response: "awaiting",
  interviews: "interviewed",
  offers: "offer",
  rejections: "rejection",
  ghosted: "ghosted",
};

export function StatCards({
  stats,
  activeFilter,
  onSelect,
}: {
  stats: Stats;
  activeFilter?: StatusFilter;
  /** Clicking a card filters the table to the applications it counts. */
  onSelect?: (filter: StatusFilter) => void;
}) {
  const labels = useStatLabels();
  const { t } = useI18n();
  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-6">
      {DEFS.map((def, i) => {
        const filter = CARD_FILTER[def.key];
        return (
          <StatCard
            key={def.key}
            def={def}
            index={i}
            value={stats[def.key]}
            label={labels[def.labelKey]}
            onClick={onSelect ? () => onSelect(filter) : undefined}
            active={activeFilter !== undefined && activeFilter === filter && filter !== ""}
            hint={def.key === "interviews" ? t.table.interviewedHint : undefined}
          />
        );
      })}
    </div>
  );
}
