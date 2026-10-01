import type { ReactNode } from "react";
import NewsletterFooter from "@/newsletter/components/NewsletterFooter";
import NewsletterHeader from "@/newsletter/components/NewsletterHeader";
import { CENTERED_NEWSLETTER_SHELL_CLASS } from "@/lib/brand";

/**
 * Outer frame shared by every layout: soft background, centered 345 / 650 / 900px column,
 * masthead on top, footer at the bottom. Layouts only supply the `children` (the sectors).
 */
export default function NewsletterShell({
  mastheadDateLabel,
  children,
}: {
  mastheadDateLabel: string;
  children: ReactNode;
}) {
  return (
    <div className="newsletter-theme-locked bg-[#eef4f8] flex justify-center px-0 pt-3 pb-[6px] sm:pt-5 sm:pb-[10px]">
      <div className={CENTERED_NEWSLETTER_SHELL_CLASS}>
        <NewsletterHeader mastheadDateLabel={mastheadDateLabel} />
        <main className="w-full max-w-full min-w-0 box-border space-y-6 pt-6 pb-0 sm:space-y-8 sm:pt-8">
          {children}
        </main>
        <NewsletterFooter />
      </div>
    </div>
  );
}
