"""EMAIL LAYOUT FOR NEWSLETTERS WITH 2 NEWS PER SECTOR  (team edits go here).

`render_body` returns the <tr> rows between the masthead and the footer. It receives
`sectors_raw` ({"Healthcare": [article, ...], ...}) already trimmed so the largest sector has
2 article(s). The masthead, footer, <head> and page shell come from the production renderer
and are shared by every layout.

Email HTML rules: tables + inline styles only (no Tailwind/flex/grid), 345 / 650 / 900px shells,
mobile rules live in `_responsive_email_style_tag` / `_centered_email_style_tag` in
pipeline/shared/email_renderer.py (shared; edit with care).

Starts identical to production (`_render_vertical`). To port a finished design to the main app,
see "Porting an email layout" in the README.
"""
from __future__ import annotations

from pipeline.shared.email_renderer import _render_vertical


def render_body(sectors_raw: dict) -> str:
    return _render_vertical(sectors_raw)
