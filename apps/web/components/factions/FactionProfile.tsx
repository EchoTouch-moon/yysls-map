"use client";

import { useEffect, useState } from "react";

import { useProgress } from "@/components/ui/ProgressSelect";
import { apiFetch } from "@/lib/http";

type Faction = {
  slug: string;
  name: string;
  faction_type: string;
  summary: string;
  spoiler_level: number;
};

export function FactionProfile({ slug }: { slug: string }) {
  const progress = useProgress();
  return <FactionForProgress key={`${slug}:${progress}`} slug={slug} progress={progress} />;
}

function FactionForProgress({
  slug,
  progress,
}: {
  slug: string;
  progress: string;
}) {
  const [faction, setFaction] = useState<Faction | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    apiFetch<Faction>(
      `/resources/factions/${encodeURIComponent(slug)}?progress=${progress}`,
    )
      .then((response) => {
        if (active) setFaction(response.data);
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(
            reason instanceof Error
              ? reason.message
              : "势力卷宗不存在或尚不可见。",
          );
        }
      });
    return () => {
      active = false;
    };
  }, [progress, slug]);

  if (error) return <p role="alert" className="mt-10 text-red-300">{error}</p>;
  if (!faction) return <p className="mt-10 text-[var(--fog)]">正在调阅势力卷宗…</p>;
  return (
    <article className="mt-10 border border-[var(--line)] bg-[rgba(32,35,31,.52)] p-8">
      <p className="text-xs uppercase tracking-[0.2em] text-[var(--cinnabar-bright)]">
        {faction.faction_type} · 剧透等级 {faction.spoiler_level}
      </p>
      <h1 className="mt-4 text-4xl">{faction.name}</h1>
      <p className="mt-7 max-w-3xl leading-8 text-[var(--fog)]">{faction.summary}</p>
    </article>
  );
}
