export type EvidenceSourceType =
  | "player_note"
  | "quest_reference"
  | "official_reference"
  | "community_analysis";

export type EvidenceSource = {
  source_type: EvidenceSourceType;
  title: string;
  reference: string | null;
};

const SOURCE_TYPE_LABELS: Record<EvidenceSourceType, string> = {
  player_note: "玩家亲历",
  quest_reference: "任务定位",
  official_reference: "官方资料",
  community_analysis: "社区整理",
};

function safeHttpReference(reference: string | null): string | null {
  if (!reference) return null;
  try {
    const parsed = new URL(reference);
    return parsed.protocol === "http:" || parsed.protocol === "https:"
      ? parsed.toString()
      : null;
  } catch {
    return null;
  }
}

export function EvidenceList({
  sources,
  className = "",
}: {
  sources?: readonly EvidenceSource[];
  className?: string;
}) {
  if (!sources?.length) return null;

  return (
    <details className={`border-t border-[var(--line)] pt-4 ${className}`}>
      <summary className="cursor-pointer text-xs tracking-[0.16em] text-[var(--fog)] transition hover:text-[var(--paper)]">
        资料来源（{sources.length}）
      </summary>
      <p className="mt-3 text-xs leading-5 text-[var(--fog)]">
        外部页面可能包含超出当前进度的内容，请确认后再打开。
      </p>
      <ol className="mt-4 grid gap-4">
        {sources.map((source, index) => {
          const href = safeHttpReference(source.reference);
          return (
            <li
              key={`${source.source_type}:${source.reference ?? source.title}:${index}`}
              className="border-l border-[var(--line)] pl-4"
            >
              <p className="text-[10px] tracking-[0.14em] text-[var(--cinnabar-bright)]">
                {SOURCE_TYPE_LABELS[source.source_type]}
              </p>
              {href ? (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1 inline-block text-sm leading-6 text-[var(--paper-light)] underline decoration-[var(--line-strong)] underline-offset-4 hover:decoration-[var(--paper)]"
                >
                  {source.title}
                </a>
              ) : (
                <p className="mt-1 text-sm leading-6 text-[var(--paper-light)]">
                  {source.title}
                </p>
              )}
            </li>
          );
        })}
      </ol>
    </details>
  );
}
