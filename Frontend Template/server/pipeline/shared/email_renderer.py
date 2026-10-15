"""Generate a self-contained, table-based HTML email from newsletter data.

Each template has its own renderer that mirrors the visual design of the
corresponding web template: colours, card backgrounds, section header styles,
image placement, and column layouts are all faithfully reproduced.

All styles are 100 % inline; layout is table-based so the output renders
identically in Gmail, Apple Mail, Outlook, and Yahoo Mail.

Public API
----------
render_newsletter_email(payload, template_id) -> str
"""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from typing import Any
from urllib.parse import quote

from pipeline.shared.config import getenv_optional
from pipeline.shared.utils import sanitize_headline

# ── Resolved colour tokens (from frontend/src/index.css :root) ────────────────
_BG       = "#f8f9fc"   # --background
_PRIMARY  = "#273249"   # --primary
_ACCENT   = "#d02541"   # --accent
_BORDER   = "#dde0e5"   # --border
_HL_NAVY  = "#e8ebf2"   # --highlight-navy
_HL_MID   = "#eff1f5"   # --highlight-mid
_HL_ICE   = "#f3f4f8"   # --highlight-ice
_CARD     = "#ffffff"   # --card
_FG       = "#1a2236"   # --foreground
_FG_MUTED = "#696e7a"   # --muted-foreground
_MUTED    = "#eef0f5"   # --muted
_CENTERED_PAGE_BG = "#eef4f8"
_CENTERED_SEP = "#c0d2dc"  # footer + internal dividers (vertical centered)
_CENTERED_FOOTER_STRIP_BG = "#e9eff4"  # subtle gray strip behind the legal lines
_FOOTER_LEGAL_TEXT = "#a4abb4"  # deliberately low-contrast: unsubscribe + copyright line
# Centered template: fixed main-block + hero sizes (mobile / tablet / desktop).
_CENTERED_SHELL_W = 900
_CENTERED_SHELL_W_TABLET = 650
_CENTERED_SHELL_W_MOBILE = 345
_CENTERED_HERO_H_TABLET = 160
_CENTERED_HERO_H_MOBILE = 150
_HEADER_DESKTOP_FILE = "Newsletter_Header_Desktop.jpg"
# Source file is 1800×420; layout canvas stays 900×210 (same 30:7 aspect).
_HEADER_DESKTOP_NATURAL_W = 1800
_HEADER_DESKTOP_NATURAL_H = 420
_HEADER_TABLET_FILE = "Newsletter_Header_Tab.jpg"
_HEADER_MOBILE_FILE = "Newsletter_Header_Mobile.jpg"
_CENTERED_HEADER_DESKTOP_DATE = {"x": 730, "y": 133, "w": 140, "h": 36}
_CENTERED_HEADER_REF_W = 900
_CENTERED_HEADER_RIGHT_PAD_DESKTOP = 30


def _centered_header_date_right_pad(art_w: int) -> int:
    return max(0, round(_CENTERED_HEADER_RIGHT_PAD_DESKTOP * art_w / _CENTERED_HEADER_REF_W))


def _centered_header_date_box_right(
    art_w: int, art_h: int, y: float, h: float, box_w: int,
) -> dict[str, float]:
    right_pad = _centered_header_date_right_pad(art_w)
    return {
        "x": round(art_w - right_pad - box_w, 4),
        "y": y,
        "w": box_w,
        "h": h,
    }


_CENTERED_HEADER_TABLET_DATE_Y = 59.3472
# Mobile date: ~2.5px higher than footer midline so it sits tighter in the bar.
_CENTERED_HEADER_MOBILE_DATE_Y = 53.2419
# Date box widths stay tight so the overlay cannot spill into the baked-in logo.
_CENTERED_HEADER_TABLET_DATE = _centered_header_date_box_right(
    650, 160, _CENTERED_HEADER_TABLET_DATE_Y, 20.6528, 240,
)
# right pad ~10px (scaled 12 − 2) nudges the date 2px toward the right edge.
_CENTERED_HEADER_MOBILE_DATE = {
    "x": round(345 - 10 - 165, 4),
    "y": _CENTERED_HEADER_MOBILE_DATE_Y,
    "w": 165,
    "h": 14.259,
}
_CENTERED_HEADER_MOBILE_RIGHT_PAD = 10
_CENTERED_HEADER_MOBILE_DATE_FONT_PX = 7.5
_CENTERED_HEADER_MOBILE_DATE_LINE_PX = 9.5

_CENTERED_HEADER_ART = {
    "desktop": {
        "w": 900,
        "h": 210,
        "file": _HEADER_DESKTOP_FILE,
        "date_box": _CENTERED_HEADER_DESKTOP_DATE,
    },
    "tablet": {
        "w": 650,
        "h": 160,
        "file": _HEADER_TABLET_FILE,
        "date_box": _CENTERED_HEADER_TABLET_DATE,
    },
    "mobile": {
        "w": 345,
        "h": 150,
        "file": _HEADER_MOBILE_FILE,
        "date_box": _CENTERED_HEADER_MOBILE_DATE,
    },
}

_CENTERED_BP_TABLET_MAX = 1023


def _centered_header_date_font_size(art_h: int) -> int:
    if art_h >= 200:
        return 12
    if art_h >= 155:
        return 10
    return 9


def _centered_header_date_cell_style(art_h: int, *, font_weight: int = 400) -> str:
    fs = _centered_header_date_font_size(art_h)
    lh = fs + 2
    return (
        "font-family:Arial,Helvetica,sans-serif;"
        f"text-transform:uppercase;font-weight:{font_weight};letter-spacing:0.02em;"
        f"color:#ffffff !important;mso-color-alt:#ffffff;"
        f"font-size:{fs}px !important;line-height:{lh}px !important;"
        "white-space:nowrap;text-align:right;vertical-align:middle;padding:0 2px 0 0;"
    )


def _centered_header_canvas_style(w: int, h: int, img_src: str) -> str:
    """Canvas TD — never use font-size:0 (Gmail hides all nested date text)."""
    return (
        f"width:100%;max-width:{w}px;height:{h}px;max-height:{h}px;padding:0;margin:0;"
        f"vertical-align:top;background-color:#0a1628;"
        f"background-image:url('{img_src}');background-size:100% 100%;"
        f"background-repeat:no-repeat;background-position:top left;"
    )


def _centered_header_date_overlay_html(
    art: dict[str, Any],
    date_display: str,
    *,
    font_weight: int = 400,
    two_column: bool = False,
) -> str:
    """Date overlay — top spacer + right-aligned date.

    Desktop keeps the nested right-aligned table (frozen). Mobile/tablet use a
    fluid left cell (``width=100%``) that pushes a shrink-wrapped date to the
    right — a fixed-width middle date column was centering in Gmail mobile.
    """
    img_w, img_h = art["w"], art["h"]
    box = art["date_box"]
    x, y, bw, bh = box["x"], box["y"], box["w"], box["h"]
    right_px = max(0, round(img_w - x - bw, 4))
    date_cell = _centered_header_date_cell_style(img_h, font_weight=font_weight)
    date_inner = (
        f'<span style="color:#ffffff !important;mso-color-alt:#ffffff;'
        f'{_centered_header_date_cell_style(img_h, font_weight=font_weight)}text-align:right !important;">'
        f"{_e(date_display)}</span>"
    )
    if two_column:
        # Mobile: keep the explicit right pad (includes +2px right nudge).
        gutter = (
            _CENTERED_HEADER_MOBILE_RIGHT_PAD
            if img_w <= _CENTERED_SHELL_W_MOBILE
            else max(right_px, 12)
        )
        return (
            f'<table role="presentation" width="{img_w}" cellpadding="0" cellspacing="0" border="0" '
            f'style="width:100%;max-width:{img_w}px;height:{img_h}px;border-collapse:collapse;">'
            f'<tr><td class="em-header-spacer-top" height="{y}" colspan="3" '
            f'style="height:{y}px;line-height:{y}px;font-size:0;mso-line-height-rule:exactly">&nbsp;</td></tr>'
            f'<tr>'
            f'<td class="em-header-date-left" width="100%" height="{bh}" '
            f'style="height:{bh}px;font-size:0;line-height:0;mso-line-height-rule:exactly">'
            f"&nbsp;</td>"
            f'<td class="em-header-date-overlay" height="{bh}" align="right" valign="middle" nowrap '
            f'style="height:{bh}px;white-space:nowrap;{date_cell}text-align:right !important;">'
            f"{date_inner}</td>"
            f'<td class="em-header-date-right-pad" width="{gutter}" height="{bh}" '
            f'style="width:{gutter}px;height:{bh}px;font-size:0;line-height:0;mso-line-height-rule:exactly">'
            f"&nbsp;</td>"
            f"</tr></table>"
        )
    return (
        f'<table role="presentation" width="{img_w}" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;max-width:{img_w}px;height:{img_h}px;border-collapse:collapse;table-layout:fixed">'
        f'<tr><td class="em-header-spacer-top" height="{y}" '
        f'style="height:{y}px;line-height:{y}px;font-size:0;mso-line-height-rule:exactly">&nbsp;</td></tr>'
        f'<tr><td class="em-header-date-row" align="right" valign="middle" height="{bh}" '
        f'style="height:{bh}px;padding:0 {right_px}px 0 0;text-align:right;vertical-align:middle">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="right" '
        f'style="width:{bw}px;height:{bh}px;border-collapse:collapse">'
        f'<tr><td class="em-header-date-overlay" width="{bw}" height="{bh}" align="right" valign="middle" '
        f'style="width:{bw}px;height:{bh}px;{date_cell}text-align:right !important;">'
        f"{date_inner}"
        f"</td></tr></table></td></tr></table>"
    )


def _header_centered_desktop_block(date_display: str) -> str:
    """Desktop 900×210 masthead — frozen layout (do not change)."""
    art = _CENTERED_HEADER_ART["desktop"]
    w, h = art["w"], art["h"]
    img_src = _e(_centered_header_img_src("desktop"))
    overlay = _centered_header_date_overlay_html(art, date_display)
    canvas_style = _centered_header_canvas_style(w, h, img_src)
    vml_open = (
        f"<!--[if gte mso 9]><v:rect xmlns:v=\"urn:schemas-microsoft-com:vml\" fill=\"true\" "
        f'stroke="false" style="width:{w}pt;height:{h}pt">'
        f'<v:fill type="frame" src="{img_src}" color="#0a1628"/>'
        f'<v:textbox inset="0,0,0,0" style="mso-fit-text-to-shape:true"><![endif]-->'
    )
    vml_close = "<!--[if gte mso 9]></v:textbox></v:rect><![endif]-->"
    return (
        f'<table role="presentation" class="em-header-desktop" width="{w}" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;max-width:{w}px;border-collapse:collapse;table-layout:fixed">'
        f'<tr><td class="em-header-desktop-canvas" width="{w}" height="{h}" valign="top" align="left" '
        f'background="{img_src}" style="{canvas_style}">'
        f"{vml_open}{overlay}{vml_close}"
        f"</td></tr></table>"
    )


def _centered_header_variant_block(key: str, css_class: str, date_display: str) -> str:
    """Mobile/tablet masthead — per-artboard date box in bottom-right footer bar."""
    art = _CENTERED_HEADER_ART[key]
    w, h = art["w"], art["h"]
    canvas_class = f"em-header-variant-canvas em-header-variant-canvas-{'m' if key == 'mobile' else 't'}"
    img_src = _e(_centered_header_img_src(key))
    # two_column: Outlook Mobile ignores nested align=right and drifts over the logo.
    overlay = _centered_header_date_overlay_html(
        art, date_display, font_weight=500, two_column=True,
    )
    canvas_style = _centered_header_canvas_style(w, h, img_src)
    # No VML here — these blocks only ship in the <!--[if !mso]> branch.
    return (
        f'<table role="presentation" class="em-header-variant {css_class}" width="{w}" cellpadding="0" cellspacing="0" border="0" '
        f'style="width:100%;max-width:{w}px;border-collapse:collapse;table-layout:fixed">'
        f'<tr><td class="{canvas_class}" width="{w}" height="{h}" valign="top" align="left" '
        f'background="{img_src}" style="{canvas_style}">'
        f"{overlay}"
        f"</td></tr></table>"
    )

_DEFAULT_NEWSLETTER_PUBLIC_BASE = "https://newsletter.evernile.com"


def _newsletter_public_base() -> str:
    return (
        getenv_optional("NEWSLETTER_PUBLIC_BASE_URL", "").strip()
        or getenv_optional("APPROVAL_PUBLIC_BASE_URL", "").strip()
        or _DEFAULT_NEWSLETTER_PUBLIC_BASE
    ).rstrip("/")


def _newsletter_asset_url(filename: str, *, env_key: str) -> str:
    override = getenv_optional(env_key, "").strip()
    if override:
        return override
    base = _newsletter_public_base()
    if base:
        return f"{base}/{quote(filename)}"
    return f"/{quote(filename)}"


@lru_cache(maxsize=32)
def _newsletter_image_src(filename: str, *, env_key: str = "") -> str:
    """Hosted asset URL for email HTML (lightweight; no base64 unless offline fallback)."""
    override = getenv_optional(env_key, "").strip() if env_key else ""
    if override:
        return override
    return _newsletter_asset_url(filename, env_key=env_key)


def _centered_header_img_src(key: str) -> str:
    """Masthead ``<img src>`` at the public newsletter host."""
    files = {
        "desktop": (_HEADER_DESKTOP_FILE, "NEWSLETTER_HEADER_DESKTOP_URL"),
        "tablet": (_HEADER_TABLET_FILE, "NEWSLETTER_HEADER_TABLET_URL"),
        "mobile": (_HEADER_MOBILE_FILE, "NEWSLETTER_HEADER_MOBILE_URL"),
    }
    filename, env_key = files[key]
    return _newsletter_image_src(filename, env_key=env_key)
_CENTERED_FOOTER_LOGO_SRC = _newsletter_asset_url(
    "Evernile Capital Logo_OG.avif",
    env_key="NEWSLETTER_CENTERED_FOOTER_LOGO_URL",
)

# Public URLs for form links in emails.
# If per-link overrides are not provided, we fall back to relative paths (e.g. "/unsubscribe"),
# matching how the web app navigates internally (no manual base URL concatenation).
def _public_form_url(env_key: str, path: str) -> str:
    override = getenv_optional(env_key, "")
    if override:
        return override
    p = path if path.startswith("/") else f"/{path}"
    return p


_SCHEDULE_URL = _public_form_url("NEWSLETTER_SCHEDULE_URL", "/schedule-discussion")
_UNSUBSCRIBE_URL = _public_form_url("NEWSLETTER_UNSUBSCRIBE_URL", "/unsubscribe")

_FOOTER_CONTACT_PHONE = "+91 8889926196"
_FOOTER_CONTACT_PHONE_HREF = "tel:+918889926196"
_FOOTER_CONTACT_EMAIL = "contact@evernile.com"
_FOOTER_WHATSAPP_URL = "https://wa.me/918889926196?text="
_FOOTER_LINKEDIN_URL = getenv_optional("EVERNILE_LINKEDIN_URL", "https://www.linkedin.com/company/evernile/")
# Bump when whatsapp.png / linkedin.png are replaced: mail clients and image proxies
# cache by URL, so a same-name swap otherwise keeps serving the old artwork.
_FOOTER_SOCIAL_ICON_VERSION = "3"


def _versioned_icon_url(url: str) -> str:
    """Append the icon revision so recipients refetch replaced artwork."""
    if not _FOOTER_SOCIAL_ICON_VERSION:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}v={_FOOTER_SOCIAL_ICON_VERSION}"


def _footer_whatsapp_icon_src() -> str:
    return _versioned_icon_url(
        _newsletter_image_src("whatsapp.png", env_key="NEWSLETTER_FOOTER_WHATSAPP_ICON_URL")
    )


def _footer_linkedin_icon_src() -> str:
    return _versioned_icon_url(
        _newsletter_image_src("linkedin.png", env_key="NEWSLETTER_FOOTER_LINKEDIN_ICON_URL")
    )
_FOOTER_SOCIAL_ICON_PX = 13

# Open form links in a new tab in HTML email clients that honor it.
_FORM_A_ATTRS = ' target="_blank" rel="noopener noreferrer"'

# Vertical-layout email: narrow image column; tablet/desktop bg stretches to text height.
_VL_IMG_COL_WIDTH_PCT = "20.5%"
_VL_TEXT_COL_WIDTH_PCT = "79.5%"
_VL_STORY_ROW_MOBILE_IMG_H = 150

# Story headline font size (px) — unified at 16.
_STORY_HEADLINE_FONT_SIZE = 16

_SECTOR_ORDER = ["Healthcare", "Consumer", "BFSI", "Technology"]


# ══════════════════════════════════════════════════════════════════════════════
# Utilities
# ══════════════════════════════════════════════════════════════════════════════

def _e(s: object) -> str:
    text = str(s) if s is not None else ""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _fmt_date(iso: str | None) -> str:
    """Format an ISO date string as 'Month D, YYYY' (cross-platform)."""
    s = (iso or "").strip()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(s[:19], fmt)
            return f"{dt.strftime('%B')} {dt.day}, {dt.year}"
        except ValueError:
            continue
    return s


def _fmt_masthead_date(iso: str | None) -> str:
    """Newsletter header bar: 'Monday · May 18, 2026'."""
    s = (iso or "").strip()
    if not s:
        return ""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(s[:19], fmt)
            return f"{dt.strftime('%A')} · {_fmt_date(s)}"
        except ValueError:
            continue
    return s


def _masthead_date_display(payload: dict[str, Any]) -> str:
    """Build full masthead date string from payload (`Thursday · May 25, 2026`)."""
    header = payload.get("header") if isinstance(payload.get("header"), dict) else {}
    header_summary = (header.get("summary_date") or "").strip() if header else ""
    summary_date = (payload.get("summary_date") or "").strip()
    iso = header_summary or summary_date
    if iso:
        return _fmt_masthead_date(iso)
    return _fmt_masthead_date(datetime.today().strftime("%Y-%m-%d"))


def _src_line(a: dict) -> str:
    src  = _e(a.get("source", ""))
    date = _e(a.get("Scrape_date") or a.get("scrape_date") or a.get("source_date") or "")
    return f"{src}{' · ' + date if date else ''}"


def _bullets(a: dict, color: str = _ACCENT, size: int = 12) -> str:
    lh = size + 6
    rows = ""
    for key in ("summary_1", "summary_2"):
        pt = str(a.get(key, "")).strip()
        if pt:
            rows += (
                f'<tr><td style="padding-bottom:4px;vertical-align:top;">'
                f'<table cellpadding="0" cellspacing="0" border="0"><tr>'
                f'<td style="color:{color};font-weight:bold;padding-right:6px;'
                f'vertical-align:top;font-size:{size}px;line-height:{lh}px;'
                f'font-family:Arial,sans-serif;">•</td>'
                f'<td style="font-size:{size}px;line-height:{lh}px;color:{_FG};'
                f'font-family:Arial,sans-serif;">{_e(pt)}</td>'
                f'</tr></table></td></tr>'
            )
    return rows


def _hl(a: dict, size: int = _STORY_HEADLINE_FONT_SIZE, color: str = _FG, weight: str = "600") -> str:
    text  = _e(sanitize_headline(str(a.get("headline", "") or "")))
    url   = str(a.get("url", "")).strip()
    lh    = size + 7
    style = (
        f'font-size:{size}px;font-weight:{weight};color:{color};'
        f'line-height:{lh}px;font-family:Arial,sans-serif;text-decoration:underline;'
    )
    if url:
        return f'<a href="{_e(url)}" style="{style}">{text}</a>'
    return f'<span style="{style}">{text}</span>'


def _img_cover(
    url: str,
    alt: str = "",
    height: int = 160,
    rounded: str = "0",
    *,
    extra_class: str = "",
) -> str:
    """Fixed-height cover image for vertical-layout mobile story column."""
    if not url:
        return ""
    cls = f' class="{extra_class.strip()}"' if extra_class.strip() else ""
    return (
        f'<img src="{_e(url)}" width="100%" height="{height}" alt="{_e(alt)}"{cls} '
        f'style="display:block;width:100%;max-width:100%;height:{height}px;max-height:{height}px;'
        f'object-fit:cover;object-position:center;border-radius:{rounded};">'
    )


def _vertical_story_media_cell(url: str, alt: str = "") -> str:
    """Vertical image column: bg stretches to text height on tablet/desktop; fixed img on mobile."""
    if not url:
        return ""
    safe = url.replace("'", "%27")
    mobile_img = _img_cover(
        url,
        alt,
        height=_VL_STORY_ROW_MOBILE_IMG_H,
        rounded="0",
        extra_class="em-vl-story-mobile-only",
    )
    return (
        f'<td width="{_VL_IMG_COL_WIDTH_PCT}" class="em-stack em-vl-story-media" '
        f'style="vertical-align:top;padding:0;line-height:0;background:{_CARD};overflow:hidden;'
        f"background-image:url('{safe}');background-size:cover;"
        f'background-position:center center;">'
        f"{mobile_img}</td>"
    )


def _row_gap(px: int = 1, color: str = _HL_ICE) -> str:
    """A tiny visual gap between stacked content blocks."""
    return (
        f'<tr><td height="{px}" style="background:{color};'
        f'font-size:0;line-height:0;">&nbsp;</td></tr>'
    )


def _get_articles(sectors_raw: dict, label: str) -> list[dict]:
    articles = sectors_raw.get(label)
    if articles is None:
        key = next((k for k in sectors_raw if k.strip().lower() == label.lower()), None)
        articles = sectors_raw.get(key) if key else None
    if not isinstance(articles, list):
        return []
    return [a for a in articles if isinstance(a, dict)]


def _responsive_email_style_tag() -> str:
    """`<style>` block with mobile-only rules (`max-width: 620px`). Desktop clients
    that ignore media queries (e.g. Windows Outlook) keep the original layout."""
    css = f"""
@media print {{
  /* PDF export: start each new sector on a fresh page */
  tr.pdf-sector-break > td {{
    break-before: page;
    page-break-before: always;
  }}
}}

@media only screen and (max-width: 620px) {{
  html {{ -webkit-text-size-adjust: 100%; }}
  body {{ width: 100% !important; min-width: 0 !important; }}
  .em-shell {{ table-layout: auto !important; }}
  .em-sector-pad {{ padding-left: 12px !important; padding-right: 12px !important; }}
  .em-pad-header-outer {{ padding: 10px 8px 8px !important; }}
  td.em-stack {{
    display: block !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
  }}
  td.em-vl-story-media.em-stack {{
    margin-bottom: 0 !important;
  }}
  td.em-vl-story-media {{
    background-image: none !important;
    min-height: 0 !important;
    height: auto !important;
    padding: 0 0 4px 0 !important;
    margin: 0 !important;
    line-height: 0 !important;
    font-size: 0 !important;
  }}
  td.em-vl-story-media img.em-vl-story-mobile-only {{
    display: block !important;
    width: 100% !important;
    max-width: 100% !important;
    height: {_VL_STORY_ROW_MOBILE_IMG_H}px !important;
    max-height: {_VL_STORY_ROW_MOBILE_IMG_H}px !important;
    margin: 0 !important;
    padding: 0 !important;
    object-fit: cover !important;
    object-position: center center !important;
  }}
  td.em-vl-story-text.em-stack {{
    padding-top: 0 !important;
  }}
}}
"""
    return f"<style>{css}</style>"


def _email_theme_lock_head() -> str:
    """Declare light-only rendering so clients do not auto-invert for dark mode."""
    return (
        '<meta name="color-scheme" content="light only">\n'
        '<meta name="supported-color-schemes" content="light">\n'
    )


def _email_theme_lock_style_tag() -> str:
    """Force newsletter colours when the device prefers dark mode."""
    css = f"""
:root {{
  color-scheme: light only;
  supported-color-schemes: light;
}}
img {{
  -webkit-filter: none !important;
  filter: none !important;
}}
@media (prefers-color-scheme: dark) {{
  body.email-force-light,
  body.email-force-light table,
  body.email-force-light td,
  body.email-force-light p,
  body.email-force-light span,
  body.email-force-light div {{
    color: {_FG} !important;
  }}
  body.email-force-light td.em-header-masthead-wrap span,
  body.email-force-light td.em-header-date-overlay,
  body.email-force-light td.em-header-date-overlay span {{
    color: #ffffff !important;
    mso-color-alt: #ffffff;
  }}
  body.email-force-light {{
    background-color: {_BG} !important;
  }}
  body.email-force-light.email-centered-page {{
    background-color: {_CENTERED_PAGE_BG} !important;
  }}
  body.email-force-light.email-centered-page table.em-shell,
  body.email-force-light.email-centered-page table.em-centered-shell,
  body.email-force-light.email-centered-page td.em-centered-outer-pad,
  body.email-force-light.email-centered-page td.em-centered-footer-pad,
  body.email-force-light.email-centered-page td.em-centered-sector-pad,
  body.email-force-light.email-centered-page td.em-pad-header-outer,
  body.email-force-light.email-centered-page td.em-pad-header-outer.email-centered-header-pad {{
    background-color: {_CENTERED_PAGE_BG} !important;
  }}
  table.em-sector-card {{
    background-color: {_HL_ICE} !important;
    border-color: {_BORDER} !important;
  }}
  td.em-header-date-overlay,
  td.em-header-date-overlay span {{
    color: #ffffff !important;
    mso-color-alt: #ffffff;
  }}
  a {{
    color: inherit !important;
  }}
  a[style*="background:{_ACCENT}"],
  a[style*="background: {_ACCENT}"] {{
    background-color: {_ACCENT} !important;
    color: #ffffff !important;
  }}
  td.em-centered-footer-contact,
  td.em-centered-footer-contact span,
  td.em-centered-footer-contact a {{
    color: #6c7680 !important;
    font-family: Arial, sans-serif !important;
    font-size: 12px !important;
    line-height: 14px !important;
  }}
  td.em-footer-contact-mobile-line,
  td.em-footer-contact-mobile-line span,
  td.em-footer-contact-mobile-line a {{
    color: #6c7680 !important;
    font-family: Arial, sans-serif !important;
    font-size: 10px !important;
    line-height: 14px !important;
  }}
}}
"""
    return f"<style>{css}</style>"


def _centered_email_style_tag() -> str:
    sw = _CENTERED_SHELL_W
    sw_t = _CENTERED_SHELL_W_TABLET
    sw_m = _CENTERED_SHELL_W_MOBILE
    tmax = _CENTERED_BP_TABLET_MAX
    css = f"""
table.em-centered-shell {{
  margin-left: auto !important;
  margin-right: auto !important;
}}

td.em-header-masthead-wrap,
td.em-header-desktop-wrap {{
  padding: 0 !important;
  background-color: #0a1628 !important;
  width: 100% !important;
}}
/* Mobile-first: Gmail app often ignores min-width MQ — show mobile by default */
table.em-header-desktop {{
  display: none !important;
  max-height: 0 !important;
  overflow: hidden !important;
}}
table.em-header-variant-m {{
  display: table !important;
  width: 100% !important;
  max-width: 345px !important;
  border-collapse: collapse !important;
  table-layout: fixed !important;
}}
table.em-header-variant-t {{
  display: none !important;
  max-height: 0 !important;
  overflow: hidden !important;
}}
td.em-header-desktop-canvas {{
  width: 100% !important;
  max-width: 900px !important;
  height: 210px !important;
  max-height: 210px !important;
  padding: 0 !important;
  vertical-align: top !important;
  background-color: #0a1628 !important;
  background-repeat: no-repeat !important;
  background-size: 100% 100% !important;
  background-position: top left !important;
}}
td.em-header-desktop-canvas td.em-header-spacer-top {{
  height: 133px !important;
  max-height: 133px !important;
  line-height: 133px !important;
}}
td.em-header-desktop-canvas td.em-header-date-row {{
  text-align: right !important;
  padding-right: 30px !important;
}}
td.em-header-desktop-canvas td.em-header-date-overlay {{
  text-align: right !important;
  vertical-align: middle !important;
  font-weight: 400 !important;
  font-size: 12px !important;
  width: 140px !important;
  height: 36px !important;
}}
td.em-header-variant-canvas.em-header-variant-canvas-m {{
  height: {_CENTERED_HERO_H_MOBILE}px !important;
  max-height: {_CENTERED_HERO_H_MOBILE}px !important;
}}
td.em-header-variant-canvas.em-header-variant-canvas-t {{
  height: {_CENTERED_HERO_H_TABLET}px !important;
  max-height: {_CENTERED_HERO_H_TABLET}px !important;
}}
td.em-header-variant-canvas {{
  padding: 0 !important;
  vertical-align: top !important;
  background-color: #0a1628 !important;
  background-repeat: no-repeat !important;
  background-size: 100% 100% !important;
  background-position: top left !important;
}}
td.em-header-date-row {{
  text-align: right !important;
  vertical-align: middle !important;
}}
td.em-header-date-overlay,
td.em-header-date-overlay span {{
  text-align: right !important;
  vertical-align: middle !important;
  font-weight: 400 !important;
  color: #ffffff !important;
  mso-color-alt: #ffffff;
}}
table.em-header-variant-m td.em-header-spacer-top {{
  height: {_CENTERED_HEADER_MOBILE_DATE_Y}px !important;
  max-height: {_CENTERED_HEADER_MOBILE_DATE_Y}px !important;
  line-height: {_CENTERED_HEADER_MOBILE_DATE_Y}px !important;
}}
table.em-header-variant-m td.em-header-date-right-pad {{
  width: {_CENTERED_HEADER_MOBILE_RIGHT_PAD}px !important;
}}
table.em-header-variant-m td.em-header-date-overlay,
table.em-header-variant-m td.em-header-date-overlay span {{
  font-size: {_CENTERED_HEADER_MOBILE_DATE_FONT_PX}px !important;
  line-height: {_CENTERED_HEADER_MOBILE_DATE_LINE_PX}px !important;
  font-weight: 500 !important;
  text-align: right !important;
  white-space: nowrap !important;
}}
table.em-header-variant-t td.em-header-date-overlay,
table.em-header-variant-t td.em-header-date-overlay span {{
  font-size: 10px !important;
  line-height: 12px !important;
  font-weight: 500 !important;
  text-align: right !important;
  white-space: nowrap !important;
}}
td.em-header-desktop-canvas td.em-header-date-overlay,
td.em-header-desktop-canvas td.em-header-date-overlay span {{
  font-size: 12px !important;
  line-height: 14px !important;
  font-weight: 400 !important;
}}

@media only screen and (min-width: 621px) {{
  .em-centered-outer-pad {{
    padding-top: 12px !important;
    padding-bottom: 6px !important;
  }}
  table.em-centered-shell td.em-centered-sector-pad,
  table.em-centered-shell td.em-pad-header-outer,
  table.em-centered-shell td.em-centered-footer-pad {{
    padding-left: 0 !important;
    padding-right: 0 !important;
  }}
  table.em-centered-shell td.em-pad-header-outer {{
    padding-top: 8px !important;
  }}
  table.em-centered-shell td.em-centered-sector-pad > table,
  table.em-centered-shell td.em-pad-header-outer > table,
  table.em-centered-shell td.em-centered-footer-pad > table {{
    width: 100% !important;
    max-width: 100% !important;
  }}
  td.em-centered-footer-unsub {{
    padding-top: 1px !important;
    padding-bottom: 3px !important;
  }}
  td.em-centered-footer-copy {{
    padding-top: 0 !important;
    padding-bottom: 1px !important;
  }}
  tr.em-footer-contact-mobile {{
    display: none !important;
    max-height: 0 !important;
    overflow: hidden !important;
    mso-hide: all;
  }}
  tr.em-footer-sep-mobile {{
    display: none !important;
    max-height: 0 !important;
    overflow: hidden !important;
    mso-hide: all;
  }}
  td.em-vl-story-media img.em-vl-story-mobile-only {{
    display: none !important;
    max-height: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    visibility: hidden !important;
    line-height: 0 !important;
    font-size: 0 !important;
    mso-hide: all;
  }}
  td.em-vl-story-media {{
    background-size: cover !important;
    background-position: center center !important;
  }}
}}

@media only screen and (min-width: 1024px) {{
  table.em-centered-shell {{
    width: {sw}px !important;
    max-width: {sw}px !important;
    min-width: {sw}px !important;
    table-layout: fixed !important;
  }}
  table.em-header-desktop {{
    display: table !important;
    max-height: none !important;
    overflow: visible !important;
    width: 100% !important;
    max-width: 900px !important;
    border-collapse: collapse !important;
    table-layout: fixed !important;
  }}
  table.em-header-variant-m,
  table.em-header-variant-t {{
    display: none !important;
    max-height: 0 !important;
    overflow: hidden !important;
  }}
}}

@media only screen and (min-width: 621px) and (max-width: {tmax}px) {{
  table.em-centered-shell {{
    width: {sw_t}px !important;
    max-width: {sw_t}px !important;
    min-width: {sw_t}px !important;
    table-layout: fixed !important;
  }}
  table.em-header-desktop,
  table.em-header-variant-m {{
    display: none !important;
    max-height: 0 !important;
    overflow: hidden !important;
    mso-hide: all;
  }}
  table.em-header-variant-t {{
    display: table !important;
    max-height: none !important;
    overflow: visible !important;
    width: 100% !important;
    max-width: 650px !important;
    border-collapse: collapse !important;
    table-layout: fixed !important;
  }}
}}

@media only screen and (max-width: 620px) {{
  table.em-centered-shell {{
    width: {sw_m}px !important;
    max-width: {sw_m}px !important;
    min-width: {sw_m}px !important;
    table-layout: fixed !important;
  }}
  .em-centered-outer-pad {{
    padding: 5px 0 3px !important;
  }}
  tr.em-footer-contact-desktop {{
    display: none !important;
    max-height: 0 !important;
    overflow: hidden !important;
    mso-hide: all;
  }}
  tr.em-footer-cta-desktop {{
    display: none !important;
    max-height: 0 !important;
    overflow: hidden !important;
    mso-hide: all;
  }}
  tr.em-footer-sep-desktop {{
    display: none !important;
    max-height: 0 !important;
    overflow: hidden !important;
    mso-hide: all;
  }}
  p.em-footer-tagline {{
    font-size: 10px !important;
    line-height: 14px !important;
  }}
  p.em-footer-subline {{
    font-size: 9px !important;
    line-height: 13px !important;
  }}
  td.em-footer-logo-row {{
    padding-top: 11px !important;
  }}
  table.em-centered-shell td.em-centered-sector-pad,
  table.em-centered-shell td.em-pad-header-outer,
  table.em-centered-shell td.em-centered-footer-pad {{
    padding-left: 0 !important;
    padding-right: 0 !important;
  }}
  table.em-centered-shell td.em-pad-header-outer {{
    padding-top: 8px !important;
  }}
  td.em-centered-footer-unsub {{
    padding-top: 1px !important;
    padding-bottom: 3px !important;
  }}
  td.em-centered-footer-copy {{
    padding-top: 0 !important;
    padding-bottom: 1px !important;
  }}
  td.em-footer-contact-mobile-text {{
    white-space: normal !important;
    text-align: left !important;
  }}
  td.em-footer-contact-mobile-line {{
    white-space: nowrap !important;
    text-align: left !important;
  }}
  td.em-footer-cta-mobile-cell {{
    white-space: nowrap !important;
    text-align: right !important;
  }}
  table.em-header-desktop,
  table.em-header-variant-t {{
    display: none !important;
    max-height: 0 !important;
    overflow: hidden !important;
  }}
  table.em-header-variant-m {{
    display: table !important;
    max-height: none !important;
    overflow: visible !important;
    width: 100% !important;
    max-width: 345px !important;
    border-collapse: collapse !important;
    table-layout: fixed !important;
  }}
}}
"""
    mso_css = """
<!--[if gte mso 9]>
<style type="text/css">
  table.em-header-desktop { display: table !important; max-height: none !important; overflow: visible !important; }
  table.em-header-variant-m, table.em-header-variant-t { display: none !important; max-height: 0 !important; overflow: hidden !important; }
  td.em-header-date-overlay, td.em-header-date-overlay span { color: #ffffff !important; font-size: 12px !important; line-height: 14px !important; font-weight: 400 !important; }
</style>
<![endif]-->
"""
    return f"<style>{css}</style>{mso_css}"


def _use_centered_page_background(html: str) -> str:
    """Use the centered template's page color for outer padding areas only."""
    return (
        html.replace(f"background:{_BG};", f"background:{_CENTERED_PAGE_BG};")
            .replace(f"background-color:{_BG};", f"background-color:{_CENTERED_PAGE_BG};")
    )


# ══════════════════════════════════════════════════════════════════════════════
# Shared header / footer  (mirrors NewsletterHeader.tsx)
# ══════════════════════════════════════════════════════════════════════════════

def _header_centered(date_display: str) -> str:
    """Centered masthead — one desktop block + mobile/tablet for non-Outlook only.

    Do **not** duplicate the desktop header inside ``<!--[if mso]>`` and
    ``<!--[if !mso]>`` — many clients (Gmail included) render both branches and
    produce a blank dark header stacked above the real banner.

    Outlook desktop (Word) ignores media queries, so mobile/tablet stay inside
    ``<!--[if !mso]>`` and never appear there. Everyone else gets desktop +
    mobile + tablet with CSS choosing one.
    """
    desktop = _header_centered_desktop_block(date_display)
    mobile = _centered_header_variant_block("mobile", "em-header-variant-m", date_display)
    tablet = _centered_header_variant_block("tablet", "em-header-variant-t", date_display)
    blocks = (
        desktop
        + f"<!--[if !mso]><!-->{mobile}{tablet}<!--<![endif]-->"
    )
    return (
        f'\n        <!-- Newsletter masthead (centered responsive) -->\n'
        f'        <tr>\n'
        f'          <td class="em-pad-header-outer email-centered-header-pad" style="background:{_CENTERED_PAGE_BG};padding:8px 0 10px;">\n'
        f'            <table width="100%" cellpadding="0" cellspacing="0" border="0"\n'
        f'                   style="border-radius:12px;overflow:hidden;width:100%;max-width:100%;">\n'
        f'              <tr>\n'
        f'                <td class="em-header-masthead-wrap em-header-desktop-wrap"\n'
        f'                    style="padding:0;background-color:#0a1628;width:100%;">\n'
        f"{blocks}"
        f'                </td>\n'
        f'              </tr>\n'
        f'            </table>\n'
        f'          </td>\n'
        f'        </tr>\n'
    )


def _footer_centered() -> str:
    """Minimal footer used only by the centered vertical template."""
    year = datetime.today().year
    schedule_href = _e(_SCHEDULE_URL)
    unsub_href = _e(_UNSUBSCRIBE_URL)
    wa_href = _e(_FOOTER_WHATSAPP_URL)
    li_href = _e(_FOOTER_LINKEDIN_URL)
    phone_href = _e(_FOOTER_CONTACT_PHONE_HREF)
    mail_href = _e(f"mailto:{_FOOTER_CONTACT_EMAIL}")
    sep = _CENTERED_SEP
    text = "#6c7680"
    link = "#253246"
    btn = (
        f"display:inline-block;background:{_ACCENT};color:#ffffff;border:none;border-radius:8px;"
        f"padding:8px 16px;font-family:Arial,sans-serif;font-size:13px;"
        f"font-weight:600;line-height:16px;text-decoration:none;white-space:nowrap;"
    )
    contact_text = (
        f"font-family:Arial,sans-serif;font-size:12px;line-height:14px;"
        f"color:{text};"
    )
    contact_link = f"{contact_text}text-decoration:none;"
    contact_td = f"{contact_text}vertical-align:middle;white-space:nowrap;"
    contact_dot = (
        f"font-family:Arial,sans-serif;font-size:12px;line-height:14px;"
        f"color:{text};vertical-align:middle;padding:0 4px;"
    )
    icon_td = "vertical-align:middle;padding:0;line-height:0;"
    icon_link = "text-decoration:none;display:inline-block;line-height:0;"
    footer_legal = (
        f"font-family:Arial,sans-serif;font-size:7px;line-height:10px;font-weight:400;"
        f"color:{_FOOTER_LEGAL_TEXT};text-align:center;"
    )
    btn_mobile = (
        f"display:inline-block;background:{_ACCENT};color:#ffffff;border:none;border-radius:5px;"
        f"padding:4px 8px;font-family:Arial,sans-serif;font-size:11px;"
        f"font-weight:600;line-height:14px;text-decoration:none;white-space:nowrap;"
    )
    # Top-aligned so the button sits level with the first contact line.
    cta_td_mobile = (
        "vertical-align:top;text-align:right;white-space:nowrap;padding:0 0 0 6px;width:1%;"
    )
    contact_td_mobile = (
        f"font-family:Arial,sans-serif;font-size:10px;line-height:14px;"
        f"color:{text};vertical-align:middle;text-align:left;"
    )
    # 14px line box for the mobile contact rows; the phone row runs 1px shorter so the
    # number sits closer to the email line.
    contact_line_mobile = (
        f"font-family:Arial,sans-serif;font-size:10px;line-height:14px;height:14px;"
        f"color:{text};text-align:left;vertical-align:middle;"
    )
    contact_line_mobile_phone = (
        f"font-family:Arial,sans-serif;font-size:10px;line-height:12px;height:12px;"
        f"color:{text};text-align:left;vertical-align:middle;"
    )
    contact_text_mobile = (
        f"font-family:Arial,sans-serif;font-size:10px;line-height:14px;color:{text};"
    )
    contact_link_mobile = f"{contact_text_mobile}text-decoration:none;"
    icon_px = _FOOTER_SOCIAL_ICON_PX
    icon_img = (
        f"display:block;width:{icon_px}px;height:{icon_px}px;max-width:{icon_px}px;"
        "border:0;-ms-interpolation-mode:bicubic;"
    )

    return (
        f'\n        <!-- Minimal centered footer -->\n'
        f'        <tr>\n'
        f'          <td class="em-centered-footer-pad" style="background:{_CENTERED_PAGE_BG};padding:0;">\n'
        f'            <table width="100%" cellpadding="0" cellspacing="0" border="0">\n'
        f'              <tr class="em-footer-sep-desktop"><td height="1" style="background:{sep};font-size:0;line-height:0;">&nbsp;</td></tr>\n'
        f'              <tr><td class="em-footer-logo-row" align="center" style="padding:18px 12px 10px;">\n'
        f'                <img src="{_e(_CENTERED_FOOTER_LOGO_SRC)}" alt="Evernile Capital" width="120" border="0"\n'
        f'                     style="display:block;width:120px;max-width:88%;height:auto;margin:0 auto;">\n'
        f'              </td></tr>\n'
        f'              <tr><td align="center" style="padding:0 12px 2px;">\n'
        f'                <p class="em-footer-tagline" style="margin:0;font-family:Arial,sans-serif;font-size:12px;line-height:17px;'
        f'font-weight:600;color:{link};text-align:center;">'
        f'We are an investment banking firm advising Indian enterprises across '
        f'capital raises, M&amp;A, and strategic financial advisory.</p>\n'
        f'              </td></tr>\n'
        f'              <tr><td align="center" style="padding:0 12px 10px;">\n'
        f'                <p class="em-footer-subline" style="margin:0;font-family:Arial,sans-serif;font-size:11px;line-height:16px;'
        f'font-weight:400;color:{link};text-align:center;">'
        f'To learn more or start a conversation, connect with us below.</p>\n'
        f'              </td></tr>\n'
        f'              <tr class="em-footer-sep-mobile"><td height="1" style="background:{sep};font-size:0;line-height:0;">&nbsp;</td></tr>\n'
        f'              <tr class="em-footer-cta-desktop"><td align="center" style="padding:0 12px 12px;">\n'
        f'                <a href="{schedule_href}"{_FORM_A_ATTRS} style="{btn}">Connect with us</a>\n'
        f'              </td></tr>\n'
        f'              <tr class="em-footer-contact-desktop"><td align="center" style="padding:0 12px 18px;">\n'
        f'                <table align="center" cellpadding="0" cellspacing="0" border="0"><tr>\n'
        f'                  <td class="em-centered-footer-contact" style="{contact_td}">'
        f'<span style="{contact_text}">Gurugram | Ahmedabad</span></td>\n'
        f'                  <td class="em-centered-footer-contact" style="{contact_dot}">&middot;</td>\n'
        f'                  <td class="em-centered-footer-contact" style="{contact_td}">'
        f'<a href="{phone_href}" style="{contact_link}">{_FOOTER_CONTACT_PHONE}</a></td>\n'
        f'                  <td class="em-centered-footer-contact" style="{contact_dot}">&middot;</td>\n'
        f'                  <td class="em-centered-footer-contact" style="{contact_td}">'
        f'<a href="{mail_href}" style="{contact_link}">{_FOOTER_CONTACT_EMAIL}</a></td>\n'
        f'                  <td style="{contact_dot}">&middot;</td>\n'
        f'                  <td style="{icon_td}">'
        f'<a href="{wa_href}"{_FORM_A_ATTRS} style="{icon_link}">'
        f'<img src="{_e(_footer_whatsapp_icon_src())}" width="{icon_px}" height="{icon_px}" alt="WhatsApp" style="{icon_img}"></a></td>\n'
        f'                  <td style="{contact_dot}">&middot;</td>\n'
        f'                  <td style="{icon_td}">'
        f'<a href="{li_href}"{_FORM_A_ATTRS} style="{icon_link}">'
        f'<img src="{_e(_footer_linkedin_icon_src())}" width="{icon_px}" height="{icon_px}" alt="LinkedIn" style="{icon_img}"></a></td>\n'
        f'                </tr></table>\n'
        f'              </td></tr>\n'
        f'              <tr class="em-footer-contact-mobile"><td style="padding:10px 8px 18px;">\n'
        f'                <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr>\n'
        f'                  <td class="em-footer-contact-mobile-text" align="left" style="{contact_td_mobile}">\n'
        f'                    <table align="left" cellpadding="0" cellspacing="0" border="0">\n'
        f'                      <tr><td class="em-footer-contact-mobile-line" style="{contact_line_mobile}">\n'
        f'<span style="{contact_text_mobile}">Gurugram | Ahmedabad</span></td></tr>\n'
        f'                      <tr><td class="em-footer-contact-mobile-line" style="{contact_line_mobile_phone}">\n'
        f'<a href="{phone_href}" style="{contact_link_mobile}">{_FOOTER_CONTACT_PHONE}</a></td></tr>\n'
        f'                      <tr><td class="em-footer-contact-mobile-line" style="{contact_line_mobile}">\n'
        f'<a href="{mail_href}" style="{contact_link_mobile}">{_FOOTER_CONTACT_EMAIL}</a></td></tr>\n'
        f'                      <tr><td class="em-footer-contact-mobile-line" style="{contact_line_mobile}">\n'
        f'<a href="{wa_href}"{_FORM_A_ATTRS} style="{icon_link} vertical-align:middle;padding-right:2px;"><img src="{_e(_footer_whatsapp_icon_src())}" width="{icon_px}" height="{icon_px}" alt="WhatsApp" style="{icon_img}"></a>'
        f'<a href="{li_href}"{_FORM_A_ATTRS} style="{icon_link} vertical-align:middle;"><img src="{_e(_footer_linkedin_icon_src())}" width="{icon_px}" height="{icon_px}" alt="LinkedIn" style="{icon_img}"></a></td></tr>\n'
        f'                    </table>\n'
        f'                  </td>\n'
        f'                  <td class="em-footer-cta-mobile-cell" align="right" style="{cta_td_mobile}">\n'
        f'<a href="{schedule_href}"{_FORM_A_ATTRS} style="{btn_mobile}">Connect with us</a></td>\n'
        f'                </tr></table>\n'
        f'              </td></tr>\n'
        f'              <tr><td class="em-centered-footer-unsub" align="center" style="background:{_CENTERED_FOOTER_STRIP_BG};padding:1px 12px 3px;">\n'
        f'                <p style="margin:0;{footer_legal}">'
        f'<a href="{unsub_href}"{_FORM_A_ATTRS} style="color:{_FOOTER_LEGAL_TEXT};font-size:7px;font-weight:400;text-decoration:underline;">Unsubscribe</a></p>\n'
        f'              </td></tr>\n'
        f'              <tr><td class="em-centered-footer-copy" align="center" style="background:{_CENTERED_FOOTER_STRIP_BG};padding:0 12px 1px;">\n'
        f'                <p style="margin:0;{footer_legal}">'
        f'Copyright &copy; {year} Evernile. All Rights Reserved.</p>\n'
        f'              </td></tr>\n'
        f'            </table>\n'
        f'          </td>\n'
        f'        </tr>\n'
    )


# ══════════════════════════════════════════════════════════════════════════════
# Vertical centered
# ══════════════════════════════════════════════════════════════════════════════

def _section_header_vertical(label: str) -> str:
    return (
        f'<tr><td style="background:{_HL_MID};padding:10px 16px;'
        f'border-bottom:1px solid {_BORDER};">'
        f'<span style="font-size:12px;font-weight:750;letter-spacing:2px;'
        f'color:{_ACCENT};font-family:Arial,sans-serif;">'
        f'{_e(label.upper())}</span></td></tr>'
    )


def _article_row_vertical(
    article: dict,
    idx: int,
    *,
    desktop_tall_lead: bool = False,
    lead_img_height: int | None = None,
) -> str:
    """Narrow image column; tablet/desktop image height matches text column; fixed img on mobile."""
    del idx, desktop_tall_lead, lead_img_height
    img_url = str(article.get("image_url", "")).strip()
    hl = _hl(article)
    bl = _bullets(article, color=_ACCENT, size=12)
    src = _src_line(article)

    img_cell = _vertical_story_media_cell(img_url, article.get("headline", "") or "") if img_url else ""
    text_w = _VL_TEXT_COL_WIDTH_PCT if img_url else "100%"
    text_cls = ' class="em-stack em-vl-story-text"' if img_url else ' class="em-vl-story-text"'

    return (
        f"<tr>"
        f"{img_cell}"
        f'<td width="{text_w}"{text_cls} style="vertical-align:top;background:{_CARD};padding:12px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" border="0">'
        f'<tr><td style="padding-bottom:8px;">{hl}</td></tr>'
        f"{bl}"
        f'<tr><td style="padding-top:6px;font-size:10px;color:{_FG_MUTED};'
        f'font-family:Arial,sans-serif;">{src}</td></tr>'
        f"</table>"
        f"</td>"
        f"</tr>"
    )


def _render_vertical(sectors_raw: dict) -> str:
    rows = ""
    sector_idx = 0
    for label in _SECTOR_ORDER:
        articles = _get_articles(sectors_raw, label)
        if not articles:
            continue
        card_rows = _section_header_vertical(label)
        for i, art in enumerate(articles):
            if i > 0:
                card_rows += _row_gap(1, _HL_ICE)
            card_rows += _article_row_vertical(art, i, desktop_tall_lead=True)

        classes: list[str] = []
        if sector_idx > 0:
            classes.append("pdf-sector-break")
        row_cls = f' class="{" ".join(classes)}"' if classes else ""
        rows += (
            f'<tr{row_cls}><td class="em-sector-pad em-centered-sector-pad"'
            f' style="background:{_CENTERED_PAGE_BG};padding:0 0 10px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" border="0" class="em-sector-card"'
            f' style="background:{_HL_ICE};border-radius:16px;'
            f'border:1px solid {_BORDER};overflow:hidden;">'
            f"{card_rows}"
            f"</table></td></tr>"
        )
        sector_idx += 1
    return rows


# ══════════════════════════════════════════════════════════════════════════════
# Dispatch table — centered layouts only
# ══════════════════════════════════════════════════════════════════════════════

_RENDERERS: dict[str, Any] = {
    "vertical-centered-layout": _render_vertical,
}


# ══════════════════════════════════════════════════════════════════════════════
# Public entry point
# ══════════════════════════════════════════════════════════════════════════════

def render_newsletter_email(
    payload: dict[str, Any],
    template_id: str = "vertical-centered-layout",
) -> str:
    """Convert *payload* + *template_id* into a centered-layout HTML email string."""
    summary_date: str = str(payload.get("summary_date") or "")
    sectors_raw: dict = payload.get("sectors") or {}
    # Optional: display label overrides for sector display names.
    label_overrides = payload.get("sector_label_overrides") or {}
    if isinstance(sectors_raw, dict) and isinstance(label_overrides, dict) and label_overrides:
        sectors_raw = {**sectors_raw, "__label_overrides": label_overrides}

    header: dict[str, Any] = payload.get("header") or {}
    header_label = str(header.get("newsletter_label") or "").strip() or "Daily Newsletter"
    date_display = _masthead_date_display(payload)

    from pipeline.shared.newsletter_templates import normalize_template_id

    template_id = normalize_template_id(template_id)
    renderer = _RENDERERS[template_id]
    content_rows = renderer(sectors_raw)

    centered_header = _use_centered_page_background(_header_centered(date_display))
    centered_content_rows = _use_centered_page_background(content_rows)
    centered_footer = _footer_centered()
    return f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
{_email_theme_lock_head()}<title>Evernile Capital — {_e(header_label)}</title>
<!--[if mso]><noscript><xml>
<o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings>
</xml></noscript><![endif]-->
{_email_theme_lock_style_tag()}
{_responsive_email_style_tag()}
{_centered_email_style_tag()}
</head>
<body class="email-force-light email-centered-page" style="margin:0;padding:0;background-color:{_CENTERED_PAGE_BG} !important;color:{_FG} !important;">
<table width="100%" cellpadding="0" cellspacing="0" border="0"
       style="width:100%;background-color:{_CENTERED_PAGE_BG};">
  <tr>
    <td align="center" class="em-centered-outer-pad" style="padding:12px 0 6px;">
      <table width="{_CENTERED_SHELL_W}" align="center" cellpadding="0" cellspacing="0" border="0"
             class="em-shell em-centered-shell"
             style="width:{_CENTERED_SHELL_W}px;max-width:{_CENTERED_SHELL_W}px;min-width:{_CENTERED_SHELL_W}px;table-layout:fixed;background-color:{_CENTERED_PAGE_BG};">
        {centered_header}
        {centered_content_rows}
        {centered_footer}
      </table>
    </td>
  </tr>
</table>
</body>
</html>"""
