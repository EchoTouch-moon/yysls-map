"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useProgress } from "@/components/ui/ProgressSelect";
import {
  EvidenceList,
  type EvidenceSource,
} from "@/components/ui/EvidenceList";
import { apiFetch } from "@/lib/http";

type HistoryChip = {
  slug: string;
  title: string;
  relation_kind: string;
};

type StoryPathStep = {
  arc_slug: string;
  arc_title: string;
  beat_sort_order: number;
  role: string;
  guide: string;
  event_slug: string;
  event_title: string;
  event_summary: string;
  why_it_matters: string;
  historical: HistoryChip[];
};

type CharacterDetail = {
  restricted?: boolean;
  required_progress?: string | null;
  message?: string;
  id?: string;
  slug?: string;
  name?: string;
  summary?: string;
  interpretation?: string | null;
  identity_tags?: string[];
  faction_name?: string | null;
  first_appear_chapter?: string | null;
  sources?: EvidenceSource[];
  story_path?: StoryPathStep[];
};

type GraphNodeLite = { id: string; slug: string; label: string };

type GraphEdgeLite = {
  id: string;
  source: string;
  target: string;
  label: string;
};

type RelationRow = {
  id: string;
  source_slug: string;
  source_name: string;
  target_slug: string;
  target_name: string;
  label: string;
};

const STORY_ROLE_LABELS: Record<string, string> = {
  setup: "铺垫",
  clue: "线索",
  escalation: "升级",
  turning_point: "转折",
  consequence: "后果",
  resolution: "回收",
};

function roleLabel(value: string): string {
  return STORY_ROLE_LABELS[value] ?? value;
}

export function CharacterProfile({ slug }: { slug: string }) {
  const progress = useProgress();
  return <Profile key={`${slug}:${progress}`} slug={slug} progress={progress} />;
}

function Profile({ slug, progress }: { slug: string; progress: string }) {
  const [reveal, setReveal] = useState(false);
  const [detail, setDetail] = useState<CharacterDetail | null>(null);
  const [relations, setRelations] = useState<RelationRow[]>([]);
  const [relationsHiddenCount, setRelationsHiddenCount] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const revealSuffix = reveal ? "&reveal=true" : "";
    apiFetch<CharacterDetail>(
      `/characters/${encodeURIComponent(slug)}?progress=${progress}${revealSuffix}`,
    )
      .then((response) => {
        if (active) {
          setDetail(response.data);
          setError("");
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "角色详情读取失败。");
        }
      });
    return () => {
      active = false;
    };
  }, [progress, reveal, slug]);

  useEffect(() => {
    let active = true;
    // 默认只取当前进度可见的关系；显式 Reveal 后才解锁隐藏关系（G4）。
    const graphProgress = reveal ? "unrestricted" : progress;
    apiFetch<{ nodes: GraphNodeLite[]; edges: GraphEdgeLite[] }>(
      `/graph?focus=${encodeURIComponent(slug)}&progress=${graphProgress}`,
    )
      .then((response) => {
        if (!active || !response.data) return;
        const nodeById = new Map(response.data.nodes.map((node) => [node.id, node]));
        const focusNode = response.data.nodes.find((node) => node.slug === slug);
        const rows: RelationRow[] = [];
        let hidden = 0;
        for (const edge of response.data.edges) {
          const source = nodeById.get(edge.source);
          const target = nodeById.get(edge.target);
          if (!source || !target) continue;
          if (focusNode && source.id === focusNode.id && target.id === focusNode.id) {
            continue;
          }
          if (
            !reveal &&
            focusNode &&
            source.id !== focusNode.id &&
            target.id !== focusNode.id
          ) {
            hidden += 1;
            continue;
          }
          rows.push({
            id: edge.id,
            source_slug: source.slug,
            source_name: source.label,
            target_slug: target.slug,
            target_name: target.label,
            label: edge.label,
          });
        }
        setRelations(rows);
        setRelationsHiddenCount(hidden);
      })
      .catch(() => {
        if (active) setRelations([]);
      });
    return () => {
      active = false;
    };
  }, [progress, reveal, slug]);

  if (error) return <p role="alert" className="mt-10 text-red-300">{error}</p>;
  if (!detail) return <p className="mt-10 text-[var(--fog)]">正在调阅角色卷宗…</p>;
  if (detail.restricted) {
    return (
      <div className="mt-10 border border-[var(--cinnabar)] bg-[rgba(157,46,37,.08)] p-8">
        <p className="text-xs tracking-[0.2em] text-[var(--cinnabar-bright)]">内容受限</p>
        <p className="mt-4 leading-7">{detail.message}</p>
        <p className="mt-3 text-sm text-[var(--fog)]">
          所需进度：{detail.required_progress ?? "后续章节"}
        </p>
      </div>
    );
  }

  const storyPath = detail.story_path ?? [];
  const historyChips = new Map<string, HistoryChip>();
  for (const step of storyPath) {
    for (const chip of step.historical) {
      historyChips.set(chip.slug, chip);
    }
  }

  return (
    <article className="mt-10 grid gap-8 border border-[var(--line)] bg-[rgba(32,35,31,.52)] p-8 md:grid-cols-[1fr_16rem]">
      <div>
        <h1 className="text-4xl">{detail.name}</h1>

        {/* 第一层 · 初识 */}
        <section aria-label="初识" className="mt-6">
          <SectionLabel>初识</SectionLabel>
          <p className="mt-3 leading-8 text-[var(--paper)]">{detail.summary}</p>
        </section>

        {/* 第二层 · 剧情足迹 */}
        {storyPath.length > 0 && (
          <section aria-label="剧情足迹" className="mt-9 border-t border-[var(--line)] pt-7">
            <SectionLabel cinnabar>剧情足迹</SectionLabel>
            <p className="mt-2 text-xs leading-5 text-[var(--fog)]">
              此人在清河主线中出现过的关键节点，按幕次排列。
            </p>
            <ol className="mt-4 grid gap-4">
              {storyPath.map((step) => (
                <li
                  key={`${step.arc_slug}:${step.beat_sort_order}`}
                  className="border border-[var(--line)] bg-[rgba(21,19,15,.4)] p-5"
                >
                  <p className="text-xs tracking-[0.16em] text-[var(--cinnabar-bright)]">
                    第 {String(step.beat_sort_order).padStart(2, "0")} 幕 ·{" "}
                    {roleLabel(step.role)}
                  </p>
                  <h3 className="mt-2 text-lg leading-snug text-[var(--paper-light)]">
                    {step.event_title}
                  </h3>
                  <p className="mt-3 text-sm leading-7 text-[var(--paper)]">{step.guide}</p>
                  <details className="group mt-3">
                    <summary className="cursor-pointer list-none text-xs tracking-[0.12em] text-[var(--fog)] transition hover:text-[var(--paper)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]">
                      为什么重要 ＋
                    </summary>
                    <p className="mt-2 border-l border-[var(--cinnabar)] pl-3 text-sm leading-7 text-[var(--fog)] group-open:text-[var(--paper)]">
                      {step.why_it_matters}
                    </p>
                  </details>
                  <Link
                    href={`/timeline?beat=${encodeURIComponent(step.event_slug)}`}
                    className="mt-3 inline-block text-xs text-[var(--cinnabar-bright)] underline decoration-[var(--line-strong)] underline-offset-4 hover:text-[var(--paper-light)]"
                  >
                    在导读中阅读这一幕 →
                  </Link>
                </li>
              ))}
            </ol>
          </section>
        )}

        {/* 第三层 · 人物关系 */}
        <section aria-label="人物关系" className="mt-9 border-t border-[var(--line)] pt-7">
          <SectionLabel>他与谁相连</SectionLabel>
          {relations.length > 0 ? (
            <ul className="mt-4 grid gap-2">
              {relations.map((row) => (
                <li
                  key={row.id}
                  className="flex flex-wrap items-center gap-2 border border-[var(--line)] px-4 py-2.5 text-sm text-[var(--paper)]"
                >
                  <Link href={`/characters/${row.source_slug}`} className="hover:text-[var(--paper-light)]">
                    {row.source_name}
                  </Link>
                  <span className="text-[var(--cinnabar-bright)]">—{row.label}→</span>
                  <Link href={`/characters/${row.target_slug}`} className="hover:text-[var(--paper-light)]">
                    {row.target_name}
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-4 text-sm leading-7 text-[var(--fog)]">当前进度下暂无可见关系。</p>
          )}
          {!reveal && relationsHiddenCount > 0 && (
            <p className="mt-3 text-xs leading-5 text-[var(--fog)]">
              另有 {relationsHiddenCount} 条关系涉及后续揭示，显示完整解析后展开。
            </p>
          )}
          <Link
            href={`/graph?focus=${encodeURIComponent(detail.slug ?? slug)}`}
            className="archive-button mt-5 inline-block"
          >
            以此人为中心展开关系图
          </Link>
        </section>

        {/* 第四层 · 完整解析（显式 Reveal） */}
        <section aria-label="完整解析" className="mt-9 border-t border-[var(--line)] pt-7">
          {reveal ? (
            detail.interpretation ? (
              <div className="border-l-2 border-[var(--cinnabar)] pl-5">
                <h2 className="text-sm tracking-[0.18em] text-[var(--cinnabar-bright)]">
                  完整解析
                </h2>
                <p className="mt-3 text-sm leading-7 text-[var(--fog)]">
                  {detail.interpretation}
                </p>
              </div>
            ) : (
              <p className="text-sm leading-7 text-[var(--fog)]">
                此人暂无更多隐藏解析。
              </p>
            )
          ) : (
            <button
              type="button"
              onClick={() => setReveal(true)}
              className="border border-[var(--cinnabar)] px-5 py-3 text-sm tracking-[0.14em] text-[var(--cinnabar-bright)] transition hover:bg-[rgba(157,46,37,.1)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
            >
              ⚠ 显示该人物的完整解析
            </button>
          )}
          {reveal && (
            <button
              type="button"
              onClick={() => setReveal(false)}
              className="mt-4 block text-xs text-[var(--fog)] underline underline-offset-4 hover:text-[var(--paper)]"
            >
              收起解析
            </button>
          )}
        </section>

        {/* 第五层 · 历史背景 */}
        {historyChips.size > 0 && (
          <section aria-label="相关历史背景" className="mt-9 border-t border-[var(--line)] pt-7">
            <SectionLabel>相关历史背景</SectionLabel>
            <p className="mt-2 text-xs leading-5 text-[var(--fog)]">
              与此人的剧情节点相关的可核史实卡片。
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {[...historyChips.values()].map((chip) => (
                <Link
                  key={chip.slug}
                  href={`/history/${chip.slug}`}
                  className="border border-[var(--line)] px-3 py-1.5 text-xs text-[var(--paper)] transition hover:border-[var(--paper)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
                >
                  {chip.title}
                </Link>
              ))}
            </div>
          </section>
        )}

        <EvidenceList sources={detail.sources} className="mt-9" />
      </div>

      <dl className="space-y-5 border-t border-[var(--line)] pt-6 text-sm md:border-l md:border-t-0 md:pl-6 md:pt-0">
        <div>
          <dt className="text-xs text-[var(--fog)]">所属势力</dt>
          <dd className="mt-1">{detail.faction_name ?? "未归档"}</dd>
        </div>
        <div>
          <dt className="text-xs text-[var(--fog)]">初次登场</dt>
          <dd className="mt-1">{detail.first_appear_chapter ?? "未归档"}</dd>
        </div>
        <div>
          <dt className="text-xs text-[var(--fog)]">身份标签</dt>
          <dd className="mt-2 flex flex-wrap gap-2">
            {(detail.identity_tags ?? []).map((tag) => (
              <span key={tag} className="border border-[var(--line)] px-2 py-1 text-xs">
                {tag}
              </span>
            ))}
          </dd>
        </div>
        <div className="border-t border-[var(--line)] pt-4 text-xs leading-5 text-[var(--fog)]">
          部分重大揭示默认隐藏。选择「显示完整解析」即表示接受相关剧透。
        </div>
      </dl>
    </article>
  );
}

function SectionLabel({ children, cinnabar = false }: { children: React.ReactNode; cinnabar?: boolean }) {
  return (
    <h2
      className={`text-sm tracking-[0.18em] ${
        cinnabar ? "text-[var(--cinnabar-bright)]" : "text-[var(--paper-light)]"
      }`}
    >
      {children}
    </h2>
  );
}
