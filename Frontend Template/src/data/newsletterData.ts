import type { NewsletterData, SectorContent, Story } from "@/types";
import raw from "./newsletter.json";

/** The sample data holds this many stories per sector — the maximum a layout can ask for. */
export const MAX_NEWS_PER_SECTOR = 5;

/** Display order of sectors in the newsletter. */
export const SECTOR_ORDER = ["Healthcare", "Consumer", "BFSI", "Technology"];

type RawArticle = {
  headline: string;
  url: string;
  image_url: string;
  source: string;
  Scrape_date: string;
  priority_rank: number;
  summary_1: string;
  summary_2: string;
};

function toStory(a: RawArticle): Story {
  return {
    title: a.headline,
    summaryPoints: [a.summary_1, a.summary_2].filter(Boolean),
    image: a.image_url,
    url: a.url,
    source: a.source,
    sourceDate: a.Scrape_date,
  };
}

function formatMastheadDate(iso: string): string {
  const d = new Date(`${iso}T12:00:00`);
  const weekday = new Intl.DateTimeFormat("en-US", { weekday: "long" }).format(d);
  const date = new Intl.DateTimeFormat("en-US", { month: "long", day: "numeric", year: "numeric" }).format(d);
  return `${weekday} · ${date}`;
}

const FULL_SECTORS: SectorContent[] = SECTOR_ORDER.map((label) => {
  const articles = [...((raw.sectors as Record<string, RawArticle[]>)[label] ?? [])].sort(
    (a, b) => a.priority_rank - b.priority_rank,
  );
  const stories = articles.map(toStory);
  return { key: label.toLowerCase(), label, image: stories[0]?.image ?? "", stories };
});

export function clampCount(n: number): number {
  return Math.max(1, Math.min(MAX_NEWS_PER_SECTOR, Math.floor(n) || 1));
}

/**
 * Newsletter with a story count per sector, in `SECTOR_ORDER` (each clamped to 1–5).
 * A single number applies to every sector. This is the only place counts are applied —
 * layouts just render the stories they get.
 */
export function getNewsletterData(perSector: number | number[]): NewsletterData {
  return {
    mastheadDateLabel: formatMastheadDate(raw.summary_date),
    sectors: FULL_SECTORS.map((s, i) => ({
      ...s,
      stories: s.stories.slice(0, clampCount(Array.isArray(perSector) ? (perSector[i] ?? 1) : perSector)),
    })),
  };
}
