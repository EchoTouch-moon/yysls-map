"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useProgress } from "@/components/ui/ProgressSelect";
import { apiFetch } from "@/lib/http";

type HistoricalReference = {
  reference_type: string;
  title: string;
  publisher: string;
  url: string;
  locator: string | null;
};

type RelatedBeat = {
  arc_slug: string;
  arc_title: string;
  event_slug: string;
  event_title: string;
};

type HistoryDetail = {
  slug: string;
  title: string;
  period_label: string;
  summary: string;
  fact_kind: string;
  boundary_note: string;
  references: HistoricalReference[];
  related: RelatedBeat[];
};

const FACT_KIND_LABELS: Record<string, string> = {
  work_fact: "作品事实",
  historical_fact: "历史事实",
  credible_parallel: "可信对照",
  editorial_inference: "编辑推测",
};

const REFERENCE_TYPE_LABELS: Record<string, string> = {
  primary_source: "一手史料",
  scholarly_research: "学术研究",
  institutional_reference: "机构资料",
};

function safeHttp(url: string | null): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:"
      ? parsed.toString()
      : null;
  } catch {
    return null;
  }
}

type HistoryApiPayload =
  | HistoryDetail
  | { message?: string; required_progress?: string | null };

export function HistoryDetailCard({ slug }: { slug: string }) {
  const progress = useProgress();
  return <HistoryDetail key={progress} slug={slug} progress={progress} />;
}

function HistoryDetail({ slug, progress }: { slug: string; progress: string }) {
  const [detail, setDetail] = useState<HistoryDetail | null>(null);
  const [restrictedMessage, setRestrictedMessage] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    apiFetch<HistoryApiPayload>(
      `/history/${encodeURIComponent(slug)}?progress=${progress}`,
    )
      .then((response) => {
        if (!active || !response.data) return;
        const data = response.data;
        if ("boundary_note" in data) {
          setDetail(data);
          setRestrictedMessage(null);
        } else {
          setDetail(null);
          setRestrictedMessage(
            data.message ??
              `此卡片需进度达到：${data.required_progress ?? "后续章节"}`,
          );
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          const message = reason instanceof Error ? reason.message : "历史背景读取失败。";
          if (message.includes("404") || message.includes("不存在")) {
            setNotFound(true);
          }
          setError(message);
        }
      });
    return () => {
      active = false;
    };
  }, [progress, slug]);

  if (error && !notFound) {
    return <p role="alert" className="mt-10 text-red-300">{error}</p>;
  }
  if (notFound) {
    return (
      <div className="mt-10 border border-dashed border-[var(--line)] p-10 text-center text-sm leading-7 text-[var(--fog)]">
        未找到这张史料卡片。
        <Link href="/history" className="ml-2 text-[var(--cinnabar-bright)] underline underline-offset-4">
          返回历史背景
        </Link>
      </div>
    );
  }
  if (restrictedMessage) {
    return (
      <div className="mt-10 border border-[var(--cinnabar)] bg-[rgba(157,46,37,.08)] p-8">
        <p className="text-xs tracking-[0.2em] text-[var(--cinnabar-bright)]">内容受限</p>
        <p className="mt-4 leading-7">{restrictedMessage}</p>
        <p className="mt-3 text-sm text-[var(--fog)]">
          可在首页调整「避免重大剧情揭示」设置后重新查看。
        </p>
      </div>
    );
  }
  if (!detail) {
    return (
      <p className="mt-10 text-[var(--fog)]" role="status">
        正在展开史料卡片…
      </p>
    );
  }

  return (
    <article className="archive-frame relative mt-10 overflow-hidden p-8 sm:p-10">
      <p className="text-xs tracking-[0.22em] text-[var(--cinnabar-bright)]">
        {FACT_KIND_LABELS[detail.fact_kind] ?? detail.fact_kind} · {detail.period_label}
      </p>
      <h2 className="mt-3 max-w-3xl text-3xl leading-tight text-[var(--paper-light)]">
        {detail.title}
      </h2>

      <section aria-label="史实概述" className="mt-7 max-w-3xl">
        <p className="text-sm leading-8 text-[var(--paper)]">{detail.summary}</p>
      </section>

      <section aria-label="边界说明" className="mt-7 max-w-3xl border-l-2 border-[var(--cinnabar)] pl-5">
        <p className="text-xs tracking-[0.18em] text-[var(--cinnabar-bright)]">边界说明</p>
        <p className="mt-3 text-sm leading-7 text-[var(--paper)]">{detail.boundary_note}</p>
      </section>

      {detail.references.length > 0 && (
        <section aria-label="独立历史来源" className="mt-8 max-w-3xl border-t border-[var(--line)] pt-6">
          <p className="text-xs tracking-[0.18em] text-[var(--cinnabar-bright)]">独立历史来源</p>
          <ol className="mt-4 grid gap-4">
            {detail.references.map((reference, index) => {
              const href = safeHttp(reference.url);
              return (
                <li
                  key={`${reference.reference_type}:${reference.url}:${index}`}
                  className="border-l border-[var(--line)] pl-4 text-sm"
                >
                  <p className="text-xs tracking-[0.14em] text-[var(--cinnabar-bright)]">
                    {REFERENCE_TYPE_LABELS[reference.reference_type] ?? reference.reference_type}
                  </p>
                  {reference.publisher && (
                    <p className="mt-1 text-xs text-[var(--fog)]">{reference.publisher}</p>
                  )}
                  {href ? (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-1 inline-block text-[var(--paper-light)] underline decoration-[var(--line-strong)] underline-offset-4 hover:decoration-[var(--paper)]"
                    >
                      {reference.title}
                    </a>
                  ) : (
                    <p className="mt-1 text-[var(--paper-light)]">{reference.title}</p>
                  )}
                  {reference.locator && (
                    <p className="mt-1 text-xs leading-5 text-[var(--fog)]">
                      定位：{reference.locator}
                    </p>
                  )}
                </li>
              );
            })}
          </ol>
        </section>
      )}

      {detail.related.length > 0 && (
        <section aria-label="在故事中的位置" className="mt-8 max-w-3xl border-t border-[var(--line)] pt-6">
          <p className="text-xs tracking-[0.18em] text-[var(--cinnabar-bright)]">在故事中的位置</p>
          <ul className="mt-4 grid gap-2">
            {detail.related.map((beat) => (
              <li key={`${beat.arc_slug}:${beat.event_slug}`}>
                <Link
                  href={`/timeline?beat=${encodeURIComponent(beat.event_slug)}`}
                  className="inline-block border border-[var(--line)] px-4 py-2 text-xs text-[var(--paper)] transition hover:border-[var(--paper)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
                >
                  {beat.arc_title} · {beat.event_title} → 回到导读
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}
