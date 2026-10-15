"""Supported newsletter template IDs (vertical centered only)."""

from __future__ import annotations

DEFAULT_TEMPLATE_ID = "vertical-centered-layout"

SUPPORTED_TEMPLATE_IDS: frozenset[str] = frozenset(
    {
        "vertical-centered-layout",
    }
)


def normalize_template_id(template_id: str) -> str:
    """Resolve a template id to a supported centered renderer id."""
    tid = (template_id or "").strip()
    if tid in SUPPORTED_TEMPLATE_IDS:
        return tid
    return DEFAULT_TEMPLATE_ID


