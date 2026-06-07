"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";

import { useProgress } from "@/components/ui/ProgressSelect";
import { apiFetch } from "@/lib/http";

type Character = {
  id: string;
  slug: string;
  name: string;
  summary: string;
  identity_tags: string[];
  importance: number;
};

type SearchResult = {
  kind: "character" | "faction" | "event";
  slug: string;
  title: string;
  summary: string;
  score: number;
};

type SearchData = {
  query: string;
  results: SearchResult[];
};

export function CharacterDirectory() {
  const progress = useProgress();
  return <DirectoryForProgress key={progress} progress={progress} />;
}

function DirectoryForProgress({ progress }: { progress: string }) {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [results, setResults] = useState<SearchResult[] | null>(null);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    apiFetch<Character[]>(`/resources/characters?progress=${progress}&limit=100`)
      .then((response) => {
        if (active) {
          setCharacters(response.data ?? []);
          setResults(null);
          setError("");
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "人物卷宗读取失败。");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [progress]);

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = query.trim();
    if (!normalized) {
      setResults(null);
      return;
    }
    setLoading(true);
    try {
      const response = await apiFetch<SearchData>(
        `/search?q=${encodeURIComponent(normalized)}&progress=${progress}`,
      );
      setResults(response.data?.results ?? []);
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "检索失败。");
    } finally {
      setLoading(false);
    }
  }

  const shownCharacters =
    results === null
      ? characters
      : results
          .filter((result) => result.kind === "character")
          .map((result) => ({
            id: result.slug,
            slug: result.slug,
            name: result.title,
            summary: result.summary,
            identity_tags: [],
            importance: 1,
          }));

  return (
    <section className="mt-10">
      <form onSubmit={search} className="flex max-w-2xl gap-3">
        <label className="sr-only" htmlFor="character-search">
          检索角色、势力或事件
        </label>
        <input
          id="character-search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="输入角色名或线索关键词"
          className="min-w-0 flex-1 border border-[var(--line)] bg-[rgba(32,35,31,.52)] px-4 py-3 outline-none focus:border-[var(--cinnabar-bright)]"
        />
        <button className="bg-[var(--cinnabar)] px-6 py-3 text-sm" type="submit">
          检索
        </button>
      </form>
      {error && <p role="alert" className="mt-6 text-sm text-red-300">{error}</p>}
      {results !== null && (
        <p className="mt-6 text-xs text-[var(--fog)]">
          检索仅返回当前进度允许公开的内容，共 {results.length} 条。
        </p>
      )}
      <div className="mt-8 grid gap-5 md:grid-cols-2">
        {shownCharacters.map((character) => (
          <Link
            key={character.id}
            href={`/characters/${character.slug}`}
            className="group border border-[var(--line)] bg-[rgba(32,35,31,.52)] p-6 transition hover:border-[var(--paper)]"
          >
            <div className="flex items-start justify-between gap-4">
              <h2 className="text-2xl">{character.name}</h2>
              <span className="text-xs text-[var(--cinnabar-bright)]">
                重要度 {character.importance}
              </span>
            </div>
            <p className="mt-4 line-clamp-3 text-sm leading-7 text-[var(--fog)]">
              {character.summary}
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              {character.identity_tags.map((tag) => (
                <span key={tag} className="border border-[var(--line)] px-2 py-1 text-[10px]">
                  {tag}
                </span>
              ))}
            </div>
          </Link>
        ))}
      </div>
      {!loading && shownCharacters.length === 0 && (
        <div className="mt-8 border border-dashed border-[var(--line)] p-10 text-center text-[var(--fog)]">
          没有找到当前进度可见的人物。
        </div>
      )}
      {loading && <p className="mt-8 text-sm text-[var(--fog)]">正在翻阅卷宗…</p>}
    </section>
  );
}
