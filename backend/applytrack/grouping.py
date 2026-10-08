"""Group emails into applications and label them with the employer.

Grouping: one application per **job** (see :func:`job_group_key`). Threads about
the same job — e.g. a confirmation and a later rejection sent as separate
conversations — are merged via the job reference number (``335649BR``) or
company + role; different jobs at the same company stay separate (20 UBS
applications stay 20). Without a reference or role, a thread is its own
application.

Company labelling (see :func:`extract_company`): a real company domain wins
(``@ubs.com`` -> UBS), because display names there are often systems, departments
or people. On applicant-tracking platforms (Workday, Brassring, Umantis, Oracle,
…) the domain is never the employer, so we use the display name, the subject
("… at Schroders"), or the subdomain/local part. The LLM's company wins when
present.
"""

from __future__ import annotations

import re

from .classify.base import Classification

_FREEMAIL = {
    "gmail", "outlook", "yahoo", "gmx", "hotmail", "icloud", "proton",
    "protonmail", "bluewin", "hispeed", "sunrise",
}
_NON_ALNUM = re.compile(r"[^a-z0-9]+")

# Applicant-tracking-system domains: the registrable domain is the ATS vendor,
# not the employer. The employer is in the subdomain or local part / display name.
_ATS_DOMAINS = {
    "myworkday.com", "workday.com", "brassring.com", "umantis.com",
    "oraclecloud.com", "oracle.com", "ocs.oraclecloud.com", "successfactors.com",
    "successfactors.eu", "smartrecruiters.com", "greenhouse.io", "lever.co",
    "taleo.net", "icims.com", "refline.ch", "softgarden.io", "softgarden.de",
    "prescreen.io", "avature.net", "eightfold.ai", "personio.de", "ostendis.com",
    "jacando.com", "guidecom.de", "concludis.de", "rexx-systems.com",
}

# Generic subdomain labels that precede (or stand in for) the employer label.
_SUB_MARKERS = {
    "hcm", "careers", "career", "jobs", "job", "recruiting", "recruitment",
    "apply", "talent", "erecruiting", "e-recruiting", "customers", "candidate",
    "mail", "email", "workflow", "no-reply", "noreply", "smtp", "ocs",
    "ocs.oraclecloud", "eu-frankfurt-1", "us2", "cloud",
}

# Generic local-part tokens that are never the employer.
_GENERIC_LOCAL = {
    "fa", "sender", "mail", "smtp", "noreply", "no-reply", "donotreply",
    "do-not-reply", "system", "notification", "notifications", "info", "hr",
    "ghr", "careers", "career", "jobs", "recruiting", "recruitment", "no",
    "reply", "do", "not", "donot",
}

# Role / system words stripped from a sender display name to reveal the employer.
_ROLE_TOKENS = {
    "recruiting", "recruitment", "careers", "career", "talent", "acquisition",
    "hr", "human", "resources", "team", "hiring", "jobs", "job", "system",
    "myhr", "workday", "noreply", "no-reply", "donotreply", "do-not-reply",
    "recruiter", "people", "bewerbermanagement", "bewerbermanagment",
    "talentacquisition", "rekrutierung", "global", "interview", "scheduling",
    "personalabteilung", "personaldienst", "connect",
}

# Tokens that mark a display name as a company (so it is NOT a personal name).
_COMPANY_MARKERS = {
    "ag", "gmbh", "sa", "plc", "inc", "ltd", "llc", "co", "co.", "bank",
    "banque", "capital", "partners", "group", "holding", "asset", "management",
    "managers", "&", "re", "privatbank", "kantonalbank", "services", "advisors",
    "insurance", "financial", "consulting", "international",
}


def normalise(text: str | None) -> str:
    """Lowercase, transliterate umlauts, collapse to a slug fragment."""
    if not text:
        return ""
    text = text.lower().strip()
    text = text.replace("ß", "ss").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    return _NON_ALNUM.sub("-", text).strip("-")


def _parse_header(header: str) -> tuple[str, str]:
    """Split a ``From``/``To`` header into (display_name, email)."""
    header = (header or "").strip()
    m = re.match(r'^"?([^"<]*?)"?\s*<([^>]+)>$', header)
    if m:
        return m.group(1).strip(), m.group(2).strip().lower()
    if "@" in header:
        return "", header.strip().strip("<>").lower()
    return header.strip(), ""


def _titlecase(token: str) -> str:
    token = re.sub(r"[_\-.]+", " ", token).strip()
    out: list[str] = []
    for w in token.split():
        if w.isalpha() and len(w) <= 4:
            out.append(w.upper())  # short bank acronyms: ubs→UBS, zkb→ZKB, ubp→UBP
        elif w.isupper() and len(w) <= 5:
            out.append(w)  # keep an existing acronym
        else:
            out.append(w.capitalize())
    return " ".join(out)


def _looks_like_person(tokens: list[str]) -> bool:
    """Heuristic: 2-3 name-like words with no company marker → a person.

    Accepts "Anna Muster" and the corporate "MUSTER Anna" style (an
    all-caps surname), as long as at least one word is Title-case.
    """
    if not (2 <= len(tokens) <= 3):
        return False
    if any(t.lower().strip(".") in _COMPANY_MARKERS for t in tokens):
        return False
    title = r"[A-ZÄÖÜ][a-zäöüéè]+"
    if not all(re.fullmatch(rf"{title}|[A-ZÄÖÜ]{{2,}}", t) for t in tokens):
        return False
    return any(re.fullmatch(title, t) for t in tokens)


def _clean_display(name: str) -> tuple[str, bool]:
    """Strip role/system words from a display name. Returns (cleaned, removed_any)."""
    removed = False
    kept: list[str] = []
    for raw in re.split(r"[\s,]+", name):
        tok = raw.strip(" -|")
        if not tok:
            continue
        if tok.lower() in _ROLE_TOKENS:
            removed = True
            continue
        kept.append(tok)
    return " ".join(kept).strip(" -|.&"), removed


# Pretty names for domain / local-part labels that don't title-case well.
_COMPANY_ALIASES = {
    "ubs": "UBS", "ubp": "UBP", "zkb": "ZKB", "lukb": "LUKB", "sgkb": "SGKB",
    "swissre": "Swiss Re", "swissreservices": "Swiss Re",
    "juliusbaer": "Julius Bär", "maerki-baumann": "Maerki Baumann",
    "dz-privatbank": "DZ PRIVATBANK", "lgtcp": "LGT Capital Partners", "lgt": "LGT",
    "jsafrasarasin": "J. Safra Sarasin", "swisslife": "Swiss Life", "pimco": "PIMCO",
    "vontobel": "Vontobel", "rothschildandco": "Rothschild & Co",
    "jpmorgan": "JPMorgan Chase & Co", "jpmchase": "JPMorgan Chase & Co",
    "schroders": "Schroders", "credit-suisse": "Credit Suisse",
}


def _label_name(label: str) -> str:
    """Alias or title-cased rendering of a single domain/local-part label."""
    return _COMPANY_ALIASES.get(label.lower()) or _titlecase(label)


def _split_email(email: str) -> tuple[str, list[str], bool, bool] | None:
    """Return (local, domain_labels, is_ats, is_freemail), or None if unparsable."""
    if "@" not in email:
        return None
    local, domain = email.split("@", 1)
    labels = domain.split(".")
    if len(labels) < 2:
        return None
    registrable = ".".join(labels[-2:])
    is_ats = (
        registrable in _ATS_DOMAINS
        or ".".join(labels[-3:]) in _ATS_DOMAINS
        or any(d in domain for d in _ATS_DOMAINS)
    )
    return local, labels, is_ats, labels[-2] in _FREEMAIL


def _company_from_ats_email(local: str, labels: list[str]) -> str | None:
    """Employer on an ATS address: a non-generic subdomain, else the local part."""
    for cand in reversed(labels[:-2]):
        if cand not in _SUB_MARKERS and not cand.replace("-", "").isdigit():
            return _label_name(cand)
    parts = [p for p in re.split(r"[_\-.]+", local) if p and p.lower() not in _GENERIC_LOCAL]
    return _label_name(parts[0]) if parts else None


# "<Role> at <Company>" at the end of an English subject.
_SUBJECT_AT_RE = re.compile(r"\sat\s+([A-Z][\w&.\-]*(?:\s+[A-Z][\w&.\-]*){0,3})\s*$")


def company_from_subject(subject: str | None) -> str | None:
    """Employer named in the subject, e.g. 'Relationship Manager - 1172 at Schroders'."""
    if not subject:
        return None
    m = _SUBJECT_AT_RE.search(subject.strip())
    return m.group(1).strip(" .") if m else None


def extract_company(header: str, subject: str | None = None) -> str | None:
    """Best-effort employer name from a ``From``/``To`` header (and subject).

    Order of trust:
    1. A real company domain (``@ubs.com``, ``@ubp.ch``) — the display name there
       is often a system, department or person ("SH-UBS-Interview-Scheduling",
       "MUSTER Anna"), so the domain wins.
    2. On ATS platforms / free-mail: the display name, unless it's a person.
    3. The subject ("… at Schroders").
    4. The ATS subdomain or local part (``swisslife@myworkday.com``).
    """
    display, email = _parse_header(header)
    parts = _split_email(email)

    if parts:
        local, labels, is_ats, is_freemail = parts
        if not is_ats and not is_freemail:
            return _label_name(labels[-2])

    cleaned, removed = _clean_display(display) if display else ("", False)
    is_person = bool(cleaned) and not removed and _looks_like_person(cleaned.split())
    if cleaned and not is_person and "@" not in cleaned:
        return cleaned

    from_subject = company_from_subject(subject)
    if from_subject:
        return from_subject

    if parts and parts[2]:  # ATS
        return _company_from_ats_email(parts[0], parts[1])
    return None  # free-mail personal address → not a company


# --- Role / position extraction from the subject line --------------------------

# Markers after which the role usually follows (longest/most specific first).
_ROLE_MARKERS = [
    r"ihre bewerbung\s*[|:]\s*",  # "Ihre Bewerbung | <role>"
    r"deine bewerbung\s*[|:]\s*",
    r"ihre bewerbung als\s+",
    r"deine bewerbung als\s+",
    r"meine bewerbung als\s+",
    r"bewerbung um die stelle als\s+",
    r"bewerbung um die stelle\s+",
    r"bewerbung als\s+",
    r"ihre bewerbung bei\s+\S+\s+",  # "… bei UBS <role>" — company word consumed
    r"deine bewerbung bei\s+\S+\s+",
    r"bewerbung bei\s+\S+\s+",
    r"your application for\s+",
    r"application for the position of\s+",
    r"application for\s+",
    r"interview invitation for\s+",
    r"invitation for\s+",
    r"your application:\s+",
    r"application:\s+",
]

# Role mentioned in the body: "…deine Bewerbung als <role>." / "…for the role of <role>."
# Captures up to the end of the sentence or a trailing "bei/at <Company>".
_BODY_ROLE_RE = re.compile(
    r"(?:bewerbung als|bewerbung f(?:ü|ue)r die (?:stelle|position)(?: als)?|"
    r"for the (?:role|position) of|application for the (?:role|position) of|"
    r"application for)\s+(.{3,120}?)(?:[.!?\n]|\s+(?:bei|at|with)\s+[A-ZÄÖÜ]|$)",
    re.IGNORECASE,
)

# Subjects that are pure acknowledgments / noise → no role.
_NO_ROLE_RE = re.compile(
    r"^(thank you|herzlichen dank|vielen dank|besten dank|confirmation of|"
    r"ihre bewerber|your job application status|registration|reminder|complete)",
    re.IGNORECASE,
)


def _clean_role(role: str, company: str | None) -> str | None:
    # Cut at "… bei <company>" / "… at <company>".
    role = re.split(r"\s+(?:bei|at)\s+[A-ZÄÖÜ]", role)[0]
    # Cut trailing application/confirmation suffixes after a dash/pipe.
    role = re.split(
        r"\s*[-–—|]\s*(?:application|your application|bewerbung|confirmation|"
        r"status|job\s*number|ref)",
        role,
        flags=re.IGNORECASE,
    )[0]
    # Drop reference numbers: (337922BR), (Job number: …), (1172).
    role = re.sub(r"\(\s*(?:job\s*number[^)]*|ref[^)]*|\d+[a-z]*)\s*\)", "", role, flags=re.IGNORECASE)
    # Drop workload percentages and gender tags.
    role = re.sub(r"\(?\s*\d{2,3}\s*[-–]\s*\d{2,3}\s*%\s*\)?", "", role)
    role = re.sub(r"\(?\s*\d{2,3}\s*%\s*\)?", "", role)
    role = re.sub(
        r"\(?\s*\b[mwfdax](?:\s*/\s*[mwfdax])+\b\s*[;)]?", "", role, flags=re.IGNORECASE
    )
    role = re.sub(r"\(\s*all genders\s*\)", "", role, flags=re.IGNORECASE)
    # Strip a leading company name left in the role ("UBS Client Account Manager").
    if company and role.lower().startswith(company.lower()):
        role = role[len(company):]
    # Drop standalone long reference codes and tidy up.
    role = re.sub(r"\b\d{4,}[a-z]{0,3}\b", "", role, flags=re.IGNORECASE)
    role = re.sub(r"\s{2,}", " ", role).strip(" -–—|:,.;")
    # Close a parenthesis the subject cut off: "Analyst (12 months" → "Analyst (12 months)".
    if role.count("(") > role.count(")"):
        role += ")"

    if len(role) < 3 or role.lower() in _GENERIC_ROLES:
        return None
    return role


# Words that end up as a "role" in subjects like "Re: UBP Interview" but aren't one.
_GENERIC_ROLES = {
    "application", "bewerbung", "online application", "interview", "termin",
    "feedback", "update", "gespraech", "gespräch", "absage", "zusage",
}


def extract_role(subject: str, company: str | None = None) -> str | None:
    """Best-effort job title from an email subject. Returns None if unclear."""
    if not subject:
        return None
    s = re.sub(r"^(?:(?:re|aw|wg|fwd|fw)\s*:\s*)+", "", subject.strip(), flags=re.IGNORECASE).strip()
    if _NO_ROLE_RE.match(s):
        return None

    low = s.lower()
    for marker in _ROLE_MARKERS:
        m = re.search(marker, low)
        if m:
            return _clean_role(s[m.end():], company)

    # No "application" marker: try "<role> at <Company>" or "<Company> - <role>".
    at = re.search(r"\s+at\s+[A-ZÄÖÜ]", s)
    if at:
        return _clean_role(s[: at.start()], company)
    if company and low.startswith(company.lower()):
        return _clean_role(s[len(company):].lstrip(" -–—|:"), company)
    return None


def extract_role_from_body(body: str, company: str | None = None) -> str | None:
    """Fallback: job title mentioned in the email text (first match)."""
    if not body:
        return None
    m = _BODY_ROLE_RE.search(body)
    return _clean_role(m.group(1), company) if m else None


def counterparty_address(direction: str, sender: str, recipient: str) -> str:
    """The company-side address: recipient for our outbound mail, else sender."""
    return recipient if direction == "sent" else sender


def is_ignored_sender(sender: str, recipient: str) -> bool:
    """True if either party matches a configured ignore pattern (e.g. a recruiter).

    Checks both sender and recipient so a thread is ignored whether the agency
    wrote to us or we replied to them.
    """
    from .config import get_settings

    patterns = get_settings().ignored_list
    if not patterns:
        return False
    haystack = f"{sender}\n{recipient}".lower()
    return any(p in haystack for p in patterns)


def resolve_company(
    classification: Classification, company_address: str, subject: str | None = None
) -> str:
    """Best company string: LLM classification, else header/subject-derived, else Unknown."""
    return (
        (classification.company or "").strip()
        or extract_company(company_address, subject)
        or "Unknown"
    )


def thread_group_key(thread_id: str) -> str:
    """Fallback key: one application per Gmail thread."""
    return f"thread:{thread_id}"


# Job reference numbers: "(335649BR)", "Job number: 210722077", "340891BR".
_REF_RE = re.compile(
    r"\((\d{5,}[a-z]{0,3})\)|job\s*number:?\s*(\d{5,})|\b(\d{6,}br)\b",
    re.IGNORECASE,
)


def extract_job_ref(text: str | None) -> str | None:
    """First job reference number in a subject/body, upper-cased."""
    m = _REF_RE.search(text or "")
    if not m:
        return None
    return next(g for g in m.groups() if g).upper()


def job_group_key(
    company: str | None, role: str | None, ref: str | None, thread_id: str
) -> str:
    """Key that merges threads about the *same job*, keeping different jobs apart.

    Confirmation and rejection often arrive in separate Gmail threads; they
    belong to one application. Prefer the job reference number, then the role;
    without either (or without a known company) fall back to the thread.
    """
    company_slug = normalise(company)
    if company_slug and company_slug != "unknown":
        if ref:
            return f"job:{company_slug}:ref:{ref.lower()}"
        if role:
            return f"job:{company_slug}:role:{normalise(role)}"
    return thread_group_key(thread_id)


# Backwards-compatible alias (kept for any external callers/tests).
def build_group_key(company: str, role: str | None) -> str:
    company_slug = normalise(company) or "unknown"
    role_slug = normalise(role)
    return f"{company_slug}::{role_slug}" if role_slug else company_slug
