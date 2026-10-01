/** Shared newsletter brand tokens and masthead geometry. */

/** Centered newsletter template: fixed main-block widths (mobile / tablet / desktop). */
export const CENTERED_NEWSLETTER_SHELL_W_DESKTOP = 900;
export const CENTERED_NEWSLETTER_SHELL_W_TABLET = 650;
export const CENTERED_NEWSLETTER_SHELL_W_MOBILE = 345;

/** Static art lives in `public/` and is served from the site root. */
export function newsletterPublicImgSrc(filename: string): string {
  const segments = filename.split("/").filter(Boolean);
  return `/${segments.map((segment) => encodeURIComponent(segment)).join("/")}`;
}

/** Perfected desktop date box (900×210 artboard) — do not change. */
export const CENTERED_HEADER_DESKTOP_DATE_BOX = {
  x: 730,
  y: 169,
  w: 140,
  h: 36,
} as const;

/** Right inset scaled from desktop (30px @ 900px). */
export function centeredHeaderDateRightPadPx(artW: number): number {
  return Math.round((30 * artW) / CENTERED_NEWSLETTER_SHELL_W_DESKTOP);
}

/** Date box anchored to bottom-right footer bar; wide enough for full weekday + date. */
export function centeredHeaderDateBoxRight(
  artW: number,
  _artH: number,
  y: number,
  h: number,
  boxW: number,
) {
  const rightPad = centeredHeaderDateRightPadPx(artW);
  return {
    x: artW - rightPad - boxW,
    y,
    w: boxW,
    h,
  };
}

/** Tablet 650×160 — bottom-right footer bar. */
export const CENTERED_HEADER_TABLET_DATE_Y = 132.7;

/** Mobile 345×150 — bottom-right footer bar. */
export const CENTERED_HEADER_MOBILE_DATE_Y = 127.1;

/** Tablet 650×160 — bottom-right, right-aligned full date. */
export const CENTERED_HEADER_TABLET_DATE_BOX = centeredHeaderDateBoxRight(
  650,
  160,
  CENTERED_HEADER_TABLET_DATE_Y,
  20.6528,
  300,
);

/** Mobile 345×150 — bottom-right, right-aligned full date. */
export const CENTERED_HEADER_MOBILE_DATE_BOX = centeredHeaderDateBoxRight(
  345,
  150,
  CENTERED_HEADER_MOBILE_DATE_Y,
  14.259,
  200,
);

export function centeredHeaderDateBoxPct(
  artW: number,
  artH: number,
  box: { x: number; y: number; w: number; h: number },
) {
  return {
    top: (box.y / artH) * 100,
    right: ((artW - box.x - box.w) / artW) * 100,
    width: (box.w / artW) * 100,
    height: (box.h / artH) * 100,
  };
}

/** Matches email CSS font sizes (mobile variant uses 8px in email). */
export function centeredHeaderDateFontSizePx(artH: number): number {
  if (artH >= 200) return 12;
  if (artH >= 155) return 10;
  return 8;
}

/** Preview typography — sizes/weights match email masthead date overlay. */
export function centeredHeaderDateTypography(artH: number): {
  fontSize: string;
  lineHeight: string;
  fontWeight: number;
  fontFamily: string;
  letterSpacing: string;
  textTransform: "uppercase";
  color: string;
  whiteSpace: "nowrap";
  textAlign: "right";
  display: "block";
  width: string;
} {
  const fontSize = centeredHeaderDateFontSizePx(artH);
  const lineHeight = artH >= 200 ? fontSize + 2 : artH >= 155 ? 12 : 10;
  return {
    fontSize: `${fontSize}px`,
    lineHeight: `${lineHeight}px`,
    fontWeight: artH >= 200 ? 400 : 500,
    fontFamily: "Arial, Helvetica, sans-serif",
    letterSpacing: "0.02em",
    textTransform: "uppercase",
    color: "#ffffff",
    whiteSpace: "nowrap",
    textAlign: "right",
    display: "block",
    width: "100%",
  };
}

/** Date overlay box — same top / right / size % as email spacer tables. */
export function centeredHeaderDateOverlayStyle(
  artW: number,
  artH: number,
  box: { x: number; y: number; w: number; h: number },
) {
  const pct = centeredHeaderDateBoxPct(artW, artH, box);
  return {
    top: `${pct.top}%`,
    right: `${pct.right}%`,
    width: `${pct.width}%`,
    height: `${pct.height}%`,
  };
}

/** Header image URL (local `public/`). */
function newsletterHeaderImgSrc(filename: string): string {
  return newsletterPublicImgSrc(filename);
}

/** Desktop masthead source pixels (2× display size for sharp downscale in 900×210). */
export const CENTERED_HEADER_DESKTOP_NATURAL = {
  w: 1800,
  h: 420,
} as const;

/** Tablet masthead source pixels (2× display size for sharp downscale in 650×160). */
export const CENTERED_HEADER_TABLET_NATURAL = {
  w: 1300,
  h: 320,
} as const;

/** Mobile masthead source pixels (2× display size for sharp downscale in 345×150). */
export const CENTERED_HEADER_MOBILE_NATURAL = {
  w: 690,
  h: 300,
} as const;

export const CENTERED_HEADER_DESKTOP = {
  w: 900,
  h: 210,
  naturalW: CENTERED_HEADER_DESKTOP_NATURAL.w,
  naturalH: CENTERED_HEADER_DESKTOP_NATURAL.h,
  src: newsletterHeaderImgSrc("Newsletter_Header_Desktop.jpg"),
  dateBox: CENTERED_HEADER_DESKTOP_DATE_BOX,
} as const;

export const CENTERED_HEADER_TABLET = {
  w: 650,
  h: 160,
  naturalW: CENTERED_HEADER_TABLET_NATURAL.w,
  naturalH: CENTERED_HEADER_TABLET_NATURAL.h,
  src: newsletterHeaderImgSrc("Newsletter_Header_Tab.jpg"),
  dateBox: CENTERED_HEADER_TABLET_DATE_BOX,
} as const;

export const CENTERED_HEADER_MOBILE = {
  w: 345,
  h: 150,
  naturalW: CENTERED_HEADER_MOBILE_NATURAL.w,
  naturalH: CENTERED_HEADER_MOBILE_NATURAL.h,
  src: newsletterHeaderImgSrc("Newsletter_Header_Mobile.jpg"),
  dateBox: CENTERED_HEADER_MOBILE_DATE_BOX,
} as const;

export const CENTERED_HEADER_ART = {
  desktop: CENTERED_HEADER_DESKTOP,
  tablet: CENTERED_HEADER_TABLET,
  mobile: CENTERED_HEADER_MOBILE,
} as const;

/** Widths driven by `.centered-newsletter-shell` in index.css (345 / 650 / 900). */
export const CENTERED_NEWSLETTER_SHELL_CLASS = "centered-newsletter-shell shrink-0";

/** Shared story headline typography for all centered template previews. */
export const NEWSLETTER_STORY_HEADLINE_CLASS =
  "font-sans text-base font-semibold text-foreground mt-1 leading-snug underline";

export const NEWSLETTER_STORY_HEADLINE_LINK_CLASS =
  `${NEWSLETTER_STORY_HEADLINE_CLASS} block hover:text-accent transition-colors`;

/** Soft separator lines (footer rules + internal dividers) — matches vertical centered footer. */
export const CENTERED_SEPARATOR_COLOR = "#c0d2dc";
export const CENTERED_SEPARATOR_BORDER_CLASS = "border-[#c0d2dc]";

/** Centered template footer logo. */
export const CENTERED_FOOTER_LOGO_SRC = newsletterPublicImgSrc("Evernile Capital Logo_OG.avif");

/** Footer WhatsApp / LinkedIn icon size (px) — preview and email parity. */
export const NEWSLETTER_FOOTER_SOCIAL_ICON_PX = 13;

/** Icon revision - keep in sync with `_FOOTER_SOCIAL_ICON_VERSION`; bump when the files are replaced. */
const FOOTER_SOCIAL_ICON_VERSION = "3";

export const NEWSLETTER_FOOTER_WHATSAPP_ICON_SRC = `${newsletterPublicImgSrc("whatsapp.png")}?v=${FOOTER_SOCIAL_ICON_VERSION}`;

export const NEWSLETTER_FOOTER_LINKEDIN_ICON_SRC = `${newsletterPublicImgSrc("linkedin.png")}?v=${FOOTER_SOCIAL_ICON_VERSION}`;

export const EVERNILE_CONTACT = {
  locations: "Gurugram | Ahmedabad",
  phone: "+91 8889926196",
  phoneHref: "tel:+918889926196",
  email: "contact@evernile.com",
  emailHref: "mailto:contact@evernile.com",
  whatsappHref: "https://wa.me/918889926196?text=",
  linkedinHref: "https://www.linkedin.com/company/evernile/",
} as const;
