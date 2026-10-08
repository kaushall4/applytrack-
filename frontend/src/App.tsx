import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useEffect, useState } from "react";
import { Route, Routes, useLocation } from "react-router-dom";

import { api, ApiError } from "./api/client";
import { ConnectAccount } from "./components/ConnectAccount";
import { Header } from "./components/layout/Header";
import { SessionExpiredBanner } from "./components/SessionExpiredBanner";
import { useToast } from "./components/ui/Toast";
import { useI18n } from "./i18n";
import type { AccountStatus } from "./lib/types";
import { Dashboard } from "./pages/Dashboard";
import { Noise } from "./pages/Noise";
import { Review } from "./pages/Review";

function Page({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}

export function App() {
  const { t } = useI18n();
  const { notify } = useToast();
  const location = useLocation();

  const [account, setAccount] = useState<AccountStatus | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [connectOpen, setConnectOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const loadAccount = useCallback(() => {
    api
      .accountStatus()
      .then(setAccount)
      .catch(() => setAccount({ connected: false, email_address: null, last_synced_at: null }));
  }, []);

  useEffect(loadAccount, [loadAccount]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await api.sync();
      notify(`${t.toast.syncDone} · ${result.message}`, "success");
      loadAccount();
      setRefreshKey((k) => k + 1);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        // Google no longer accepts the stored token → show the reconnect state.
        notify(t.toast.sessionExpired, "error");
        loadAccount();
      } else {
        notify(err instanceof Error ? err.message : t.errors.generic, "error");
      }
    } finally {
      setSyncing(false);
    }
  };

  // One-click reconnect with the remembered address (Google pre-selects it).
  const handleReconnect = async () => {
    if (!account?.email_address) {
      setConnectOpen(true);
      return;
    }
    setReconnecting(true);
    try {
      const acc = await api.connect(account.email_address);
      setAccount(acc);
      notify(t.toast.reconnected, "success");
    } catch (err) {
      notify(err instanceof Error ? err.message : t.errors.generic, "error");
    } finally {
      setReconnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await api.disconnect();
      notify(t.toast.disconnected, "info");
      loadAccount();
    } catch (err) {
      notify(err instanceof Error ? err.message : t.errors.generic, "error");
    }
  };

  return (
    <div className="relative min-h-full">
      {/* Ambient gradient blobs */}
      <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div
          className="absolute -left-24 -top-32 h-96 w-96 rounded-full opacity-20 blur-3xl"
          style={{ background: "rgb(var(--glow-1))" }}
        />
        <div
          className="absolute -right-24 top-40 h-96 w-96 rounded-full opacity-10 blur-3xl"
          style={{ background: "rgb(var(--glow-2))" }}
        />
      </div>

      <Header
        account={account}
        syncing={syncing}
        reconnecting={reconnecting}
        onSync={handleSync}
        onConnect={() => setConnectOpen(true)}
        onReconnect={handleReconnect}
        onDisconnect={handleDisconnect}
      />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        {account?.session_expired && (
          <SessionExpiredBanner
            email={account.email_address}
            busy={reconnecting}
            onReconnect={handleReconnect}
          />
        )}
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route
              path="/"
              element={
                <Page>
                  <Dashboard key={refreshKey} onConnect={() => setConnectOpen(true)} />
                </Page>
              }
            />
            <Route path="/review" element={<Page><Review key={refreshKey} /></Page>} />
            <Route path="/noise" element={<Page><Noise key={refreshKey} /></Page>} />
          </Routes>
        </AnimatePresence>
      </main>

      <ConnectAccount
        open={connectOpen}
        defaultEmail={account?.email_address}
        onClose={() => setConnectOpen(false)}
        onConnected={(acc) => {
          setAccount(acc);
          notify(`${t.header.connected}: ${acc.email_address}`, "success");
        }}
      />
    </div>
  );
}
