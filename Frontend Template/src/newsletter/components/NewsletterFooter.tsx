import {
  CENTERED_FOOTER_LOGO_SRC,
  EVERNILE_CONTACT,
  NEWSLETTER_FOOTER_LINKEDIN_ICON_SRC,
  NEWSLETTER_FOOTER_WHATSAPP_ICON_SRC,
} from "@/lib/brand";

const CENTERED_FOOTER_CONTACT_CLASS =
  "font-sans text-[12px] font-normal leading-[14px] text-[#6c7680]";
/** Mobile contact lines - keep in sync with `contact_line_mobile`. */
const CENTERED_FOOTER_CONTACT_MOBILE_CLASS =
  "font-sans text-[10px] font-normal leading-[14px] h-[14px] text-[#6c7680]";
/** The phone line runs 1px shorter, pulling the email line closer. */
const CENTERED_FOOTER_LINE_PHONE = "leading-[12px] h-[12px]";
const CENTERED_FOOTER_LEGAL_CLASS = "text-[7px] font-normal leading-[10px] text-[#a4abb4]";
/** Subtle gray strip behind the copyright line - keep in sync with `_CENTERED_FOOTER_STRIP_BG`. */
const CENTERED_FOOTER_STRIP_CLASS = "bg-[#e9eff4]";
/** 13px — keep in sync with `NEWSLETTER_FOOTER_SOCIAL_ICON_PX` / `_FOOTER_SOCIAL_ICON_PX`. */
const CENTERED_FOOTER_ICON_CLASS = "h-[13px] w-[13px] object-contain";

function CenteredFooterSeparator() {
  return <div className="centered-footer-separator" role="presentation" aria-hidden />;
}

function ContactFooterDesktop() {
  const separator = (
    <span
      className={`inline-flex items-center ${CENTERED_FOOTER_CONTACT_CLASS} text-[#6c7680]/40 leading-[14px]`}
    >
      ·
    </span>
  );
  const contactItemClass = `inline-flex items-center ${CENTERED_FOOTER_CONTACT_CLASS}`;
  const iconLinkClass = "inline-flex items-center justify-center leading-none hover:opacity-80";

  return (
    <div className="mt-4 hidden min-[621px]:flex flex-wrap items-center justify-center gap-x-2">
      <span className={contactItemClass}>{EVERNILE_CONTACT.locations}</span>
      {separator}
      <a href={EVERNILE_CONTACT.phoneHref} className={`${contactItemClass} hover:text-[#253246]`}>
        {EVERNILE_CONTACT.phone}
      </a>
      {separator}
      <a href={EVERNILE_CONTACT.emailHref} className={`${contactItemClass} hover:text-[#253246]`}>
        {EVERNILE_CONTACT.email}
      </a>
      {separator}
      <a
        href={EVERNILE_CONTACT.whatsappHref}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="WhatsApp"
        className={iconLinkClass}
      >
        <img src={NEWSLETTER_FOOTER_WHATSAPP_ICON_SRC} alt="" className={CENTERED_FOOTER_ICON_CLASS} />
      </a>
      {separator}
      <a
        href={EVERNILE_CONTACT.linkedinHref}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="LinkedIn"
        className={iconLinkClass}
      >
        <img src={NEWSLETTER_FOOTER_LINKEDIN_ICON_SRC} alt="" className={CENTERED_FOOTER_ICON_CLASS} />
      </a>
    </div>
  );
}

function ContactFooterMobile() {
  const itemClass = `inline-flex items-center ${CENTERED_FOOTER_CONTACT_MOBILE_CLASS}`;
  const iconLinkClass = "inline-flex items-center justify-center leading-none hover:opacity-80";

  return (
    <div className="mt-[10px] flex min-[621px]:hidden w-full max-w-full items-start justify-between gap-[6px]">
      <div className="flex min-w-0 flex-col items-start text-left">
        <span className={itemClass}>{EVERNILE_CONTACT.locations}</span>
        <a
          href={EVERNILE_CONTACT.phoneHref}
          className={`${itemClass} ${CENTERED_FOOTER_LINE_PHONE} hover:text-[#253246]`}
        >
          {EVERNILE_CONTACT.phone}
        </a>
        <a href={EVERNILE_CONTACT.emailHref} className={`${itemClass} hover:text-[#253246]`}>
          {EVERNILE_CONTACT.email}
        </a>
        <div className="flex items-center gap-x-[2px] whitespace-nowrap h-[14px]">
          <a
            href={EVERNILE_CONTACT.whatsappHref}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="WhatsApp"
            className={iconLinkClass}
          >
            <img src={NEWSLETTER_FOOTER_WHATSAPP_ICON_SRC} alt="" className={CENTERED_FOOTER_ICON_CLASS} />
          </a>
          <a
            href={EVERNILE_CONTACT.linkedinHref}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="LinkedIn"
            className={iconLinkClass}
          >
            <img src={NEWSLETTER_FOOTER_LINKEDIN_ICON_SRC} alt="" className={CENTERED_FOOTER_ICON_CLASS} />
          </a>
        </div>
      </div>
      <a
        href="https://newsletter.evernile.com/schedule-discussion"
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex shrink-0 items-center justify-center whitespace-nowrap rounded-[5px] bg-accent px-[8px] py-[4px] text-[11px] font-semibold leading-[14px] text-accent-foreground transition-opacity hover:opacity-90"
      >
        Connect with us
      </a>
    </div>
  );
}

/** Minimal footer for all centered templates (preview ↔ vertical centered reference). */
export default function NewsletterFooter() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full max-w-full min-w-0 box-border pb-[2px]">
      <div>
        {/* Desktop keeps the divider above the logo; mobile moves it below the sub-line. */}
        <div className="hidden min-[621px]:block">
          <CenteredFooterSeparator />
        </div>
        <div className="pt-[11px] min-[621px]:pt-5 text-center">
          <div className="inline-flex flex-col items-center gap-3">
            <img
              src={CENTERED_FOOTER_LOGO_SRC}
              alt="Evernile Capital"
              className="h-auto max-h-9 w-[88%] max-w-[132px] object-contain object-center"
              decoding="async"
            />
            <p className="max-w-md text-[10px] leading-[14px] min-[621px]:text-xs min-[621px]:leading-snug font-semibold text-[#253246]">
              We are an investment banking firm advising Indian enterprises across
              capital raises, M&amp;A, and strategic financial advisory.
            </p>
            <p className="-mt-[6px] max-w-md text-[9px] leading-[13px] min-[621px]:text-[11px] min-[621px]:leading-snug font-normal text-[#253246]">
              To learn more or start a conversation, connect with us below.
            </p>
            <a
              href="https://newsletter.evernile.com/schedule-discussion"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden min-[621px]:inline-flex items-center justify-center rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-accent-foreground transition-opacity hover:opacity-90"
            >
              Connect with us
            </a>
          </div>

          <div className="mt-3 w-full min-[621px]:hidden">
            <CenteredFooterSeparator />
          </div>

          <ContactFooterDesktop />
          <ContactFooterMobile />
        </div>
      </div>

      <div className="mt-5">
        <div className={`px-3 py-[1px] text-center ${CENTERED_FOOTER_STRIP_CLASS}`}>
          <a
            href="https://newsletter.evernile.com/unsubscribe"
            target="_blank"
            rel="noopener noreferrer"
            className={`inline-block ${CENTERED_FOOTER_LEGAL_CLASS} underline`}
          >
            Unsubscribe
          </a>
          <p className={`mt-[3px] mb-0 ${CENTERED_FOOTER_LEGAL_CLASS}`}>
            Copyright © {currentYear} Evernile. All Rights Reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
