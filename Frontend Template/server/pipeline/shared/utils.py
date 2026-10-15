"""Slim stand-in for backend/pipeline/shared/utils.py: only `sanitize_headline` (copied verbatim)."""
from __future__ import annotations

import html
import re

_FUNDING_ALERT_PREFIX_RE = re.compile(
    r"^\{\s*Funding\s+Alert\s*\}\s*",
    re.IGNORECASE,
)

_LITERAL_UNICODE_ESCAPE_RE = re.compile(r"\\u([0-9a-fA-F]{4})")


def normalize_space(text: str) -> str:
    return " ".join(text.split())


def decode_literal_unicode_escapes(text: str) -> str:
    if not text or "\\u" not in text:
        return text
    return _LITERAL_UNICODE_ESCAPE_RE.sub(lambda m: chr(int(m.group(1), 16)), text)


def sanitize_headline(headline: str | None) -> str:
    if not headline:
        return ""
    text = normalize_space(str(headline).strip())
    text = decode_literal_unicode_escapes(text)
    text = html.unescape(text)
    text = normalize_space(text)
    return _FUNDING_ALERT_PREFIX_RE.sub("", text).strip()
