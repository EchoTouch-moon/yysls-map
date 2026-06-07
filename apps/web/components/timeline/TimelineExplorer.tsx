"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useProgress } from "@/components/ui/ProgressSelect";
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
};

type TimelineData = {
  progress: string;
  events: TimelineEvent[];
};

export function TimelineExplorer() {
  const progress = useProgress();
  return <TimelineForProgress key={progress} progress={progress} />;
}

function TimelineForProgress({ progress }: { progress: string }) {
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
        if (active) {
          setError(reason instanceof Error ? reason.message : "时间线读取失败。");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [progress]);

  const chapters = useMemo(
    () =>
      Array.from(
        new Map(events.map((event) => [event.chapter_slug, event.chapter_title])),
      ),
    [events],
  );
  const visibleEvents = chapter
    ? events.filter((event) => event.chapter_slug === chapter)
    : events;

  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-center justify-between gap-4 border-y border-[var(--line)] py-4">
        <p className="text-xs tracking-[0.16em] text-[var(--fog)]">
          当前仅显示进度范围内的公开事件
        </p>
        <label className="text-xs text-[var(--fog)]">
          章节
          <select
            value={chapter}
            onChange={(event) => setChapter(event.target.value)}
            className="ml-3 border border-[var(--line)] bg-[var(--ink)] px-3 py-2 text-[var(--paper)]"
          >
            <option value="">全部可见章节</option>
            {chapters.map(([slug, title]) => (
              <option key={slug} value={slug}>
                {title}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading && <StatusCard>正在整理事件次序…</StatusCard>}
      {error && <StatusCard role="alert">{error}</StatusCard>}
      {!loading && !error && visibleEvents.length === 0 && (
        <StatusCard>当前进度暂无可公开事件。</StatusCard>
      )}

      <ol className="relative mt-8 border-l border-[var(--line)] pl-8">
        {visibleEvents.map((event) => (
          <li key={event.id} className="relative mb-10">
            <span className="absolute -left-[2.3rem] top-1 size-3 border border-[var(--cinnabar-bright)] bg-[var(--ink)]" />
            <p className="text-xs tracking-[0.16em] text-[var(--cinnabar-bright)]">
              {event.chapter_title} · {String(event.sort_order).padStart(2, "0")}
            </p>
            <h2 className="mt-3 text-2xl">{event.title}</h2>
            <p className="mt-4 max-w-3xl text-sm leading-7 text-[var(--fog)]">
              {event.summary}
            </p>
            {event.impact && (
              <p className="mt-4 border-l border-[var(--cinnabar)] pl-4 text-sm leading-7">
                {event.impact}
              </p>
            )}
            {event.characters.length > 0 && (
              <div className="mt-5 flex flex-wrap gap-2">
                {event.characters.map((character) => (
                  <Link
                    key={character.slug}
                    href={`/characters/${character.slug}`}
                    className="border border-[var(--line)] px-3 py-1 text-xs text-[var(--paper)] hover:border-[var(--paper)]"
                  >
                    {character.name}
                  </Link>
                ))}
              </div>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}

function StatusCard({
  children,
  role,
}: {
  children: React.ReactNode;
  role?: "alert";
}) {
  return (
    <div
      role={role}
      className="mt-8 border border-dashed border-[var(--line)] p-10 text-center text-sm text-[var(--fog)]"
    >
      {children}
    </div>
  );
}
