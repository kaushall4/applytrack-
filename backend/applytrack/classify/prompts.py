"""System prompt, few-shot examples, and user-message builder for the LLM."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are an email-intent classifier for a job-application tracker. The user runs \
a dedicated Gmail account used ONLY for job hunting and applies in BOTH German \
and English. Treat German and English with EQUAL weight — never assume English.

Classify the email into exactly ONE intent:
- application_sent — the user sent a job application.
- application_received — an automated acknowledgment that an application was received.
- interview_invite — invited to an interview / phone screen / assessment / first round.
- next_round — advancing to a further stage beyond the first interview.
- rejection — declined / not moving forward.
- offer — a job offer is being extended.
- info_request — they ask the user for more documents, availability, or details.
- not_application_related — newsletters, job alerts, marketing, spam.

DECISIVE RULE — tone never changes the result. Polite, warm, or complimentary \
wording does NOT change the classification when the text also contains a decision \
signal. What matters is the FINAL statement about the outcome of the application, \
not the tone. A "compliment sandwich" that praises the candidate and then declines \
is a REJECTION, even if it opens with "thank you for your application" or lavish \
praise.

PRECEDENCE — if signals for several intents appear in one email, the stronger / \
terminal one wins, in this order:
offer > rejection > next_round > interview_invite > info_request > \
application_received > application_sent.
So as soon as a rejection signal is present (e.g. "leider", "nicht erfolgreich", \
"we have decided to move forward with other candidates"), it is a rejection — even \
if "vielen Dank für Ihre Bewerbung" or praise is also present. Thanks/praise must \
NEVER override a rejection.

Also extract the company and the role/title if present (else null), and the \
email's language ("de" or "en").

Respond with STRICT JSON ONLY, no prose, no markdown fences, exactly:
{"intent": "<one intent>", "confidence": <0.0-1.0>, "company": <string|null>, \
"role": <string|null>, "language": "de"|"en", "reasoning": "<short, one sentence>"}\
"""


# Few-shot examples steer the model on the hard cases: the compliment-sandwich
# rejection, a pure acknowledgment, and a clear interview invite. Sent as a
# user/assistant message pair sequence before the real email.
FEW_SHOT_MESSAGES: list[dict[str, str]] = [
    {
        "role": "user",
        "content": (
            "From: karriere@beispiel-bank.ch\n"
            "Subject: Ihre Bewerbung\n\n"
            "Body:\nVielen Dank für Ihre Bewerbung. Ihr Profil und Ihre Qualifikationen "
            "haben uns sehr beeindruckt. Dennoch müssen wir Ihnen leider mitteilen, dass "
            "Ihre Bewerbung diesmal nicht erfolgreich war."
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{"intent": "rejection", "confidence": 0.96, "company": "Beispiel Bank", '
            '"role": null, "language": "de", "reasoning": "Despite the praise, the final '
            'statement declines the application."}'
        ),
    },
    {
        "role": "user",
        "content": (
            "From: no-reply@example.com\n"
            "Subject: Eingang Ihrer Bewerbung\n\n"
            "Body:\nVielen Dank für Ihre Bewerbung. Wir haben Ihre Unterlagen erhalten "
            "und melden uns in Kürze bei Ihnen."
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{"intent": "application_received", "confidence": 0.92, "company": null, '
            '"role": null, "language": "de", "reasoning": "Pure acknowledgment of receipt, '
            'no decision."}'
        ),
    },
    {
        "role": "user",
        "content": (
            "From: talent@northwind.com\n"
            "Subject: Next steps\n\n"
            "Body:\nWe were impressed by your application and would like to invite you to "
            "a first interview. Could you let us know your availability next week?"
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{"intent": "interview_invite", "confidence": 0.94, "company": "Northwind", '
            '"role": null, "language": "en", "reasoning": "Explicit invitation to a first '
            'interview."}'
        ),
    },
]


def build_user_message(sender: str, subject: str, body: str) -> str:
    """Assemble the per-email user message. Body is truncated to keep cost down."""
    snippet = (body or "").strip()
    if len(snippet) > 4000:
        snippet = snippet[:4000] + " […]"
    return f"From: {sender}\nSubject: {subject}\n\nBody:\n{snippet}"
