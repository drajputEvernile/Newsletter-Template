import type { ComponentType } from "react";
import type { NewsletterData } from "@/types";
import Layout1News from "./Layout1News";
import Layout2News from "./Layout2News";
import Layout3News from "./Layout3News";
import Layout4News from "./Layout4News";
import Layout5News from "./Layout5News";

export type LayoutComponent = ComponentType<{ data: NewsletterData }>;

/**
 * Layout registry, keyed by number of news per sector.
 * The backend integration later picks `LAYOUTS[headlinesPerSector]` to decide which one to render.
 */
export const LAYOUTS: Record<number, { component: LayoutComponent; file: string }> = {
  1: { component: Layout1News, file: "src/newsletter/layouts/Layout1News.tsx" },
  2: { component: Layout2News, file: "src/newsletter/layouts/Layout2News.tsx" },
  3: { component: Layout3News, file: "src/newsletter/layouts/Layout3News.tsx" },
  4: { component: Layout4News, file: "src/newsletter/layouts/Layout4News.tsx" },
  5: { component: Layout5News, file: "src/newsletter/layouts/Layout5News.tsx" },
};

/** Counts that have a layout, ascending. */
export const LAYOUT_COUNTS = Object.keys(LAYOUTS).map(Number).sort((a, b) => a - b);
