"""Fragment-based intent detection — the core of the offline classifier.

Design principles (see project spec):

* Match short, characteristic **substrings** (fragments), never whole sentences
  or long exact phrases. A single fragment like ``"leider"`` or
  ``"nicht erfolgreich"`` is enough to detect a rejection, regardless of how the
  rest of the sentence is worded.
* Matching is case-insensitive and **umlaut-folded**: ``ä/ö/ü/ß`` and their
  ``ae/oe/ue/ss`` transliterations both match. Fragments are stored in folded
  (ae/oe/ue/ss) form; the text is folded the same way before matching.
* Substring match (not word-boundary) so inflections share a stem fragment:
  ``"beruecksichtig"`` matches *beruecksichtigen / beruecksichtigt /
  beruecksichtigung*.
* Every email is checked against **all** intent fragment lists; the result is
  decided by **precedence**, not by the first fragment found. Terminal/stronger
  signals win — so a polite "thank you" can never override a rejection hidden in
  a compliment sandwich.
"""

from __future__ import annotations

import re

from .base import Intent

# Precedence on the email level: stronger/terminal intents win when fragments
# of several intents are present in the same email.
EMAIL_PRECEDENCE: list[Intent] = [
    Intent.OFFER,
    Intent.REJECTION,
    Intent.NEXT_ROUND,
    Intent.INTERVIEW_INVITE,
    Intent.INFO_REQUEST,
    Intent.APPLICATION_RECEIVED,
    Intent.APPLICATION_SENT,
]

# Fragments are deliberately short and stored umlaut-folded (ae/oe/ue/ss).
# application_sent is intentionally absent — it is decided by mail direction
# (outbound), not by fragments.
FRAGMENTS: dict[Intent, list[str]] = {
    Intent.REJECTION: [
        # DE
        "leider", "nicht erfolgreich", "diesmal nicht", "nicht weiter",
        "nicht beruecksichtig", "nicht weiterverfolg", "anderweitig",
        "andere kandidat", "anderen kandidat", "andere bewerber",
        "fuer jemanden anderen", "umfassender erfuell", "nicht entsprech",
        "absage", "haben wir uns entschied", "entschieden, ", "abzusagen",
        "nicht zum zug", "bedauerlicherweise", "nicht in die engere wahl",
        "nicht weiter in betracht",
        # EN
        "unfortunately", "we regret", "regret to inform", "not be proceeding",
        "will not proceed", "not moving forward", "other candidates",
        "another candidate", "decided to move forward with", "unable to offer",
        "not be moving ahead", "were not selected", "will not be progressing",
        "not have the best fit", "not the best fit", "not the right fit",
        "unable to consider", "not be moving forward", "will not be moving",
        "not meet the eligibility", "do not meet the", "does not meet the",
        "have not been successful", "has not been successful", "were unsuccessful",
        "was unsuccessful",
        # Farewells that close a process ("wünschen dir weiterhin viel Erfolg").
        "weiterhin viel erfolg", "beruflichen zukunft", "beruflichen werdegang alles gute",
        "every success in your", "best of luck in your", "success in your future",
    ],
    Intent.OFFER: [
        # DE
        "freuen uns, ihnen die stelle", "stelle anbieten", "arbeitsvertrag",
        "vertrag im anhang", "angebot unterbreiten", "zusage",
        # EN
        "pleased to offer", "offer you the position", "job offer",
        "employment contract", "we would like to offer",
    ],
    Intent.NEXT_ROUND: [
        # DE
        "zweite runde", "zweiten runde", "naechste runde", "folgegespraech",
        "fallstudie", "assessment", "weitere runde", "zweites gespraech",
        "weiteres gespraech", "weiteren gespraech", "weiteren interview",
        "weiteres interview", "finale gespraech", "finalen gespraech",
        "zweitrunden", "im prozess weitermachen", "im prozess weiter",
        "referenz einholen", "referenzen einholen",
        # EN
        "second round", "next round", "final round", "case study",
        "assessment center", "move to the next stage", "second interview",
        "next interview", "further interview", "final interview", "reference check",
    ],
    # Only unambiguous invitations. Vaguer cues ("next steps", "availability")
    # also appear in plain acknowledgments — see WEAK_INTERVIEW_FRAGMENTS.
    Intent.INTERVIEW_INVITE: [
        # DE
        "einladung zum gespraech", "einladung zu einem gespraech",
        "einladung zum interview", "gespraech einladen", "interview einladen",
        "zu einem gespraech", "zu einem vorstellungsgespraech", "vorstellungsgespraech",
        "persoenlichen gespraech", "persoenliches gespraech", "gespraechstermin",
        "interviewtermin", "terminvorschlag", "telefoninterview",
        "telefonisches interview", "videointerview", "video-interview", "erstgespraech",
        "kennenlernen", "kennenzulernen", "termin vereinbaren",
        "ankunft an der rezeption", "bei ihrer ankunft", "bei deiner ankunft",
        "ein gespraech mit",
        # EN
        "invite you to", "invite you for", "schedule a call", "schedule an interview",
        "schedule your interview", "your interview", "interview is scheduled",
        "phone screen", "first interview", "interview invitation", "invitation to interview",
        "like to meet you", "want to meet you", "would like to meet",
        "in-person interview", "in person interview", "interview availability",
        "available time slots", "book a time",
    ],
    Intent.INFO_REQUEST: [
        # DE (Sie + Du)
        "benoetigen wir noch", "bitte senden sie uns", "bitte sende uns",
        "nachreichen", "arbeitszeugnis", "notenauszug", "fehlende unterlagen",
        "koennten sie uns", "koenntest du uns", "darf ich dich bitten",
        "darf ich sie bitten", "zuzusenden", "zusenden",
        # EN
        "could you please send", "we still need", "missing documents",
        "please provide", "send us your", "please send", "could you send",
    ],
    Intent.APPLICATION_RECEIVED: [
        # DE (Sie + Du)
        "dank fuer ihre bewerbung", "dank fuer deine bewerbung",
        "danke fuer ihre bewerbung", "danke fuer deine bewerbung",
        "bewerbung erhalten", "unterlagen erhalten", "eingang ihrer bewerbung",
        "eingang deiner bewerbung", "eingang ihrer unterlagen",
        "eingang deiner unterlagen", "bestaetigen den eingang", "hiermit den eingang",
        "den eingang ihrer", "den eingang deiner", "empfangsbestaetigung",
        "eingangsbestaetigung", "in bearbeitung",
        "melden uns", "pruefen ihre unterlagen", "pruefen deine unterlagen",
        "pruefen wir ihre", "pruefen wir deine", "sorgfaeltig pruefen",
        # EN
        "thank you for your application", "thank you for applying",
        "received your application", "received your documents",
        "application is being reviewed", "we will be in touch", "currently reviewing",
        "get back to you",
    ],
}

# Ambiguous interview cues: an invitation *may* say "next steps" or ask for
# availability, but acknowledgments routinely promise "we'll contact you about
# the next steps". These only count when no other application signal matched,
# and then with low confidence (→ lands in "Needs review").
WEAK_INTERVIEW_FRAGMENTS: list[str] = [
    "naechster schritt", "naechsten schritt", "verfuegbarkeit",
    "next step", "your availability",
]

_WS_RE = re.compile(r"\s+")


def fold(text: str) -> str:
    """Lowercase, transliterate umlauts/ß, and collapse whitespace.

    Folding both the text and the fragments to the ae/oe/ue/ss form means either
    spelling matches. Whitespace is collapsed so fragments spanning a line break
    still match.
    """
    if not text:
        return ""
    text = text.lower()
    text = (
        text.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    return _WS_RE.sub(" ", text)


# Acknowledgments often describe a *possible* interview ("Falls Ihr Profil passt,
# laden wir Sie zu einem Gespräch ein", "If selected, we will schedule your
# interview"). Interview / next-round cues inside such conditional sentences
# don't count.
_CONDITIONAL_RE = re.compile(
    r"\b(falls|sollte|sollten|sofern|fuer den fall|wenn ihr profil|wenn dein profil|"
    r"if|should|in case|once we|whether)\b"
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?\n])\s+|\n")
_CONDITION_SENSITIVE = {Intent.INTERVIEW_INVITE, Intent.NEXT_ROUND}

# "Interview" / "Gespräch" in the *subject* of a received mail is a strong cue
# ("UBP Interview", "Get ready for your interview").
_SUBJECT_INTERVIEW_RE = re.compile(r"\binterview|gespraech\b|vorstellungsgespraech")


# Rejections often end with a perk: "we are pleased to offer you free access to
# mentoring", "...a place in our talent community". Offer cues in such sentences
# are never a job offer.
_OFFER_NOISE_RE = re.compile(
    r"mentor|free access|talent (pool|community|network)|job alert|newsletter|webinar|"
    r"career (journey|support|resources)|discount|kostenlos|talentpool|karriere-?newsletter"
)
# Polite phrasing that is only an offer when nothing in the mail says no.
_GENERIC_OFFER_FRAGMENTS = {"pleased to offer", "we would like to offer"}


def _offer_sentences(folded: str) -> str:
    return " ".join(
        s for s in _SENTENCE_SPLIT_RE.split(folded) if s and not _OFFER_NOISE_RE.search(s)
    )


def _unconditional_sentences(folded: str) -> str:
    return " ".join(
        s for s in _SENTENCE_SPLIT_RE.split(folded) if s and not _CONDITIONAL_RE.search(s)
    )


def matched_fragments(text: str) -> dict[Intent, list[str]]:
    """Return, per intent, the list of fragments found in ``text``."""
    folded = fold(text)
    unconditional = _unconditional_sentences(folded)
    offer_text = _offer_sentences(folded)
    hits: dict[Intent, list[str]] = {}
    for intent, fragments in FRAGMENTS.items():
        if intent in _CONDITION_SENSITIVE:
            haystack = unconditional
        elif intent is Intent.OFFER:
            haystack = offer_text
        else:
            haystack = folded
        found = [f for f in fragments if f in haystack]
        if found:
            hits[intent] = found
    # A real offer never also says no; generic "pleased to offer" next to a
    # rejection is a consolation perk, not a job.
    if Intent.REJECTION in hits and Intent.OFFER in hits:
        specific = [f for f in hits[Intent.OFFER] if f not in _GENERIC_OFFER_FRAGMENTS]
        if specific:
            hits[Intent.OFFER] = specific
        else:
            del hits[Intent.OFFER]
    return hits


def classify_by_precedence(
    text: str, subject: str | None = None
) -> tuple[Intent, list[str], bool]:
    """Pick the strongest matching intent.

    Returns ``(intent, matched_fragments, weak)``. ``weak`` is True when the
    result rests only on ambiguous interview cues. If nothing matches, returns
    ``(NOT_APPLICATION_RELATED, [], False)``.
    """
    hits = matched_fragments(text)
    if subject and _SUBJECT_INTERVIEW_RE.search(fold(subject)):
        hits.setdefault(Intent.INTERVIEW_INVITE, []).append("subject: interview")
    for intent in EMAIL_PRECEDENCE:
        if intent in hits:
            return intent, hits[intent], False

    # Nothing unambiguous matched — fall back to weak interview cues.
    unconditional = _unconditional_sentences(fold(text))
    weak = [f for f in WEAK_INTERVIEW_FRAGMENTS if f in unconditional]
    if weak:
        return Intent.INTERVIEW_INVITE, weak, True
    return Intent.NOT_APPLICATION_RELATED, [], False
