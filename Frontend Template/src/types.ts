export type Story = {
  title: string;
  /** Summary bullets (two per story from the pipeline). */
  summaryPoints: string[];
  image: string;
  url: string;
  source: string;
  /** Display date shown under the summary. */
  sourceDate: string;
};

export type SectorContent = {
  key: string;
  label: string;
  /** Fallback image when a story has none. */
  image: string;
  stories: Story[];
};

/** Everything a layout needs to render one newsletter. */
export type NewsletterData = {
  mastheadDateLabel: string;
  sectors: SectorContent[];
};
