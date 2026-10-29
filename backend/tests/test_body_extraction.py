"""Mail text extraction from Gmail's MIME tree."""

from __future__ import annotations

import base64

from applytrack.gmail.sync import _extract_body


def _data(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")


def test_html_nested_next_to_image_attachments():
    # Workday / Julius Baer shape: mixed → related → html, plus inline images.
    payload = {
        "mimeType": "multipart/mixed",
        "parts": [
            {"mimeType": "multipart/related", "parts": [
                {"mimeType": "text/html",
                 "body": {"data": _data("<p>After careful consideration we will not proceed.</p>")}},
                {"mimeType": "image/png", "filename": "logo.png", "body": {"attachmentId": "x"}},
            ]},
            {"mimeType": "image/jpeg", "filename": "banner.jpg", "body": {"attachmentId": "y"}},
        ],
    }
    assert "we will not proceed" in _extract_body(payload)


def test_plain_text_nested_in_alternative_wins_over_html():
    payload = {
        "mimeType": "multipart/mixed",
        "parts": [{"mimeType": "multipart/alternative", "parts": [
            {"mimeType": "text/plain", "body": {"data": _data("Nach eingehender Pruefung leider")}},
            {"mimeType": "text/html", "body": {"data": _data("<b>html</b>")}},
        ]}],
    }
    assert _extract_body(payload) == "Nach eingehender Pruefung leider"


def test_attached_text_file_is_not_the_body():
    payload = {
        "mimeType": "multipart/mixed",
        "parts": [
            {"mimeType": "text/plain", "filename": "cv.txt", "body": {"data": _data("attachment")}},
            {"mimeType": "text/html", "body": {"data": _data("<p>Real text</p>")}},
        ],
    }
    assert "Real text" in _extract_body(payload)
