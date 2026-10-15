import { useEffect, useState } from "react";
import { clampCount, getNewsletterData, MAX_NEWS_PER_SECTOR, SECTOR_ORDER } from "@/data/newsletterData";
import { LAYOUTS } from "@/newsletter/layouts";
import EmailPanel from "@/preview/EmailPanel";
import TopBar from "@/preview/TopBar";

const STORAGE_KEY = "newsletter-template:news-per-sector";

/** Parses "3" (all sectors) or "5,3,2,4" (one per sector, in sector order). */
function parseCounts(raw: string | null): number[] | null {
  if (!raw) return null;
  const parts = raw.split(",").map((p) => Number(p.trim()));
  if (parts.some((n) => !Number.isFinite(n))) return null;
  if (parts.length === 1) return SECTOR_ORDER.map(() => clampCount(parts[0]));
  if (parts.length !== SECTOR_ORDER.length) return null;
  return parts.map(clampCount);
}

/** Initial counts: `?news=` in the URL wins, then the last choice, then 5 everywhere. */
function initialCounts(): number[] {
  const fromUrl = parseCounts(new URLSearchParams(window.location.search).get("news"));
  if (fromUrl) return fromUrl;
  try {
    const fromStorage = parseCounts(window.localStorage.getItem(STORAGE_KEY));
    if (fromStorage) return fromStorage;
  } catch {
    /* storage unavailable */
  }
  return SECTOR_ORDER.map(() => MAX_NEWS_PER_SECTOR);
}

export default function App() {
  const [counts, setCounts] = useState(initialCounts);
  const [emailOpen, setEmailOpen] = useState(false);

  useEffect(() => {
    const value = counts.join(",");
    const url = new URL(window.location.href);
    url.searchParams.set("news", value);
    window.history.replaceState(null, "", url);
    try {
      window.localStorage.setItem(STORAGE_KEY, value);
    } catch {
      /* storage unavailable */
    }
  }, [counts]);

  // Uneven counts use the layout of the largest sector.
  const layoutCount = Math.max(...counts);
  const Layout = LAYOUTS[layoutCount].component;

  return (
    <div className="min-h-screen bg-[#eef4f8]">
      <TopBar counts={counts} onChange={setCounts} onEmail={() => setEmailOpen(true)} />
      <Layout data={getNewsletterData(counts)} />
      {emailOpen && <EmailPanel counts={counts} onClose={() => setEmailOpen(false)} />}
    </div>
  );
}
