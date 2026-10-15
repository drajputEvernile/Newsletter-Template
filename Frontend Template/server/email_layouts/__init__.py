"""Per-count email layouts (news per sector -> email body), plugged into the production renderer.

`pipeline/shared/*` stays an unmodified copy of the backend. This package registers one extra
template id per count (`layout-1` ... `layout-5`) in the production renderer's dispatch table at
import time, then `render_email` renders with the layout that matches the largest sector.
"""
from __future__ import annotations

from typing import Any

from pipeline.shared import email_renderer, newsletter_templates
from pipeline.shared.email_renderer import render_newsletter_email

from . import layout_1, layout_2, layout_3, layout_4, layout_5

EMAIL_LAYOUTS = {
    1: layout_1.render_body,
    2: layout_2.render_body,
    3: layout_3.render_body,
    4: layout_4.render_body,
    5: layout_5.render_body,
}


def _template_id(count: int) -> str:
    return f"layout-{count}"


for _count, _fn in EMAIL_LAYOUTS.items():
    email_renderer._RENDERERS[_template_id(_count)] = _fn
newsletter_templates.SUPPORTED_TEMPLATE_IDS = frozenset(
    {*newsletter_templates.SUPPORTED_TEMPLATE_IDS, *map(_template_id, EMAIL_LAYOUTS)}
)


def render_email(payload: dict[str, Any]) -> str:
    """Render *payload* with the layout for its largest sector (same rule as the React preview)."""
    largest = max((len(v) for v in payload.get("sectors", {}).values()), default=1)
    count = min(max(largest, 1), max(EMAIL_LAYOUTS))
    return render_newsletter_email(payload, template_id=_template_id(count))
