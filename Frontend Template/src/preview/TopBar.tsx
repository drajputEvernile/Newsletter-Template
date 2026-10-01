import { useState } from "react";
import { MAX_NEWS_PER_SECTOR, SECTOR_ORDER } from "@/data/newsletterData";
import { LAYOUT_COUNTS, LAYOUTS } from "@/newsletter/layouts";

type Props = {
  counts: number[];
  onChange: (counts: number[]) => void;
};

const btn = "rounded-md border px-3 py-1.5 text-sm font-medium transition-colors whitespace-nowrap";
const btnOn = "border-accent bg-accent text-accent-foreground";
const btnOff = "border-border bg-card text-foreground hover:bg-muted";

/** Preview-only toolbar. Not part of the newsletter — do not ship it. */
export default function TopBar({ counts, onChange }: Props) {
  const presets = [...LAYOUT_COUNTS].reverse();
  const uniform = counts.every((c) => c === counts[0]);
  const [customMode, setCustomMode] = useState(!uniform);
  // Raw text per sector so the field can be cleared while typing.
  const [drafts, setDrafts] = useState(counts.map(String));

  const setSector = (i: number, raw: string) => {
    setDrafts((d) => d.map((v, j) => (j === i ? raw : v)));
    const n = Number(raw);
    if (Number.isInteger(n) && n >= 1 && n <= MAX_NEWS_PER_SECTOR) {
      onChange(counts.map((c, j) => (j === i ? n : c)));
    }
  };

  return (
    <div className="sticky top-0 z-50 border-b border-border bg-card/95 backdrop-blur">
      <div className="flex flex-wrap items-center gap-2 px-4 py-3">
        <span className="mr-2 text-sm font-semibold text-foreground">Newsletter format</span>
        {presets.map((n) => (
          <button
            key={n}
            type="button"
            className={`${btn} ${!customMode && uniform && counts[0] === n ? btnOn : btnOff}`}
            onClick={() => {
              setCustomMode(false);
              setDrafts(SECTOR_ORDER.map(() => String(n)));
              onChange(SECTOR_ORDER.map(() => n));
            }}
          >
            {n} news/sector
          </button>
        ))}
        <button
          type="button"
          className={`${btn} ${customMode ? btnOn : btnOff}`}
          onClick={() => {
            setCustomMode(true);
            setDrafts(counts.map(String));
          }}
        >
          Custom
        </button>
        {customMode &&
          SECTOR_ORDER.map((label, i) => (
            <label key={label} className="flex items-center gap-1.5 text-sm text-muted-foreground">
              {label}
              <input
                type="number"
                min={1}
                max={MAX_NEWS_PER_SECTOR}
                value={drafts[i]}
                onChange={(e) => setSector(i, e.target.value)}
                className="w-14 rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground"
              />
            </label>
          ))}
        {customMode && <span className="text-xs text-muted-foreground">(1–{MAX_NEWS_PER_SECTOR} each)</span>}
        <span className="ml-auto text-xs text-muted-foreground">
          Editing: <code className="rounded bg-muted px-1.5 py-0.5">{LAYOUTS[Math.max(...counts)]?.file}</code>
        </span>
      </div>
    </div>
  );
}
