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

type StoryArcSummary = {
  id: string;
  slug: string;
  title: string;
  summary: string;
  core_question: string;
  estimated_minutes: number;
  beat_count: number;
};

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

type StoryBeat = {
  id: string;
  sort_order: number;
  role: string;
  guide: string;
  why_it_matters: string;
  bridge: string;
  next_question: string;
  event: Pick<
    TimelineEvent,
    "slug" | "title" | "summary" | "impact" | "characters" | "sources"
  >;
  relationships: BeatRelationship[];
  historical_contexts: HistoricalContext[];
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

type StoryArcDetail = StoryArcSummary & { beats: StoryBeat[] };
type StoryArcListData = { progress: string; arcs: StoryArcSummary[] };
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

const STORY_ROLE_LABELS: Record<string, string> = {
  setup: "铺垫",
  clue: "线索",
  escalation: "升级",
  turning_point: "转折",
  consequence: "后果",
  resolution: "回收",
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
          导读按故事的因果展开；完整事件保留章节筛选与所有已解锁记录。
        </p>
      </div>

      {mode === "guide" ? (
        <StoryGuide key={`guide:${progress}`} progress={progress} />
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

function StoryGuide({ progress }: { progress: string }) {
  const [arcs, setArcs] = useState<StoryArcSummary[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, StoryArcDetail>>({});
  const [listLoading, setListLoading] = useState(true);
  const [error, setError] = useState("");
  // /timeline?beat={event_slug} —— 深链：定位包含该事件的卷与幕次。
  const [pendingBeatSlug] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    return new URLSearchParams(window.location.search).get("beat");
  });
  const [deepLink, setDeepLink] = useState<{ arcSlug: string | null; done: boolean }>({
    arcSlug: null,
    done: false,
  });

  useEffect(() => {
    let active = true;
    const params = new URLSearchParams({ progress });
    apiFetch<StoryArcListData>(`/story-arcs?${params}`)
      .then((response) => {
        if (active) setArcs(response.data?.arcs ?? []);
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "故事导读读取失败。");
        }
      })
      .finally(() => {
        if (active) setListLoading(false);
      });
    return () => {
      active = false;
    };
  }, [progress]);

  const activeSlug =
    selectedSlug ?? deepLink.arcSlug ?? arcs[0]?.slug ?? null;

  // 深链解析：逐卷检查哪一卷包含目标事件；解析完成后不再重试。
  useEffect(() => {
    if (!pendingBeatSlug || deepLink.done || arcs.length === 0 || error) return;
    let active = true;
    void (async () => {
      for (const arc of arcs) {
        try {
          const params = new URLSearchParams({ progress });
          const response = await apiFetch<StoryArcDetail>(
            `/story-arcs/${encodeURIComponent(arc.slug)}?${params}`,
          );
          if (!active || !response.data) return;
          const arcDetail = response.data;
          const contains = arcDetail.beats.some(
            (beat) => beat.event.slug === pendingBeatSlug,
          );
          setDetails((prev) => ({ ...prev, [arc.slug]: arcDetail }));
          if (contains) {
            setDeepLink({ arcSlug: arc.slug, done: true });
            return;
          }
        } catch {
          // 单卷读取失败时继续尝试下一卷；常规加载路径会呈现错误。
        }
      }
      if (active) setDeepLink({ arcSlug: null, done: true });
    })();
    return () => {
      active = false;
    };
  }, [pendingBeatSlug, deepLink.done, arcs, progress, error]);

  // 确保当前卷详情已加载（含深链解析过程中已缓存的卷）。
  useEffect(() => {
    if (!activeSlug || details[activeSlug]) return;
    let active = true;
    const params = new URLSearchParams({ progress });
    apiFetch<StoryArcDetail>(`/story-arcs/${encodeURIComponent(activeSlug)}?${params}`)
      .then((response) => {
        const arcDetail = response.data;
        if (!active || !arcDetail) return;
        setDetails((prev) => ({ ...prev, [activeSlug]: arcDetail }));
        setError("");
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "故事导读读取失败。");
        }
      });
    return () => {
      active = false;
    };
  }, [activeSlug, details, progress]);

  const activeDetail = activeSlug ? details[activeSlug] ?? null : null;
  const activeSummary = arcs.find((arc) => arc.slug === activeSlug) ?? arcs[0];

  return (
    <div
      id="story-guide-panel"
      role="tabpanel"
      aria-labelledby="guide-timeline-tab"
      className="mt-8 min-w-0"
    >
      {listLoading && <StatusCard>正在展开故事卷轴…</StatusCard>}
      {error && <StatusCard role="alert">{error}</StatusCard>}
      {!listLoading && !error && arcs.length === 0 && (
        <StatusCard>当前进度暂无可公开导读。</StatusCard>
      )}

      {!listLoading && !error && activeSummary && (
        <>
          {arcs.length > 1 && (
            <div className="mb-5 flex flex-wrap gap-2" aria-label="选择导读卷">
              {arcs.map((arc) => (
                <button
                  key={arc.slug}
                  type="button"
                  onClick={() => setSelectedSlug(arc.slug)}
                  aria-pressed={activeSlug === arc.slug}
                  className={`border px-3 py-2 text-xs transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)] ${
                    activeSlug === arc.slug
                      ? "border-[var(--cinnabar)] text-[var(--paper-light)]"
                      : "border-[var(--line)] text-[var(--fog)] hover:border-[var(--paper)]"
                  }`}
                >
                  {arc.title}
                </button>
              ))}
            </div>
          )}
          <GuideMasthead summary={activeSummary} beatCount={activeDetail?.beats.length ?? activeSummary.beat_count} />
          {!activeDetail && <StatusCard>正在校对本卷的叙事线索…</StatusCard>}
          {activeDetail && (
            <StoryReader
              key={activeDetail.slug}
              detail={activeDetail}
              initialEventSlug={
                deepLink.done && deepLink.arcSlug === activeDetail.slug
                  ? pendingBeatSlug
                  : null
              }
            />
          )}
        </>
      )}
    </div>
  );
}

function GuideMasthead({ summary, beatCount }: { summary: StoryArcSummary; beatCount: number }) {
  return (
    <header className="archive-frame relative overflow-hidden px-6 py-7 sm:px-9 sm:py-9">
      <span className="absolute right-8 top-7 hidden text-7xl leading-none text-[rgba(192,74,54,.12)] sm:block" aria-hidden="true">卷</span>
      <p className="text-xs tracking-[0.26em] text-[var(--cinnabar-bright)]">清河主线导读</p>
      <h2 className="mt-3 max-w-3xl text-3xl leading-tight text-[var(--paper-light)] sm:text-4xl">{summary.title}</h2>
      <p className="mt-5 max-w-3xl leading-8 text-[var(--fog)]">{summary.summary}</p>
      <div className="mt-6 grid gap-4 border-t border-[var(--line)] pt-5 sm:grid-cols-[minmax(0,1fr)_auto]">
        <div>
          <p className="text-[10px] tracking-[0.18em] text-[var(--fog)]">本卷要问</p>
          <p className="mt-2 text-sm leading-7 text-[var(--paper)]">{summary.core_question}</p>
        </div>
        <dl className="flex gap-6 text-xs text-[var(--fog)] sm:self-end">
          <div>
            <dt className="tracking-[0.12em]">预计阅读</dt>
            <dd className="mt-1 text-[var(--paper-light)]">{summary.estimated_minutes} 分钟</dd>
          </div>
          <div>
            <dt className="tracking-[0.12em]">已解锁</dt>
            <dd className="mt-1 text-[var(--paper-light)]">{beatCount} 节</dd>
          </div>
        </dl>
      </div>
    </header>
  );
}

function StoryReader({
  detail,
  initialEventSlug = null,
}: {
  detail: StoryArcDetail;
  initialEventSlug?: string | null;
}) {
  const initialPosition = Math.max(
    0,
    detail.beats.findIndex((beat) => beat.event.slug === initialEventSlug),
  );
  const [activePosition, setActivePosition] = useState(initialPosition);
  const activeBeat = detail.beats[activePosition] ?? detail.beats[0];

  useEffect(() => {
    if (initialPosition > 0) {
      document
        .getElementById("story-guide-panel")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [initialPosition]);

  if (!activeBeat) return <StatusCard>当前进度尚未解锁本卷的阅读节点。</StatusCard>;

  const previousAvailable = activePosition > 0;
  const nextAvailable = activePosition < detail.beats.length - 1;

  return (
    <div className="mt-7 grid min-w-0 gap-6 lg:grid-cols-[13rem_minmax(0,1fr)]">
      <nav aria-label="故事幕次导航" className="min-w-0 border-y border-[var(--line)] py-3 lg:border-y-0 lg:border-r lg:py-0 lg:pr-5">
        <p className="mb-3 text-[10px] tracking-[0.22em] text-[var(--fog)]">卷签 · 幕次</p>
        <ol className="flex min-w-0 max-w-full gap-2 overflow-x-auto overscroll-x-contain pb-1 lg:flex-col lg:overflow-visible">
          {detail.beats.map((beat, index) => {
            const active = index === activePosition;
            return (
              <li key={beat.id} className="shrink-0">
                <button
                  type="button"
                  onClick={() => setActivePosition(index)}
                  aria-current={active ? "step" : undefined}
                  className={`w-full border-l-2 px-3 py-3 text-left text-xs leading-5 transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)] ${
                    active
                      ? "border-[var(--cinnabar-bright)] bg-[rgba(143,47,37,.14)] text-[var(--paper-light)]"
                      : "border-transparent text-[var(--fog)] hover:border-[var(--line-strong)] hover:text-[var(--paper)]"
                  }`}
                >
                  <span className="block text-[10px] tracking-[0.14em] text-[var(--cinnabar-bright)]">第 {String(beat.sort_order).padStart(2, "0")} 幕</span>
                  <span className="mt-1 block lg:line-clamp-2">{beat.event.title}</span>
                </button>
              </li>
            );
          })}
        </ol>
      </nav>

      <article aria-label={`第 ${activeBeat.sort_order} 幕：${activeBeat.event.title}`} className="archive-frame relative min-w-0 overflow-hidden p-6 sm:p-9">
        <p className="text-xs tracking-[0.22em] text-[var(--cinnabar-bright)]">第 {String(activeBeat.sort_order).padStart(2, "0")} 幕 · {labelFor(STORY_ROLE_LABELS, activeBeat.role)}</p>
        <h3 className="mt-3 text-3xl leading-tight text-[var(--paper-light)]">{activeBeat.event.title}</h3>
        <p className="mt-5 max-w-3xl text-base leading-8 text-[var(--paper)]">{activeBeat.guide}</p>

        <div className="mt-7 grid gap-5 border-y border-[var(--line)] py-6 text-sm leading-7 sm:grid-cols-2">
          <ReadingNote label="这一节发生了什么">{activeBeat.event.summary}</ReadingNote>
          <ReadingNote label="为什么重要">{activeBeat.why_it_matters}</ReadingNote>
          <ReadingNote label="与上一节的承接">{activeBeat.bridge}</ReadingNote>
          <ReadingNote label="带着这个问题读下去" cinnabar>{activeBeat.next_question}</ReadingNote>
        </div>

        {activeBeat.event.impact && <p className="mt-6 border-l border-[var(--cinnabar)] pl-4 text-sm leading-7 text-[var(--paper)]">{activeBeat.event.impact}</p>}

        {activeBeat.event.characters.length > 0 && (
          <div className="mt-6">
            <p className="text-[10px] tracking-[0.18em] text-[var(--fog)]">本节人物</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {activeBeat.event.characters.map((character) => (
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

        {activeBeat.relationships.length > 0 && (
          <section className="mt-6" aria-label="本节相关关系">
            <p className="text-[10px] tracking-[0.18em] text-[var(--fog)]">本节相关关系</p>
            <ul className="mt-3 flex flex-wrap gap-2">
              {activeBeat.relationships.map((relationship) => (
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

        <HistoricalContextList contexts={activeBeat.historical_contexts} />
        <EvidenceList sources={activeBeat.event.sources} className="mt-6 max-w-3xl" />

        <div className="mt-8 flex items-center justify-between gap-3 border-t border-[var(--line)] pt-5">
          <button type="button" onClick={() => setActivePosition((position) => position - 1)} disabled={!previousAvailable} className="archive-button disabled:cursor-not-allowed disabled:border-[var(--line)] disabled:text-[var(--fog)] disabled:hover:bg-transparent">
            ← 上一节
          </button>
          <p className="text-xs tabular-nums text-[var(--fog)]" aria-live="polite">{activePosition + 1} / {detail.beats.length}</p>
          <button type="button" onClick={() => setActivePosition((position) => position + 1)} disabled={!nextAvailable} className="archive-button disabled:cursor-not-allowed disabled:border-[var(--line)] disabled:text-[var(--fog)] disabled:hover:bg-transparent">
            下一节 →
          </button>
        </div>
      </article>
    </div>
  );
}

function ReadingNote({ label, children, cinnabar = false }: { label: string; children: React.ReactNode; cinnabar?: boolean }) {
  return (
    <div>
      <p className={`text-[10px] tracking-[0.18em] ${cinnabar ? "text-[var(--cinnabar-bright)]" : "text-[var(--fog)]"}`}>{label}</p>
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
