import type { ReactNode } from "react";

interface SectionHeadingProps {
  /** Eyebrow text displayed above the heading in cinnabar accent. */
  eyebrow?: string;
  /** Main heading content. */
  children: ReactNode;
  /** Optional subtitle or description below the heading. */
  description?: ReactNode;
  /** HTML heading level. Defaults to `2`. */
  level?: 1 | 2 | 3;
  /** Additional class names applied to the outer wrapper. */
  className?: string;
  /** Custom class name applied to the heading element. */
  headingClassName?: string;
}

/**
 * Dossier-style section heading with optional eyebrow and description.
 *
 * Preserves the archival serif aesthetic — tracking, muted palette,
 * cinnabar accent on the eyebrow line.
 */
export function SectionHeading({
  eyebrow,
  children,
  description,
  level = 2,
  className = "",
  headingClassName = "",
}: SectionHeadingProps) {
  const Tag = `h${level}` as const;

  return (
    <div className={className}>
      {eyebrow && (
        <p className="mb-7 text-xs tracking-[0.35em] text-[var(--cinnabar-bright)]">
          {eyebrow}
        </p>
      )}
      <Tag className={`max-w-3xl font-semibold leading-[1.22] tracking-[0.04em] ${headingClassName || "text-5xl md:text-7xl"}`}>
        {children}
      </Tag>
      {description && (
        <p className="mt-8 max-w-xl text-base leading-8 text-[var(--fog)]">
          {description}
        </p>
      )}
    </div>
  );
}
