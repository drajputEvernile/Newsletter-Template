# Newsletter Frontend Template

Standalone UI kit for designing the **newsletter itself** (not the email renderer). It has its own
`package.json`, its own sample data and no backend dependency.

```bash
cd "Frontend Template"
npm install
npm run dev        # UI on http://localhost:1001 + email server on 127.0.0.1:1002
```

The first `npm run dev` creates `server/.venv` and installs the email server's Python
dependencies (needs Python 3.10+). Run `npm run setup:mail` to do that step on its own.

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

## Send a test email

The **Send email** button in the top bar opens a popup: enter one or more addresses and the
current format (the counts selected in the top bar) is sent as a real email, one email per address,
through the Gmail API.

- Rendering and sending are the production code, unchanged: `server/pipeline/shared/email_renderer.py`,
  `gmail.py` and `newsletter_templates.py` are byte-for-byte copies of `backend/pipeline/shared/`
  (same layout, same subject, prefixed `[Testing]`, same one-email-per-recipient send).
  `config.py` and `utils.py` there are slim stand-ins for the backend ones.
- The React layouts in `src/newsletter/` do not change the email: the email is separate Python/table HTML.
  Email images load from `https://newsletter.evernile.com`, as in production. To change the email for a
  format, edit its layout file below.
- **Sender = folder name.** Put the mailbox's OAuth files in `server/credentials/<sender email>/`
  (`credentials.json` and `token.json`); that folder name is the From address. With several folders,
  set `GMAIL_SENDER_EMAIL` in `server/.env` to choose one, otherwise the first (alphabetical) is used.
- At most 10 recipients per send (`MAX_RECIPIENTS` in `server/.env`). `server/credentials/*` is git-ignored;
  these are real mailbox credentials, so share the folder only with people allowed to send as that mailbox.

## Email layouts (per news-per-sector count)

| News / sector | Email layout file |
| --- | --- |
| 1 | `server/email_layouts/layout_1.py` |
| 2 | `server/email_layouts/layout_2.py` |
| 3 | `server/email_layouts/layout_3.py` |
| 4 | `server/email_layouts/layout_4.py` |
| 5 | `server/email_layouts/layout_5.py` |

Each file has one function, `render_body(sectors_raw)`, returning the `<tr>` rows between the masthead and
footer. They all start identical to production. The send button renders with the layout matching the
largest sector (as with the React layouts), so changing `layout_3.py` shows up when you send a 3-news
format. Restart `npm run dev` after editing (the mail server does not auto-reload). Edit only these files:
`server/pipeline/shared/` stays an unmodified copy of the backend (helpers such as `_img_cover`, `_hl`,
`_bullets` can be imported from `pipeline.shared.email_renderer`).

### Porting an email layout to the main app
`npm run email:diff` shows what changed in `server/email_layouts/`. For each changed layout:
1. Copy its `render_body` into `backend/pipeline/shared/email_renderer.py` as e.g. `_render_vertical_3`.
2. Register it in `_RENDERERS` there under a new id (e.g. `"layout-3"`) and add that id to
   `SUPPORTED_TEMPLATE_IDS` in `backend/pipeline/shared/newsletter_templates.py`.
3. Where the backend renders a newsletter, choose the id from the largest sector's headline count
   (`email_layouts/__init__.py: render_email` shows the rule).

## Not part of the newsletter

`src/App.tsx`, `src/preview/` and `server/` are the preview harness only.
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
