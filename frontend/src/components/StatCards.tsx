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
import type { Stats } from "../lib/types";

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
  { key: "total_applied", labelKey: "total", icon: Briefcase, tint: "text-brand bg-brand/10" },
  { key: "awaiting_response", labelKey: "awaiting", icon: Hourglass, tint: "text-slate-500 bg-slate-500/10" },
  { key: "interviews", labelKey: "interviews", icon: CalendarCheck, tint: "text-indigo-500 bg-indigo-500/10" },
  { key: "offers", labelKey: "offers", icon: Award, tint: "text-emerald-500 bg-emerald-500/10" },
  { key: "rejections", labelKey: "rejections", icon: XCircle, tint: "text-rose-500 bg-rose-500/10" },
  { key: "ghosted", labelKey: "ghosted", icon: Ghost, tint: "text-amber-500 bg-amber-500/10" },
];

function StatCard({ def, value, label, index }: { def: Omit<StatDef, "value">; value: number; label: string; index: number }) {
  const display = useCountUp(value);
  const Icon = def.icon;
  const [iconTint, iconBg] = def.tint.split(" ");
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.35, ease: "easeOut" }}
      whileHover={{ y: -3 }}
      className="rounded-2xl border border-border bg-surface p-4 shadow-card"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted">{label}</span>
        <span className={`grid h-7 w-7 place-items-center rounded-lg ${iconBg}`}>
          <Icon className={`h-4 w-4 ${iconTint}`} />
        </span>
      </div>
      <div className="mt-2 text-3xl font-bold tabular-nums tracking-tight">{display}</div>
    </motion.div>
  );
}

export function StatCards({ stats }: { stats: Stats }) {
  const labels = useStatLabels();
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
      {DEFS.map((def, i) => (
        <StatCard key={def.key} def={def} index={i} value={stats[def.key]} label={labels[def.labelKey]} />
      ))}
    </div>
  );
}
