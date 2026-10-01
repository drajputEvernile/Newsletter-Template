# Newsletter Frontend Template

Standalone UI kit for designing the **newsletter itself** (not the email renderer). It has its own
`package.json`, its own sample data and no backend dependency.

```bash
cd "Frontend Template"
npm install
npm run dev        # http://localhost:1001
```

## What you get

A top bar switches the format: **5 / 4 / 3 / 2 / 1 news per sector**, or **Custom**, where each of the 4 sectors gets its own count (1–5).
The choice is kept in the URL (`?news=3` for all sectors, `?news=5,3,2,4` for Healthcare, Consumer, BFSI, Technology) so a format can be linked or reloaded.

## Where to work

One layout file per news-per-sector count — redesign each freely, they are independent:

| News / sector | File |
| --- | --- |
| 1 | `src/newsletter/layouts/Layout1News.tsx` |
| 2 | `src/newsletter/layouts/Layout2News.tsx` |
| 3 | `src/newsletter/layouts/Layout3News.tsx` |
| 4 | `src/newsletter/layouts/Layout4News.tsx` |
| 5 | `src/newsletter/layouts/Layout5News.tsx` |

Every layout receives `data: NewsletterData` (`src/types.ts`) already trimmed to its count, so
`data.sectors[i].stories.length` equals the number in the file name. For an uneven Custom mix the layout of the *largest* sector is used, so other sectors may have fewer stories — layouts should map over `stories` rather than assume a fixed length. All five start as the current
production design; the saved design is simply the file in git.

Shared building blocks live in `src/newsletter/components/` (header, footer, shell, `SectorBlock`,
`StoryRow`, …). Editing a shared component changes every layout; copy it into your layout folder
if a design should only apply to one count. Styling is Tailwind plus the newsletter rules in
`src/index.css` (345 / 650 / 900px widths, breakpoints at 621px and 1024px — keep these, the email
uses the same ones).

## Not part of the newsletter

`src/App.tsx` and `src/preview/` are the preview harness only (top bar, `?news=` handling).
The deliverable is `src/newsletter/` + `src/types.ts`.

## Sample data

`src/data/newsletter.json` is a real daily summary (4 sectors) with 5 stories per sector.
Healthcare originally had 3 stories; its last two are marked `[Placeholder]`.
`getNewsletterData(n)` in `src/data/newsletterData.ts` is the single place that applies the count.

## Integration later

`LAYOUTS` in `src/newsletter/layouts/index.ts` maps news-per-sector → layout component, so the
backend side only needs `LAYOUTS[headlinesPerSector].component` with real data in the same
`NewsletterData` shape. To support more than 5, add a layout file, register it, and raise
`MAX_NEWS_PER_SECTOR` plus the sample data.
