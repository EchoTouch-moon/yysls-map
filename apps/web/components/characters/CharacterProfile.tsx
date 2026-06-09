"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useProgress } from "@/components/ui/ProgressSelect";
import { apiFetch } from "@/lib/http";

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
};

export function CharacterProfile({ slug }: { slug: string }) {
  const progress = useProgress();
  return <ProfileForProgress key={`${slug}:${progress}`} slug={slug} progress={progress} />;
}

function ProfileForProgress({
  slug,
  progress,
}: {
  slug: string;
  progress: string;
}) {
  const [detail, setDetail] = useState<CharacterDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    apiFetch<CharacterDetail>(
      `/characters/${encodeURIComponent(slug)}?progress=${progress}`,
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
  }, [progress, slug]);

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

  return (
    <article className="mt-10 grid gap-8 border border-[var(--line)] bg-[rgba(32,35,31,.52)] p-8 md:grid-cols-[1fr_16rem]">
      <div>
        <h1 className="text-4xl">{detail.name}</h1>
        {detail.slug && (
          <Link
            href={`/graph?focus=${encodeURIComponent(detail.slug)}`}
            className="archive-button mt-5 inline-block"
          >
            以此人为中心展开关系
          </Link>
        )}
        <p className="mt-6 leading-8 text-[var(--paper)]">{detail.summary}</p>
        {detail.interpretation && (
          <section className="mt-8 border-l-2 border-[var(--cinnabar)] pl-5">
            <h2 className="text-sm tracking-[0.18em] text-[var(--cinnabar-bright)]">
              卷宗解读
            </h2>
            <p className="mt-3 text-sm leading-7 text-[var(--fog)]">
              {detail.interpretation}
            </p>
          </section>
        )}
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
      </dl>
    </article>
  );
}
