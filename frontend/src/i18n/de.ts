import type { Dict } from "./en";

// Swiss German conventions: no "ß" (always "ss").
export const de: Dict = {
  appName: "ApplyTrack",
  tagline: "Bewerbungs-Tracker",

  nav: {
    dashboard: "Übersicht",
    review: "Zu prüfen",
    noise: "Gefiltert",
  },

  header: {
    connected: "Verbunden",
    notConnected: "Kein Konto verbunden",
    connect: "Konto verbinden",
    disconnect: "Trennen",
    sync: "Jetzt synchronisieren",
    syncing: "Synchronisiere…",
    lastSynced: "Zuletzt synchronisiert",
    toggleTheme: "Design wechseln",
    sessionExpired: "Sitzung abgelaufen",
    reconnect: "Erneut verbinden",
    reconnecting: "Warte auf Google…",
  },

  session: {
    title: "Deine Gmail-Verbindung ist abgelaufen",
    body: "Google verlangt von Zeit zu Zeit eine neue Anmeldung. Einmal erneut verbinden, dann läuft die Synchronisierung weiter — deine Daten bleiben erhalten.",
    hint: "Es öffnet sich ein Google-Fenster — mit demselben Konto bestätigen.",
  },

  stats: {
    total: "Bewerbungen gesamt",
    awaiting: "Warten auf Antwort",
    interviews: "Gespräche",
    offers: "Angebote",
    rejections: "Absagen",
    ghosted: "Ohne Rückmeldung",
  },

  chart: {
    title: "Statusverteilung",
    total: "Gesamt",
  },

  table: {
    company: "Unternehmen",
    role: "Position",
    status: "Status",
    applied: "Beworben",
    lastActivity: "Letzte Aktivität",
    emails: "E-Mails",
    language: "Sprache",
    filterStatus: "Status",
    filterLanguage: "Sprache",
    all: "Alle",
    search: "Unternehmen oder Position suchen…",
    sortBy: "Sortieren nach",
    noResults: "Keine Bewerbungen passen zu diesen Filtern.",
  },

  detail: {
    timeline: "E-Mail-Verlauf",
    intent: "Absicht",
    confidence: "Sicherheit",
    sent: "Gesendet",
    received: "Erhalten",
    via: "via",
    close: "Schliessen",
    correct: "Korrigieren",
  },

  review: {
    title: "Zu prüfen",
    subtitle: "Klassifizierungen mit geringer Sicherheit, die du korrigieren kannst.",
    empty: "Nichts zu prüfen — alle Klassifizierungen sind sicher.",
    save: "Speichern",
    saved: "Gespeichert",
    clear: "Korrektur entfernen",
    lowConfidence: "geringe Sicherheit",
  },

  noise: {
    title: "Gefilterte E-Mails",
    subtitle:
      "Newsletter, Job-Alerts und Marketing — gespeichert, aber von den Bewerbungen ausgeschlossen.",
    empty: "Noch keine gefilterten E-Mails.",
  },

  connect: {
    title: "Gmail-Konto verbinden",
    description:
      "Gib die Gmail-Adresse ein, die du für die Stellensuche nutzt. Den lesenden Zugriff autorisierst du im Google-Zustimmungsdialog. Die eingegebene Adresse erklärt nur die Absicht — der Zugriff wird durch die Anmeldung gewährt.",
    placeholder: "du@gmail.com",
    submit: "Mit Google verbinden",
    connecting: "Öffne Google…",
    note: "Nur lesender Zugriff. ApplyTrack verändert oder löscht deine E-Mails nie.",
  },

  empty: {
    title: "Noch keine Bewerbungen",
    body: "Verbinde dein Gmail-Konto und synchronisiere, oder lade die Beispieldaten, um die Übersicht zu erkunden.",
  },

  errors: {
    generic: "Etwas ist schiefgelaufen. Bitte versuche es erneut.",
    load: "Daten konnten nicht geladen werden.",
  },

  toast: {
    syncDone: "Synchronisierung abgeschlossen",
    disconnected: "Konto getrennt",
    reconnected: "Wieder verbunden — du bist angemeldet",
    sessionExpired: "Deine Gmail-Verbindung ist abgelaufen. Bitte erneut verbinden.",
    overrideSaved: "Klassifizierung aktualisiert",
  },

  status: {
    application_sent: "Beworben",
    application_received: "Bestätigt",
    info_request: "Infos angefragt",
    interview_invite: "Gespräch",
    next_round: "Nächste Runde",
    rejection: "Absage",
    offer: "Angebot",
    ghosted: "Ohne Rückmeldung",
  },

  intent: {
    application_sent: "Bewerbung versendet",
    application_received: "Eingangsbestätigung",
    interview_invite: "Einladung zum Gespräch",
    next_round: "Nächste Runde",
    rejection: "Absage",
    offer: "Angebot",
    info_request: "Info-Anfrage",
    not_application_related: "Nicht bewerbungsbezogen",
  },

  lang: { de: "DE", en: "EN" },
};
