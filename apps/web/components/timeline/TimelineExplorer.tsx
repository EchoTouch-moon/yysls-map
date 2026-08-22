"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useProgress } from "@/components/ui/ProgressSelect";
import { EvidenceList, type EvidenceSource } from "@/components/ui/EvidenceList";
import { apiFetch } from "@/lib/http";

type TimelineEvent = {
  id: string;
  slug: string;
  title: string;
  summary: string;
  impact: string | null;
  chapter_slug: string;
  chapter_title: string;
  sort_order: number;
  characters: { slug: string; name: string }[];
  sources?: EvidenceSource[];
};

type TimelineData = { progress: string; events: TimelineEvent[] };

type HistoricalReference = {
  reference_type: string;
  title: string;
  publisher?: string | null;
  url: string | null;
  locator?: string | null;
};

type HistoricalContext = {
  id: string;
  slug: string;
  title: string;
  summary: string;
  fact_kind: string;
  relation_kind: string;
  boundary_note: string;
  editorial_note: string | null;
  period_label?: string | null;
  references: HistoricalReference[];
};

type BeatRelationship = {
  id: string;
  relation_type: string;
  label: string;
  source_slug: string;
  source_name: string;
  target_slug: string;
  target_name: string;
};

type CanonicalEventBeatOverlay = {
  role: string;
  guide: string;
  why_it_matters: string;
  bridge: string;
  next_question: string;
};

type CanonicalEventOverlay = {
  mapping_kind: "exact" | "merged" | "split" | null;
  slug: string;
  title: string;
  summary: string;
  impact: string | null;
  chapter_slug: string;
  chapter_title: string;
  characters: { slug: string; name: string }[];
  sources: EvidenceSource[];
  relationships: BeatRelationship[];
  historical_contexts: HistoricalContext[];
  beat: CanonicalEventBeatOverlay | null;
};

type CanonicalNodeRead = {
  canonical_key: string;
  title: string;
  node_type: "chapter" | "main_part" | "main_quest";
  parent_key: string | null;
  sort_order: number;
  events: CanonicalEventOverlay[];
};

type TimelineCanonicalData = {
  progress: string;
  chapter: { slug: string; title: string; region: string | null } | null;
  chapter_unlocked: boolean;
  spine: CanonicalNodeRead[];
  beat_index: Record<string, string[]>;
  unplaced_events: CanonicalEventOverlay[];
};

type TimelineMode = "guide" | "events";

const FACT_KIND_LABELS: Record<string, string> = {
  work_fact: "作品事实",
  historical_fact: "历史事实",
  credible_parallel: "可信对照",
  editorial_inference: "编辑推测",
};

const RELATION_KIND_LABELS: Record<string, string> = {
  setting: "时代背景",
  inspired_by: "可能借鉴",
  parallel: "主题对照",
  contrast: "对照阅读",
  fictionalized: "虚构改写",
};

const REFERENCE_TYPE_LABELS: Record<string, string> = {
  primary_source: "一手史料",
  scholarly_research: "学术研究",
  institutional_reference: "机构资料",
};

function labelFor(labels: Record<string, string>, value: string): string {
  return labels[value] ?? value;
}

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

/**
 * Progress keys intentionally remount the whole interactive surface. This
 * makes a lowered spoiler threshold discard guide and history content before
 * the next filtered API response can arrive.
 */
export function TimelineExplorer() {
  const progress = useProgress();
  return <TimelineForProgress key={progress} progress={progress} />;
}

function TimelineForProgress({ progress }: { progress: string }) {
  const [mode, setMode] = useState<TimelineMode>("guide");

  const activateMode = (nextMode: TimelineMode, moveFocus = false) => {
    setMode(nextMode);
    if (moveFocus) {
      requestAnimationFrame(() => {
        document.getElementById(`${nextMode}-timeline-tab`)?.focus();
      });
    }
  };

  const handleTabKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    const modes: readonly TimelineMode[] = ["guide", "events"];
    const currentIndex = modes.indexOf(mode);
    let nextIndex: number | null = null;

    if (event.key === "ArrowRight") nextIndex = (currentIndex + 1) % modes.length;
    if (event.key === "ArrowLeft") nextIndex = (currentIndex - 1 + modes.length) % modes.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = modes.length - 1;
    if (nextIndex === null) return;

    event.preventDefault();
    activateMode(modes[nextIndex], true);
  };

  return (
    <section className="mt-10" aria-label="剧情阅读方式">
      <div className="border-y border-[var(--line)] py-4">
        <div role="tablist" aria-label="时间线阅读模式" className="flex flex-wrap gap-2">
          <ModeButton
            active={mode === "guide"}
            id="guide-timeline-tab"
            onClick={() => activateMode("guide")}
            onKeyDown={handleTabKeyDown}
            controls="story-guide-panel"
          >
            跟着故事读
          </ModeButton>
          <ModeButton
            active={mode === "events"}
            id="events-timeline-tab"
            onClick={() => activateMode("events")}
            onKeyDown={handleTabKeyDown}
            controls="full-events-panel"
          >
            完整事件
          </ModeButton>
        </div>
        <p className="pt-3 text-xs leading-5 text-[var(--fog)]">
          主线按游戏原生故事顺序连续展开，滚动即阅读；点击只用于深入解析。
        </p>
      </div>

      {mode === "guide" ? (
        <CanonicalGuide key={`guide:${progress}`} progress={progress} />
      ) : (
        <EventTimeline key={`events:${progress}`} progress={progress} />
      )}
    </section>
  );
}

function ModeButton({
  active,
  children,
  controls,
  id,
  onClick,
  onKeyDown,
}: {
  active: boolean;
  children: React.ReactNode;
  controls: string;
  id: string;
  onClick: () => void;
  onKeyDown: (event: React.KeyboardEvent<HTMLButtonElement>) => void;
}) {
  return (
    <button
      type="button"
      role="tab"
      id={id}
      aria-selected={active}
      aria-controls={controls}
      tabIndex={active ? 0 : -1}
      onClick={onClick}
      onKeyDown={onKeyDown}
      className={`border px-4 py-2 text-sm tracking-[0.12em] transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)] ${
        active
          ? "border-[var(--cinnabar-bright)] bg-[rgba(143,47,37,.16)] text-[var(--paper-light)]"
          : "border-[var(--line)] text-[var(--fog)] hover:border-[var(--paper)] hover:text-[var(--paper)]"
      }`}
    >
      {children}
    </button>
  );
}

function CanonicalGuide({ progress }: { progress: string }) {
  const [data, setData] = useState<TimelineCanonicalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const searchParams = useMemo(
    () => (typeof window === "undefined" ? null : new URLSearchParams(window.location.search)),
    [],
  );
  const deepLinkNode = searchParams?.get("node") ?? null;
  const deepLinkBeat = searchParams?.get("beat") ?? null;

  useEffect(() => {
    let active = true;
    const params = new URLSearchParams({ progress });
    apiFetch<TimelineCanonicalData>(`/timeline/canonical?${params}`)
      .then((response) => {
        if (active) setData(response.data ?? null);
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "主线导读读取失败。");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [progress]);

  // Deep-link resolution: ?node= or ?beat= (old compatibility bridge, D-G6).
  useEffect(() => {
    if (!data || (!deepLinkNode && !deepLinkBeat)) return;
    let targetKey: string | null = null;
    if (deepLinkNode) {
      targetKey = deepLinkNode;
    } else if (deepLinkBeat && data.beat_index[deepLinkBeat]?.length) {
      targetKey = data.beat_index[deepLinkBeat][0];
    }
    if (!targetKey) return;
    const id = `canonical-${targetKey}`;
    const frame = requestAnimationFrame(() => {
      const element = document.getElementById(id);
      if (!element) return;
      element.scrollIntoView({ behavior: "smooth", block: "start" });
      // imperative highlight (no state) so the effect stays lint-clean
      element.style.outline = "2px solid var(--cinnabar-bright)";
      element.style.outlineOffset = "2px";
      window.setTimeout(() => {
        element.style.outline = "";
        element.style.outlineOffset = "";
      }, 2600);
    });
    return () => cancelAnimationFrame(frame);
  }, [data, deepLinkNode, deepLinkBeat]);

  const locked = !data || !data.chapter_unlocked || !data.chapter;
  const pendingUnplacedBeat =
    !locked && deepLinkBeat && !data.beat_index[deepLinkBeat]
      ? data.unplaced_events.find((event) => event.slug === deepLinkBeat) ?? null
      : null;

  return (
    <div
      id="story-guide-panel"
      role="tabpanel"
      aria-labelledby="guide-timeline-tab"
      className="mt-8 min-w-0"
    >
      {loading && <StatusCard>正在展开故事卷轴…</StatusCard>}
      {error && <StatusCard role="alert">{error}</StatusCard>}
      {!loading && !error && !data && <StatusCard>当前进度暂无可公开导读。</StatusCard>}

      {!loading && !error && locked && (
        <StatusCard>
          <p className="text-xs tracking-[0.22em] text-[var(--cinnabar-bright)]">
            {data?.chapter?.title ?? "本章"}
          </p>
          <p className="mt-4 text-sm leading-7">完成本章主线后解锁连续故事导读。</p>
        </StatusCard>
      )}

      {!loading && !error && data && data.chapter && !locked && (
        <>
          <CanonicalMasthead title={data.chapter.title} progress={data.progress} />

          {pendingUnplacedBeat && (
            <UnplacedEventCard
              event={pendingUnplacedBeat}
              note="该事件是编辑解析节点，尚未挂载到游戏原生主线。"
            />
          )}

          <ol className="relative mt-8" aria-label="游戏原生主线">
            {data.spine.map((node) => (
              <li key={node.canonical_key}>
                <CanonicalNodeCard node={node} />
              </li>
            ))}
          </ol>
        </>
      )}
    </div>
  );
}

function CanonicalMasthead({ title, progress }: { title: string; progress: string }) {
  return (
    <header className="archive-frame relative overflow-hidden px-6 py-7 sm:px-9 sm:py-9">
      <span className="absolute right-8 top-7 hidden text-7xl leading-none text-[rgba(192,74,54,.12)] sm:block" aria-hidden="true">卷</span>
      <p className="text-xs tracking-[0.26em] text-[var(--cinnabar-bright)]">游戏原生主线 · 清河</p>
      <h2 className="mt-3 max-w-3xl text-3xl leading-tight text-[var(--paper-light)] sm:text-4xl">{title}</h2>
      <p className="mt-5 max-w-3xl leading-8 text-[var(--fog)]">
        沿游戏中的原生任务顺序连续阅读：滚动前进，点击深入。人物、暗线、历史与完整解析都从主线节点展开。
      </p>
      <p className="mt-4 text-xs tracking-[0.14em] text-[var(--fog)]">当前进度：{progress}</p>
    </header>
  );
}

function CanonicalNodeCard({ node }: { node: CanonicalNodeRead }) {
  const [expanded, setExpanded] = useState(false);
  const primaryEvent = node.events[0] ?? null;

  if (node.node_type === "main_part") {
    return (
      <section
        id={`canonical-${node.canonical_key}`}
        data-canonical-key={node.canonical_key}
        aria-label={`篇：${node.title}`}
        className="mt-10 border-b border-[var(--line)] pb-4 transition"
      >
        <p className="text-xs tracking-[0.24em] text-[var(--cinnabar-bright)]">篇</p>
        <h3 className="mt-2 text-2xl leading-snug text-[var(--paper-light)]">{node.title}</h3>
      </section>
    );
  }

  if (node.node_type === "chapter") {
    return null;
  }

  return (
    <article
      id={`canonical-${node.canonical_key}`}
      data-canonical-key={node.canonical_key}
      aria-label={`剧情节点：${node.title}`}
      className="archive-frame relative mt-6 min-w-0 overflow-hidden p-6 transition sm:p-8"
    >
      <p className="text-xs tracking-[0.2em] text-[var(--cinnabar-bright)]">游戏主线节点</p>
      <h4 className="mt-2 text-2xl leading-snug text-[var(--paper-light)]">{node.title}</h4>

      {primaryEvent ? (
        <>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-[var(--paper)]">{primaryEvent.summary}</p>
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            aria-expanded={expanded}
            className="mt-5 inline-flex items-center gap-2 border border-[var(--line)] px-4 py-2 text-xs tracking-[0.14em] text-[var(--paper)] transition hover:border-[var(--paper)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
          >
            {expanded ? "收起解析 −" : "这里为什么重要 →"}
          </button>
        </>
      ) : (
        <p className="mt-4 max-w-3xl text-sm leading-7 text-[var(--fog)]">
          当前还没有整理这一段的完整剧情解析。
        </p>
      )}

      {expanded && primaryEvent && (
        <div className="mt-6 border-t border-[var(--line)] pt-5">
          <CanonicalOverlay event={primaryEvent} />
        </div>
      )}
    </article>
  );
}

function CanonicalOverlay({ event }: { event: CanonicalEventOverlay }) {
  const label = event.mapping_kind
    ? { exact: "一一对应", merged: "合并对应", split: "拆分对应" }[event.mapping_kind]
    : null;
  return (
    <div className="grid gap-5 text-sm leading-7">
      {label && (
        <p className="text-[10px] tracking-[0.16em] text-[var(--fog)]">
          事件对应：{label}（{event.title}）
        </p>
      )}

      {event.beat && (
        <div className="grid gap-5 border-b border-[var(--line)] pb-5 sm:grid-cols-2">
          <ReadingNote label="为什么重要">{event.beat.why_it_matters}</ReadingNote>
          <ReadingNote label="这一节发生了什么">{event.beat.guide}</ReadingNote>
          <ReadingNote label="与上一节的承接">{event.beat.bridge}</ReadingNote>
          <ReadingNote label="带着这个问题读下去" cinnabar>{event.beat.next_question}</ReadingNote>
        </div>
      )}

      {event.impact && (
        <p className="border-l border-[var(--cinnabar)] pl-4 text-[var(--paper)]">{event.impact}</p>
      )}

      {event.characters.length > 0 && (
        <div>
          <p className="text-[10px] tracking-[0.18em] text-[var(--fog)]">本节人物</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {event.characters.map((character) => (
              <Link
                key={character.slug}
                href={`/characters/${character.slug}`}
                className="border border-[var(--line)] px-3 py-1.5 text-xs text-[var(--paper)] transition hover:border-[var(--paper)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
              >
                {character.name}
              </Link>
            ))}
          </div>
        </div>
      )}

      {event.relationships.length > 0 && (
        <section aria-label="本节相关关系">
          <p className="text-[10px] tracking-[0.18em] text-[var(--fog)]">本节相关关系</p>
          <ul className="mt-3 flex flex-wrap gap-2">
            {event.relationships.map((relationship) => (
              <li key={relationship.id} className="flex items-center gap-2 border border-[var(--line)] px-3 py-1.5 text-xs text-[var(--paper)]">
                <Link href={`/characters/${relationship.source_slug}`} className="hover:text-[var(--paper-light)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]">
                  {relationship.source_name}
                </Link>
                <span className="text-[var(--cinnabar-bright)]">—{relationship.label}→</span>
                <Link href={`/characters/${relationship.target_slug}`} className="hover:text-[var(--paper-light)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]">
                  {relationship.target_name}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      <HistoricalContextList contexts={event.historical_contexts} />
      <EvidenceList sources={event.sources} className="max-w-3xl" />
    </div>
  );
}

function UnplacedEventCard({
  event,
  note,
}: {
  event: CanonicalEventOverlay;
  note: string;
}) {
  return (
    <article className="archive-frame relative mt-6 min-w-0 overflow-hidden border-l-2 border-l-[var(--cinnabar)] p-6 sm:p-8">
      <p className="text-xs tracking-[0.2em] text-[var(--cinnabar-bright)]">编辑解析节点</p>
      <h3 className="mt-2 text-2xl leading-snug text-[var(--paper-light)]">{event.title}</h3>
      <p className="mt-3 max-w-3xl text-xs leading-6 text-[var(--fog)]">{note}</p>
      <div className="mt-5">
        <CanonicalOverlay event={event} />
      </div>
    </article>
  );
}

function ReadingNote({ label, children, cinnabar = false }: { label: string; children: React.ReactNode; cinnabar?: boolean }) {
  return (
    <div>
      <p className={`text-[10px] tracking-[0.18em] ${
        cinnabar ? "text-[var(--cinnabar-bright)]" : "text-[var(--fog)]"
      }`}>{label}</p>
      <p className="mt-2 text-[var(--paper)]">{children}</p>
    </div>
  );
}

function HistoricalContextList({ contexts }: { contexts: HistoricalContext[] }) {
  if (!contexts.length) return null;

  return (
    <section className="mt-7 border-t border-[var(--line)] pt-5" aria-label="相关历史背景">
      <p className="text-xs tracking-[0.18em] text-[var(--cinnabar-bright)]">相关历史背景</p>
      <p className="mt-3 max-w-3xl text-xs leading-6 text-[var(--fog)]">作品叙事与史实不等同；下列卡片说明可核背景及其与作品的关联边界。</p>
      <div className="mt-4 grid gap-3">
        {contexts.map((context) => <HistoricalContextCard key={context.slug} context={context} />)}
      </div>
    </section>
  );
}

function HistoricalContextCard({ context }: { context: HistoricalContext }) {
  return (
    <details className="group border border-[var(--line)] bg-[rgba(21,19,15,.44)]">
      <summary className="cursor-pointer list-none px-4 py-4 transition hover:bg-[rgba(217,201,164,.035)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[var(--cinnabar-bright)]">
        <span className="flex items-start justify-between gap-4">
          <span>
            <span className="block text-sm text-[var(--paper-light)]">{context.title}</span>
            <span className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[10px] tracking-[0.12em] text-[var(--fog)]">
              <span>{labelFor(FACT_KIND_LABELS, context.fact_kind)}</span>
              <span>{labelFor(RELATION_KIND_LABELS, context.relation_kind)}</span>
              <span>{context.period_label ?? "时代待核"}</span>
            </span>
          </span>
          <span className="text-[var(--cinnabar-bright)] transition group-open:rotate-45" aria-hidden="true">＋</span>
        </span>
      </summary>
      <div className="border-t border-[var(--line)] px-4 py-5 text-sm leading-7 text-[var(--fog)]">
        <dl className="mb-4 grid gap-2 text-xs sm:grid-cols-3">
          <div><dt className="text-[10px] tracking-[0.16em] text-[var(--fog)]">事实类型</dt><dd className="mt-1 text-[var(--paper)]">{labelFor(FACT_KIND_LABELS, context.fact_kind)}</dd></div>
          <div><dt className="text-[10px] tracking-[0.16em] text-[var(--fog)]">关联性质</dt><dd className="mt-1 text-[var(--paper)]">{labelFor(RELATION_KIND_LABELS, context.relation_kind)}</dd></div>
          <div><dt className="text-[10px] tracking-[0.16em] text-[var(--fog)]">时代</dt><dd className="mt-1 text-[var(--paper)]">{context.period_label ?? "尚待来源标注"}</dd></div>
        </dl>
        <p>{context.summary}</p>
        <p className="mt-4 border-l border-[var(--cinnabar)] pl-4 text-[var(--paper)]">{context.boundary_note}</p>
        {context.editorial_note && <p className="mt-3 text-xs leading-6 text-[var(--fog)]">编辑说明：{context.editorial_note}</p>}
        <HistoricalReferenceList references={context.references} />
        <Link
          href={`/history/${context.slug}`}
          className="mt-5 inline-block text-xs text-[var(--cinnabar-bright)] underline decoration-[var(--line-strong)] underline-offset-4 hover:text-[var(--paper-light)]"
        >
          查看完整历史背景 →
        </Link>
      </div>
    </details>
  );
}

function HistoricalReferenceList({ references }: { references: HistoricalReference[] }) {
  if (!references.length) return null;
  return (
    <section className="mt-5 border-t border-[var(--line)] pt-4" aria-label="独立历史来源">
      <p className="text-[10px] tracking-[0.18em] text-[var(--fog)]">独立历史来源</p>
      <ol className="mt-3 grid gap-3">
        {references.map((source, index) => {
          const href = safeHttpReference(source.url);
          return (
            <li key={`${source.reference_type}:${source.url ?? source.title}:${index}`} className="border-l border-[var(--line)] pl-3 text-xs">
              <p className="text-[10px] tracking-[0.14em] text-[var(--cinnabar-bright)]">{labelFor(REFERENCE_TYPE_LABELS, source.reference_type)}</p>
              {source.publisher && <p className="mt-1 text-[var(--fog)]">{source.publisher}</p>}
              {href ? (
                <a href={href} target="_blank" rel="noopener noreferrer" className="mt-1 inline-block text-[var(--paper-light)] underline decoration-[var(--line-strong)] underline-offset-4 hover:decoration-[var(--paper)]">{source.title}</a>
              ) : (
                <p className="mt-1 text-[var(--paper-light)]">{source.title}</p>
              )}
              {source.locator && <p className="mt-1 text-[var(--fog)]">定位：{source.locator}</p>}
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function EventTimeline({ progress }: { progress: string }) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [chapter, setChapter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const params = new URLSearchParams({ progress });
    apiFetch<TimelineData>(`/timeline?${params}`)
      .then((response) => {
        if (active) setEvents(response.data?.events ?? []);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "时间线读取失败。");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [progress]);

  const chapters = useMemo(() => Array.from(new Map(events.map((event) => [event.chapter_slug, event.chapter_title]))), [events]);
  const visibleEvents = chapter ? events.filter((event) => event.chapter_slug === chapter) : events;

  return (
    <div
      id="full-events-panel"
      role="tabpanel"
      aria-labelledby="events-timeline-tab"
      className="mt-8"
    >
      <div className="flex flex-wrap items-center justify-between gap-4 border-y border-[var(--line)] py-4">
        <p className="text-xs tracking-[0.16em] text-[var(--fog)]">当前仅显示进度范围内的公开事件</p>
        <label className="text-xs text-[var(--fog)]">
          章节
          <select value={chapter} onChange={(event) => setChapter(event.target.value)} className="ml-3 border border-[var(--line)] bg-[var(--ink)] px-3 py-2 text-[var(--paper)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]">
            <option value="">全部可见章节</option>
            {chapters.map(([slug, title]) => <option key={slug} value={slug}>{title}</option>)}
          </select>
        </label>
      </div>

      {loading && <StatusCard>正在整理事件次序…</StatusCard>}
      {error && <StatusCard role="alert">{error}</StatusCard>}
      {!loading && !error && visibleEvents.length === 0 && <StatusCard>当前进度暂无可公开事件。</StatusCard>}

      <ol className="relative mt-8 border-l border-[var(--line)] pl-8 animate-text-fade-in">
        {visibleEvents.map((event) => (
          <li key={event.id} className="relative mb-10">
            <span className="absolute -left-[2.3rem] top-1 size-3 border border-[var(--cinnabar-bright)] bg-[var(--ink)]" />
            <p className="text-xs tracking-[0.16em] text-[var(--cinnabar-bright)]">{event.chapter_title} · {String(event.sort_order).padStart(2, "0")}</p>
            <h2 className="mt-3 text-2xl">{event.title}</h2>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-[var(--fog)]">{event.summary}</p>
            {event.impact && <p className="mt-4 border-l border-[var(--cinnabar)] pl-4 text-sm leading-7">{event.impact}</p>}
            {event.characters.length > 0 && (
              <div className="mt-5 flex flex-wrap gap-2">
                {event.characters.map((character) => <Link key={character.slug} href={`/characters/${character.slug}`} className="border border-[var(--line)] px-3 py-1 text-xs text-[var(--paper)] hover:border-[var(--paper)]">{character.name}</Link>)}
              </div>
            )}
            <EvidenceList sources={event.sources} className="mt-5 max-w-3xl" />
          </li>
        ))}
      </ol>
    </div>
  );
}

function StatusCard({ children, role }: { children: React.ReactNode; role?: "alert" }) {
  return (
    <div role={role} className="mt-8 flex min-h-[24rem] flex-col items-center justify-center border border-dashed border-[var(--line)] p-10 text-center text-sm text-[var(--fog)] opacity-0 [animation:text-fade-in_0.5s_ease_0.15s_forwards]">
      <span className="seal-mark mb-4" aria-hidden="true">阅</span>
      {children}
    </div>
  );
}
