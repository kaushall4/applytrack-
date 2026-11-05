import { motion } from "framer-motion";
import { useMemo } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { useI18n } from "../i18n";
import { ALL_STATUSES, STATUS_META } from "../lib/status";
import type { Application, Status } from "../lib/types";

export function StatusDonut({ applications }: { applications: Application[] }) {
  const { t } = useI18n();

  const data = useMemo(() => {
    const counts = new Map<Status, number>();
    for (const a of applications) {
      counts.set(a.current_status, (counts.get(a.current_status) ?? 0) + 1);
    }
    return ALL_STATUSES.filter((s) => counts.get(s))
      .map((s) => ({ status: s, name: t.status[s], value: counts.get(s) as number, hex: STATUS_META[s].hex }));
  }, [applications, t]);

  const total = applications.length;
  if (total === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="rounded-2xl border border-border bg-surface p-5 shadow-card"
    >
      <h2 className="mb-4 text-xl font-medium">{t.chart.title}</h2>
      <div className="flex items-center gap-4">
        <div className="relative h-36 w-36 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                innerRadius={54}
                outerRadius={68}
                paddingAngle={1.5}
                stroke="none"
                startAngle={90}
                endAngle={-270}
                isAnimationActive={false}
              >
                {data.map((d) => (
                  <Cell key={d.status} fill={d.hex} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  borderRadius: 12,
                  border: "1px solid rgb(var(--border))",
                  background: "rgb(var(--surface))",
                  color: "rgb(var(--fg))",
                  fontSize: 12,
                  boxShadow: "0 24px 60px -24px rgb(var(--shadow-tint) / 0.45)",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 grid place-items-center">
            <div className="text-center">
              <div className="font-display text-3xl font-medium leading-none tabular-nums">{total}</div>
              <div className="eyebrow mt-1 text-[10px]">{t.chart.total}</div>
            </div>
          </div>
        </div>

        <ul className="min-w-0 flex-1 space-y-2">
          {data.map((d) => (
            <li key={d.status} className="flex items-center gap-2 text-xs">
              <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: d.hex }} />
              <span className="min-w-0 text-muted">{d.name}</span>
              <span className="ml-auto font-medium tabular-nums">{d.value}</span>
            </li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
}
