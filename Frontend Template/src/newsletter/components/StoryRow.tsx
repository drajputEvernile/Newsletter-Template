import { StoryMedia } from "@/newsletter/components/StoryMedia";
import { StorySummary } from "@/newsletter/components/StorySummary";
import { NEWSLETTER_STORY_HEADLINE_CLASS, NEWSLETTER_STORY_HEADLINE_LINK_CLASS } from "@/lib/brand";
import type { SectorContent, Story } from "@/types";

/** Story grid switches at 621px to match the email renderer (not Tailwind `lg`). */
const STORY_GRID = "grid grid-cols-1 min-[621px]:grid-cols-12 gap-0 border-t border-border first:border-t-0";
const STORY_MEDIA_COL = "min-[621px]:col-span-2 max-[620px]:pb-1 min-[621px]:min-h-full";
const STORY_BODY_COL = "min-[621px]:col-span-10 max-[620px]:pt-0 p-4 bg-card/80 flex flex-col justify-center";

/** One story: image on the left (top on mobile), headline + summary on the right. */
export default function StoryRow({ story, sector }: { story: Story; sector: SectorContent }) {
  const titleEl = story.url ? (
    <a href={story.url} target="_blank" rel="noopener noreferrer" className={NEWSLETTER_STORY_HEADLINE_LINK_CLASS}>
      {story.title}
    </a>
  ) : (
    <h3 className={NEWSLETTER_STORY_HEADLINE_CLASS}>{story.title}</h3>
  );

  return (
    <div className={`${STORY_GRID} min-w-0`}>
      <StoryMedia src={story.image || sector.image} alt={story.title} className={`${STORY_MEDIA_COL} min-w-0`} />
      <div className={`${STORY_BODY_COL} min-w-0`}>
        {titleEl}
        <div className="mt-2">
          <StorySummary story={story} size="sm" />
        </div>
      </div>
    </div>
  );
}
