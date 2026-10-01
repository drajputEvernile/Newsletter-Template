import {
  CENTERED_HEADER_ART,
  centeredHeaderDateOverlayStyle,
  centeredHeaderDateTypography,
} from "@/lib/brand";

type NewsletterHeaderProps = {
  mastheadDateLabel: string;
};

type CenteredArt = (typeof CENTERED_HEADER_ART)[keyof typeof CENTERED_HEADER_ART];

/** One masthead artboard — image + date overlay (parity with email_renderer). */
function CenteredMastheadBlock({
  art,
  blockClass,
  dateLabel,
}: {
  art: CenteredArt;
  blockClass: string;
  dateLabel: string;
}) {
  const dateBoxStyle = centeredHeaderDateOverlayStyle(art.w, art.h, art.dateBox);
  const dateTextStyle = centeredHeaderDateTypography(art.h);
  const naturalW = "naturalW" in art ? art.naturalW : undefined;
  const imgSrcSet =
    naturalW != null && naturalW > art.w ? `${art.src} ${naturalW}w` : undefined;
  const imgSizes = imgSrcSet ? `${art.w}px` : undefined;

  return (
    <div className={`centered-header-block ${blockClass}`}>
      <div
        className="centered-header-stage"
        style={{ aspectRatio: `${art.w} / ${art.h}` }}
      >
        <img
          src={art.src}
          srcSet={imgSrcSet}
          sizes={imgSizes}
          alt=""
          width={art.w}
          height={art.h}
          className="centered-header-stage-img"
          decoding="async"
          draggable={false}
        />
        <div className="centered-header-date-box" style={dateBoxStyle}>
          <span className="centered-header-date-text" style={dateTextStyle}>
            {dateLabel}
          </span>
        </div>
      </div>
    </div>
  );
}

const NewsletterHeader = ({ mastheadDateLabel }: NewsletterHeaderProps) => (
  <header className="w-full max-w-full min-w-0 box-border">
    <div className="centered-header-hero">
      <CenteredMastheadBlock
        art={CENTERED_HEADER_ART.desktop}
        blockClass="centered-header-block-d"
        dateLabel={mastheadDateLabel}
      />
      <CenteredMastheadBlock
        art={CENTERED_HEADER_ART.mobile}
        blockClass="centered-header-block-m"
        dateLabel={mastheadDateLabel}
      />
      <CenteredMastheadBlock
        art={CENTERED_HEADER_ART.tablet}
        blockClass="centered-header-block-t"
        dateLabel={mastheadDateLabel}
      />
    </div>
  </header>
);

export default NewsletterHeader;
