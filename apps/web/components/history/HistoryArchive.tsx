"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useProgress } from "@/components/ui/ProgressSelect";
import { apiFetch } from "@/lib/http";

type HistoryListItem = {
  slug: string;
  title: string;
  period_label: string;
  summary: string;
  fact_kind: string;
};

const FACT_KIND_LABELS: Record<string, string> = {
  work_fact: "作品事实",
  historical_fact: "历史事实",
  credible_parallel: "可信对照",
  editorial_inference: "编辑推测",
};

export function HistoryArchive() {
  const progress = useProgress();
  return <HistoryList key={progress} progress={progress} />;
}

function HistoryList({ progress }: { progress: string }) {
  const [items, setItems] = useState<HistoryListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    apiFetch<{ contexts: HistoryListItem[] }>(`/history?progress=${progress}`)
      .then((response) => {
        if (active) setItems(response.data?.contexts ?? []);
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "历史背景读取失败。");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [progress]);

  if (loading) {
    return (
      <p className="mt-10 text-[var(--fog)]" role="status">
        正在整理史料卡片…
      </p>
    );
  }
  if (error) return <p role="alert" className="mt-10 text-red-300">{error}</p>;
  if (items.length === 0) {
    return (
      <p className="mt-10 border border-dashed border-[var(--line)] p-10 text-center text-sm leading-7 text-[var(--fog)]">
        当前保护层级下暂无可展示的历史卡片。可在首页调整「避免重大剧情揭示」设置。
      </p>
    );
  }

  return (
    <div className="mt-10 grid gap-4 md:grid-cols-2">
      {items.map((item) => (
        <Link
          key={item.slug}
          href={`/history/${item.slug}`}
          className="group border border-[var(--line)] bg-[rgba(32,35,31,.52)] p-6 transition hover:border-[var(--paper)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--cinnabar-bright)]"
        >
          <p className="text-xs tracking-[0.16em] text-[var(--cinnabar-bright)]">
            {FACT_KIND_LABELS[item.fact_kind] ?? item.fact_kind}
          </p>
          <h2 className="mt-3 text-xl leading-snug text-[var(--paper-light)]">{item.title}</h2>
          <p className="mt-2 text-xs text-[var(--fog)]">{item.period_label}</p>
          <p className="mt-4 line-clamp-3 text-sm leading-7 text-[var(--fog)] group-hover:text-[var(--paper)]">
            {item.summary}
          </p>
        </Link>
      ))}
    </div>
  );
}
