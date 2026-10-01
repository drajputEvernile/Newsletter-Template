import type { Story } from "@/types";
import { cn } from "@/lib/utils";

type Size = "xs" | "sm" | "base";

const sizeText: Record<Size, string> = {
  xs: "text-xs",
  sm: "text-sm",
  base: "text-base",
};

type SummaryBulletListProps = {
  points: string[];
  className?: string;
  size?: Size;
};

/** Renders summary lines (typically two) as a bullet list. */
export function SummaryBulletList({ points, className, size = "sm" }: SummaryBulletListProps) {
  const filtered = points.map((s) => (typeof s === "string" ? s.trim() : "")).filter(Boolean);
  if (!filtered.length) return null;
  return (
    <ul
      className={cn(
        "list-disc pl-4 space-y-1.5 marker:text-accent text-muted-foreground leading-relaxed",
        sizeText[size],
        className,
      )}
    >
      {filtered.map((text, i) => (
        <li key={i} className="font-sans">
          {text}
        </li>
      ))}
    </ul>
  );
}

const sourceDateText: Record<Size, string> = {
  xs: "text-[11px]",
  sm: "text-xs",
  base: "text-sm",
};

/** **Source** · date (scrape date when from JSON feed). */
export function StorySourceDateLine({ story, className, size = "sm" }: { story: Story; className?: string; size?: Size }) {
  const src = story.source?.trim() ?? "";
  const dt = story.sourceDate?.trim() ?? "";
  if (!src && !dt) return null;
  return (
    <p
      className={cn(
        "font-sans text-muted-foreground/90 flex flex-wrap items-center gap-x-2",
        sourceDateText[size],
        className,
      )}
    >
      {src ? <span className="font-bold text-inherit shrink-0">{src}</span> : null}
      {src && dt ? (
        <span
          className="flex shrink-0 items-center justify-center text-base font-bold leading-none text-inherit"
          aria-hidden
        >
          ·
        </span>
      ) : null}
      {dt ? <time className="shrink-0">{dt}</time> : null}
    </p>
  );
}

type StorySummaryProps = {
  story: Story;
  className?: string;
  size?: Size;
  /** When false, summary body only (no **Source** · date). Default true. */
  showSourceDate?: boolean;
};

/** Uses `summaryPoints` when present (JSON feed); otherwise falls back to a single paragraph from `dek`. Appends source · date when set. */
export function StorySummary({ story, className, size = "sm", showSourceDate = true }: StorySummaryProps) {
  const points = story.summaryPoints.filter((s) => s?.trim());
  const attribution =
    showSourceDate && (story.source?.trim() || story.sourceDate?.trim()) ? (
      <StorySourceDateLine story={story} size={size} className="mt-3" />
    ) : null;

  if (points?.length) {
    return (
      <>
        <SummaryBulletList points={points} className={className} size={size} />
        {attribution}
      </>
    );
  }
  if (attribution) {
    return <>{attribution}</>;
  }
  return null;
}
