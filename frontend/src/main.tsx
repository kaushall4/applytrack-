import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";
import { capturePairingKey } from "./api/client";
import { ToastProvider } from "./components/ui/Toast";
import { I18nProvider } from "./i18n";
import "./index.css";
import { ThemeProvider } from "./lib/theme";

// Installable app: register the service worker in production builds. Browsers
// only allow this on https or localhost; elsewhere the app still works normally.
if (import.meta.env.PROD && "serviceWorker" in navigator && window.isSecureContext) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      /* not installable here — the app keeps working without it */
    });
  });
}

// A phone opening the pairing link (`/?key=…`) keeps the key and drops it from the URL.
capturePairingKey();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider>
      <I18nProvider>
        <ToastProvider>
          <BrowserRouter
            future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
          >
            <App />
          </BrowserRouter>
        </ToastProvider>
      </I18nProvider>
    </ThemeProvider>
  </StrictMode>,
);
