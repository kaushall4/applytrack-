# Privacy Policy / Datenschutzerklärung — ApplyTrack

_Last updated / Zuletzt aktualisiert: 2026-10-08_

[English](#english) · [Deutsch](#deutsch)

---

## English

ApplyTrack is an open-source desktop application that runs entirely on **your own
computer**. There is no ApplyTrack server, no account with us, and no analytics or
tracking of any kind.

### What data ApplyTrack accesses
- With your explicit consent via Google's sign-in screen, ApplyTrack requests
  **read-only** access to the Gmail account you choose (scope
  `https://www.googleapis.com/auth/gmail.readonly`).
- It reads message metadata (sender, recipient, subject, date, thread) and the
  message text in order to recognise job-application emails and their status
  (applied, acknowledged, interview, rejection, offer, …).
- ApplyTrack **never** sends, modifies, labels or deletes email.

### Where data is stored
- Everything is stored **locally on your computer**: a local SQLite database
  (`applytrack.db`) with message metadata and a short text excerpt (max. 500
  characters) per email, and the OAuth token (`token.json`) that keeps you signed in.
- Full email bodies are not stored.
- Nothing is uploaded to the developer or to any server operated by the developer.

### Third parties
- **Google** — to sign in and read your mail through the official Gmail API.
- **Anthropic (optional)** — only if *you* add your own Anthropic API key, email
  sender, subject and text are sent to the Anthropic API to classify them. Without
  a key, classification runs fully offline.
- Your data is never sold, shared for advertising, or used to train models by
  ApplyTrack.

### Google API Services User Data Policy
ApplyTrack's use and transfer of information received from Google APIs adheres to
the [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy),
including the Limited Use requirements.

### Your control
- **Disconnect** in the app (or `applytrack disconnect`) deletes the stored token.
- Revoke access at any time at <https://myaccount.google.com/permissions>.
- Delete `applytrack.db` to remove all locally stored data.

### Contact
Questions: open an issue in this project's GitHub repository.

---

## Deutsch

ApplyTrack ist eine Open-Source-Desktop-Anwendung, die vollständig **auf deinem
eigenen Computer** läuft. Es gibt keinen ApplyTrack-Server, kein Konto bei uns und
keinerlei Analyse- oder Tracking-Funktionen.

### Auf welche Daten ApplyTrack zugreift
- Mit deiner ausdrücklichen Zustimmung über den Google-Anmeldebildschirm erhält
  ApplyTrack **nur lesenden** Zugriff auf das von dir gewählte Gmail-Konto (Scope
  `https://www.googleapis.com/auth/gmail.readonly`).
- Gelesen werden Metadaten (Absender, Empfänger, Betreff, Datum, Konversation) und
  der Text der E-Mails, um Bewerbungs-Mails und ihren Status zu erkennen (beworben,
  bestätigt, Gespräch, Absage, Angebot, …).
- ApplyTrack versendet, verändert, markiert oder löscht **niemals** E-Mails.

### Wo die Daten gespeichert werden
- Alles bleibt **lokal auf deinem Computer**: eine lokale SQLite-Datenbank
  (`applytrack.db`) mit Metadaten und einem kurzen Textauszug (max. 500 Zeichen) pro
  E-Mail sowie das OAuth-Token (`token.json`), damit du angemeldet bleibst.
- Vollständige E-Mail-Texte werden nicht gespeichert.
- Es werden keine Daten an den Entwickler oder an einen vom Entwickler betriebenen
  Server übertragen.

### Drittanbieter
- **Google** — für die Anmeldung und das Lesen deiner Mails über die offizielle
  Gmail-API.
- **Anthropic (optional)** — nur wenn *du* einen eigenen Anthropic-API-Key hinterlegst,
  werden Absender, Betreff und Text zur Klassifizierung an die Anthropic-API
  gesendet. Ohne Key läuft die Klassifizierung komplett offline.
- Deine Daten werden von ApplyTrack nie verkauft, für Werbung weitergegeben oder
  zum Training von Modellen verwendet.

### Google API Services User Data Policy
Die Nutzung und Weitergabe von Informationen, die ApplyTrack über Google-APIs
erhält, entspricht der [Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy),
einschliesslich der Anforderungen zur eingeschränkten Nutzung (Limited Use).

### Deine Kontrolle
- **Trennen** in der App (oder `applytrack disconnect`) löscht das gespeicherte Token.
- Den Zugriff kannst du jederzeit unter <https://myaccount.google.com/permissions>
  widerrufen.
- Lösche `applytrack.db`, um alle lokal gespeicherten Daten zu entfernen.

### Kontakt
Fragen: Bitte ein Issue im GitHub-Repository dieses Projekts eröffnen.
