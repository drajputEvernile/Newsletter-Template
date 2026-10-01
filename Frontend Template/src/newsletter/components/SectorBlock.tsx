import StoryRow from "@/newsletter/components/StoryRow";
import type { SectorContent } from "@/types";

/** One sector card: label bar + its stories. */
export default function SectorBlock({ sector }: { sector: SectorContent }) {
  return (
    <section className="w-full max-w-full min-w-0 box-border rounded-2xl border border-border bg-highlight-ice overflow-hidden">
      <div className="px-5 py-3 border-b border-border bg-highlight-mid/40">
        <span className="text-xs font-bold uppercase tracking-widest text-accent">{sector.label}</span>
      </div>
      <div>
        {sector.stories.map((story, i) => (
          <StoryRow key={`${i}-${story.url || story.title}`} story={story} sector={sector} />
        ))}
      </div>
    </section>
  );
}
