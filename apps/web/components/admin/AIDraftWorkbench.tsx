"use client";

import { type FormEvent, useState } from "react";

import { apiFetch } from "@/lib/http";

type ReviewState = "pending" | "accepted" | "rejected";

type RelationshipCandidate = {
  source: string;
  target: string;
  relation_type: string;
  summary: string;
  spoiler_level: number;
  chapter_slug: string | null;
  confidence: number;
  warnings: string[];
  review: ReviewState;
};

type EventCandidate = {
  title: string;
  summary: string;
  character_names: string[];
  chapter_slug: string | null;
  spoiler_level: number;
  confidence: number;
  warnings: string[];
  review: ReviewState;
};

type ExtractionResult = {
  run_id: string | null;
  characters: string[];
  relationships: Omit<RelationshipCandidate, "review">[];
  events: Omit<EventCandidate, "review">[];
  model: string;
  prompt_version: string;
};

export function AIDraftWorkbench({ csrf }: { csrf: string }) {
  const [relationships, setRelationships] = useState<RelationshipCandidate[]>([]);
  const [events, setEvents] = useState<EventCandidate[]>([]);
  const [meta, setMeta] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function extract(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const note = String(form.get("note") ?? "");
    setLoading(true);
    try {
      const response = await apiFetch<ExtractionResult>("/admin/ai/extract", {
        method: "POST",
        headers: { "X-CSRF-Token": csrf },
        body: JSON.stringify({ note }),
      });
      const result = response.data;
      setRelationships(
        (result?.relationships ?? []).map((candidate) => ({
          ...candidate,
          review: "pending",
        })),
      );
      setEvents(
        (result?.events ?? []).map((candidate) => ({
          ...candidate,
          review: "pending",
        })),
      );
      setMeta(
        result
          ? `${result.model} · ${result.prompt_version} · 审计 ${result.run_id}`
          : "",
      );
      setMessage("结构化草稿已生成，尚未写入正式内容。");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "AI 草稿生成失败。");
    } finally {
      setLoading(false);
    }
  }

  const pendingCount =
    relationships.filter((item) => item.review === "pending").length +
    events.filter((item) => item.review === "pending").length;

  return (
    <section className="mt-14 border-t border-[var(--line)] pt-10">
      <p className="text-xs tracking-[0.2em] text-[var(--cinnabar-bright)]">
        可选工具 · 默认关闭
      </p>
      <h2 className="mt-3 text-2xl">AI 结构化草稿审核</h2>
      <p className="mt-4 max-w-3xl text-sm leading-7 text-[var(--fog)]">
        玩家笔记会被视为不可信输入。接受候选只改变本页审核标记，不会发布、
        不会生成来源，也不会绕过正式投稿事务。
      </p>
      <form onSubmit={extract} className="mt-6">
        <label className="text-sm">
          原创笔记
          <textarea
            name="note"
            required
            minLength={20}
            maxLength={20000}
            className="mt-2 min-h-40 w-full border border-[var(--line)] bg-[var(--ink)] p-4 outline-none focus:border-[var(--cinnabar-bright)]"
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="mt-4 border border-[var(--cinnabar)] px-5 py-3 text-sm disabled:opacity-50"
        >
          {loading ? "正在提取…" : "生成待审草稿"}
        </button>
      </form>
      {message && <p role="status" className="mt-4 text-sm text-[var(--fog)]">{message}</p>}
      {meta && <p className="mt-2 text-[10px] text-[var(--fog)]">{meta}</p>}

      {(relationships.length > 0 || events.length > 0) && (
        <div className="mt-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-[var(--fog)]">待处理 {pendingCount} 项</p>
            <button
              type="button"
              onClick={() => {
                setRelationships((items) =>
                  items.map((item) => ({
                    ...item,
                    review: item.warnings.length ? item.review : "accepted",
                  })),
                );
                setEvents((items) =>
                  items.map((item) => ({
                    ...item,
                    review: item.warnings.length ? item.review : "accepted",
                  })),
                );
              }}
              className="border border-[var(--line)] px-4 py-2 text-xs"
            >
              批量接受无警告候选
            </button>
          </div>
          <div className="mt-5 grid gap-4">
            {relationships.map((candidate, index) => (
              <CandidateCard
                key={`relationship:${index}`}
                title={`${candidate.source} → ${candidate.target}`}
                label={candidate.relation_type}
                summary={candidate.summary}
                warnings={candidate.warnings}
                review={candidate.review}
                onSummary={(summary) =>
                  setRelationships((items) =>
                    items.map((item, itemIndex) =>
                      itemIndex === index ? { ...item, summary } : item,
                    ),
                  )
                }
                onReview={(review) =>
                  setRelationships((items) =>
                    items.map((item, itemIndex) =>
                      itemIndex === index ? { ...item, review } : item,
                    ),
                  )
                }
              />
            ))}
            {events.map((candidate, index) => (
              <CandidateCard
                key={`event:${index}`}
                title={candidate.title}
                label="event"
                summary={candidate.summary}
                warnings={candidate.warnings}
                review={candidate.review}
                onSummary={(summary) =>
                  setEvents((items) =>
                    items.map((item, itemIndex) =>
                      itemIndex === index ? { ...item, summary } : item,
                    ),
                  )
                }
                onReview={(review) =>
                  setEvents((items) =>
                    items.map((item, itemIndex) =>
                      itemIndex === index ? { ...item, review } : item,
                    ),
                  )
                }
              />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function CandidateCard({
  title,
  label,
  summary,
  warnings,
  review,
  onSummary,
  onReview,
}: {
  title: string;
  label: string;
  summary: string;
  warnings: string[];
  review: ReviewState;
  onSummary: (value: string) => void;
  onReview: (value: ReviewState) => void;
}) {
  return (
    <article className="border border-[var(--line)] p-5">
      <div className="flex justify-between gap-4">
        <h3>{title}</h3>
        <span className="text-[10px] uppercase text-[var(--cinnabar-bright)]">
          {label} · {review}
        </span>
      </div>
      <label className="mt-4 block text-xs text-[var(--fog)]">
        候选摘要
        <textarea
          value={summary}
          onChange={(event) => onSummary(event.target.value)}
          className="mt-2 min-h-24 w-full border border-[var(--line)] bg-[var(--ink)] p-3 text-sm text-[var(--paper)]"
        />
      </label>
      {warnings.length > 0 && (
        <ul className="mt-3 space-y-1 text-xs text-amber-300">
          {warnings.map((warning) => <li key={warning}>{warning}</li>)}
        </ul>
      )}
      <div className="mt-4 flex gap-3">
        <button
          type="button"
          onClick={() => onReview("accepted")}
          className="border border-emerald-700 px-4 py-2 text-xs"
        >
          接受候选
        </button>
        <button
          type="button"
          onClick={() => onReview("rejected")}
          className="border border-[var(--cinnabar)] px-4 py-2 text-xs"
        >
          拒绝候选
        </button>
      </div>
    </article>
  );
}
