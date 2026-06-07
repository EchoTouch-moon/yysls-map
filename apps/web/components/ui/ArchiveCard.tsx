import Link from "next/link";
import type { ReactNode } from "react";

interface ArchiveCardProps {
  /** Numeric index displayed as "0N" accent label. */
  index: number;
  /** Card heading. */
  title: string;
  /** Card body text. */
  description: string;
  /** Link destination. */
  href: string;
  /** Optional trailing content rendered below the arrow. */
  children?: ReactNode;
}

/**
 * Linked feature card in the archival dossier style.
 *
 * Renders a full-area link (`<a>` wrapping the card) so the entire surface
 * is clickable, with keyboard focus visible via the standard outline.
 * The index is prefixed with "0" for single digits to match the卷宗 aesthetic.
 */
export function ArchiveCard({
  index,
  title,
  description,
  href,
  children,
}: ArchiveCardProps) {
  return (
    <Link
      href={href}
      className="group flex flex-col border-b border-[var(--line)] p-8 transition hover:bg-[rgba(232,223,198,.05)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[var(--cinnabar-bright)] md:border-b-0 md:border-r md:last:border-r-0 lg:p-12"
    >
      <span className="text-xs text-[var(--cinnabar-bright)]" aria-hidden="true">
        {String(index + 1).padStart(2, "0")}
      </span>
      <h3 className="mt-8 text-2xl tracking-[0.12em]">{title}</h3>
      <p className="mt-4 text-sm leading-7 text-[var(--fog)]">{description}</p>
      {children}
      <span className="mt-8 block text-sm transition group-hover:translate-x-2" aria-hidden="true">
        进入 →
      </span>
    </Link>
  );
}

interface ArchiveCardListProps {
  entries: ReadonlyArray<{
    title: string;
    description: string;
    href: string;
  }>;
  className?: string;
}

/**
 * Renders a responsive grid of `ArchiveCard` items.
 *
 * The outer wrapper provides the border/background treatment that
 * previously lived inline on the home page.
 */
export function ArchiveCardList({ entries, className = "" }: ArchiveCardListProps) {
  return (
    <section className={`border-y border-[var(--line)] bg-[rgba(232,223,198,.035)] ${className}`}>
      <div className="mx-auto grid max-w-[1500px] md:grid-cols-3">
        {entries.map((entry, index) => (
          <ArchiveCard
            key={entry.href}
            index={index}
            title={entry.title}
            description={entry.description}
            href={entry.href}
          />
        ))}
      </div>
    </section>
  );
}
