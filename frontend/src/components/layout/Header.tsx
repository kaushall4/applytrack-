import { motion } from "framer-motion";
import { KeyRound, LayoutDashboard, ListChecks, MailX, Plug, RefreshCw, Unplug } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";

import { useI18n } from "../../i18n";
import { formatDateTime, senderName } from "../../lib/format";
import type { AccountStatus } from "../../lib/types";
import { cn } from "../../lib/utils";
import { LangToggle } from "./LangToggle";
import { ThemeToggle } from "./ThemeToggle";

interface HeaderProps {
  account: AccountStatus | null;
  syncing: boolean;
  reconnecting: boolean;
  onSync: () => void;
  onConnect: () => void;
  onReconnect: () => void;
  onDisconnect: () => void;
}

const NAV = [
  { to: "/", end: true, key: "dashboard", icon: LayoutDashboard },
  { to: "/review", end: false, key: "review", icon: ListChecks },
  { to: "/noise", end: false, key: "noise", icon: MailX },
] as const;

function Brand() {
  const { t } = useI18n();
  return (
    <div className="flex items-center gap-2.5">
      <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand to-violet-400 text-brand-fg shadow-sm">
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={2.6}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <div className="leading-tight">
        <div className="text-sm font-bold tracking-tight">{t.appName}</div>
        <div className="text-[11px] text-muted">{t.tagline}</div>
      </div>
    </div>
  );
}

function NavTabs() {
  const { t } = useI18n();
  const { pathname } = useLocation();

  const isActive = (to: string, end: boolean) =>
    end ? pathname === to : pathname.startsWith(to);

  return (
    <nav className="flex items-center gap-1 rounded-xl bg-surface-2/70 p-1">
      {NAV.map(({ to, end, key, icon: Icon }) => {
        const active = isActive(to, end);
        return (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={cn(
              "relative flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
              active ? "text-fg" : "text-muted hover:text-fg",
            )}
          >
            {active && (
              <motion.span
                layoutId="nav-pill"
                className="absolute inset-0 rounded-lg bg-surface shadow-sm ring-1 ring-border"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            )}
            <Icon className="relative z-10 h-4 w-4" />
            <span className="relative z-10">{t.nav[key]}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}

export function Header({
  account,
  syncing,
  reconnecting,
  onSync,
  onConnect,
  onReconnect,
  onDisconnect,
}: HeaderProps) {
  const { t } = useI18n();
  const connected = account?.connected ?? false;
  const expired = account?.session_expired ?? false;
  const address = account?.email_address ?? "";
  const initial = (senderName(address) || address || "?").charAt(0).toUpperCase();

  return (
    <header className="sticky top-0 z-30 border-b border-border glass">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-3 sm:px-6">
        <Brand />

        <div className="ml-2 hidden sm:block">
          <NavTabs />
        </div>

        <div className="ml-auto flex items-center gap-2">
          {connected ? (
            <div className="hidden items-center gap-2 rounded-xl border border-border bg-surface/60 py-1 pl-1 pr-2.5 md:flex">
              <div className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-brand to-violet-400 text-xs font-bold text-brand-fg">
                {initial}
              </div>
              <span className="max-w-[170px] truncate text-xs font-medium" title={address}>
                {address}
              </span>
              <button
                onClick={onDisconnect}
                title={t.header.disconnect}
                className="text-muted transition-colors hover:text-rose-500"
              >
                <Unplug className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : expired ? (
            <button
              onClick={onReconnect}
              disabled={reconnecting}
              title={account?.email_address ?? undefined}
              className="flex items-center gap-1.5 rounded-xl border border-amber-500/40 bg-amber-50 px-3 py-1.5 text-sm font-medium text-amber-800 transition-colors hover:bg-amber-100 disabled:opacity-60 dark:bg-amber-500/10 dark:text-amber-200 dark:hover:bg-amber-500/20"
            >
              <KeyRound className="h-4 w-4" />
              <span className="hidden sm:inline">{t.header.sessionExpired} ·</span>
              {reconnecting ? t.header.reconnecting : t.header.reconnect}
            </button>
          ) : (
            <button
              onClick={onConnect}
              className="flex items-center gap-1.5 rounded-xl bg-brand px-3 py-1.5 text-sm font-medium text-brand-fg shadow-sm transition-opacity hover:opacity-90"
            >
              <Plug className="h-4 w-4" />
              {t.header.connect}
            </button>
          )}

          {connected && (
            <button
              onClick={onSync}
              disabled={syncing}
              title={
                account?.last_synced_at
                  ? `${t.header.lastSynced}: ${formatDateTime(account.last_synced_at, "en")}`
                  : undefined
              }
              className="flex items-center gap-1.5 rounded-xl border border-border bg-surface px-3 py-1.5 text-sm font-medium transition-colors hover:bg-surface-2 disabled:opacity-60"
            >
              <RefreshCw className={cn("h-4 w-4", syncing && "animate-spin")} />
              <span className="hidden lg:inline">{syncing ? t.header.syncing : t.header.sync}</span>
            </button>
          )}

          <LangToggle />
          <ThemeToggle />
        </div>
      </div>

      {/* Mobile nav */}
      <div className="border-t border-border px-4 py-2 sm:hidden">
        <NavTabs />
      </div>
    </header>
  );
}
