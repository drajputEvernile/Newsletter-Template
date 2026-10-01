import NewsletterShell from "@/newsletter/components/NewsletterShell";
import SectorBlock from "@/newsletter/components/SectorBlock";
import type { NewsletterData } from "@/types";

/**
 * LAYOUT FOR NEWSLETTERS WITH 5 NEWS PER SECTOR.
 *
 * This file is for the frontend team to redesign: change the markup, swap SectorBlock for
 * a custom component, restyle with Tailwind. The other layouts are not affected.
 * `data.sectors[i].stories` holds 5 item(s) per sector. In Custom mode this layout is used
 * when the largest sector has 5 item(s), so other sectors may hold fewer.
 */
export default function Layout5News({ data }: { data: NewsletterData }) {
  return (
    <NewsletterShell mastheadDateLabel={data.mastheadDateLabel}>
      {data.sectors.map((sector) => (
        <SectorBlock key={sector.key} sector={sector} />
      ))}
    </NewsletterShell>
  );
}
