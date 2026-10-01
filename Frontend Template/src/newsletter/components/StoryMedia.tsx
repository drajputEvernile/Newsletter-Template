import { cn } from "@/lib/utils";

const gradientLead =
  "absolute inset-0 bg-gradient-to-t from-background/35 via-background/5 to-transparent min-[621px]:bg-gradient-to-r min-[621px]:from-background/30 min-[621px]:via-transparent min-[621px]:to-transparent pointer-events-none";

type StoryMediaProps = {
  src: string;
  alt: string;
  className?: string;
};

/** Vertical centered template story image (621px breakpoint matches email renderer). */
export function StoryMedia({ src, alt, className }: StoryMediaProps) {
  const hasUrl = Boolean(src?.trim());

  return (
    <div className={cn("relative min-h-[128px] w-full overflow-hidden bg-muted/40", className)}>
      {hasUrl ? (
        <>
          <img
            src={src}
            alt={alt}
            className="absolute inset-0 h-full w-full object-cover"
            loading="lazy"
            width={800}
            height={512}
            decoding="async"
          />
          <div className={gradientLead} aria-hidden />
        </>
      ) : (
        <div className="absolute inset-0 flex items-center justify-center bg-muted/50" aria-hidden>
          <span className="text-[9px] font-semibold uppercase tracking-widest text-muted-foreground/45 select-none px-2 text-center">
            No image
          </span>
        </div>
      )}
    </div>
  );
}
