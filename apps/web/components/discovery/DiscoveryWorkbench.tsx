"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";

import { useProgress } from "@/components/ui/ProgressSelect";
import { apiFetch } from "@/lib/http";

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

type PathData = {
  found: boolean;
  nodes: { id: string; slug: string; name: string }[];
  edges: {
    id: string;
    source: string;
    target: string;
    label: string;
    relation_type: string;
  }[];
};

export function DiscoveryWorkbench() {
  const progress = useProgress();
  return <DiscoveryForProgress key={progress} progress={progress} />;
}

function DiscoveryForProgress({ progress }: { progress: string }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [path, setPath] = useState<PathData | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = query.trim();
    if (!normalized) return;
    setLoading(true);
    try {
      const response = await apiFetch<SearchData>(
        `/search?q=${encodeURIComponent(normalized)}&progress=${progress}`,
      );
      setResults(response.data?.results ?? []);
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "搜索失败。");
    } finally {
      setLoading(false);
    }
  }

  async function findPath(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const source = String(form.get("source") ?? "").trim();
    const target = String(form.get("target") ?? "").trim();
    if (!source || !target) return;
    setLoading(true);
    try {
      const response = await apiFetch<PathData>(
        `/relationships/path?from=${encodeURIComponent(source)}&to=${encodeURIComponent(target)}&progress=${progress}`,
      );
      setPath(response.data);
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "关系路径读取失败。");
    } finally {
      setLoading(false);
    }
  }

  const fieldClass =
    "border border-[var(--line)] bg-[rgba(32,35,31,.52)] px-4 py-3 outline-none focus:border-[var(--cinnabar-bright)]";

  return (
    <div className="mt-10 grid gap-10 lg:grid-cols-2">
      <section>
        <h2 className="text-2xl">全文检索</h2>
        <form onSubmit={search} className="mt-5 flex gap-3">
          <label className="sr-only" htmlFor="global-search">搜索内容</label>
          <input
            id="global-search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className={`min-w-0 flex-1 ${fieldClass}`}
            placeholder="角色、势力或事件关键词"
          />
          <button type="submit" className="bg-[var(--cinnabar)] px-5">搜索</button>
        </form>
        <div className="mt-6 grid gap-3">
          {results.map((result) => (
            <Link
              key={`${result.kind}:${result.slug}`}
              href={resultHref(result)}
              className="border border-[var(--line)] p-5 hover:border-[var(--paper)]"
            >
              <div className="flex justify-between gap-4">
                <h3>{result.title}</h3>
                <span className="text-[10px] uppercase text-[var(--cinnabar-bright)]">
                  {result.kind}
                </span>
              </div>
              <p className="mt-3 line-clamp-2 text-sm leading-6 text-[var(--fog)]">
                {result.summary}
              </p>
            </Link>
          ))}
          {!loading && query && results.length === 0 && (
            <p className="text-sm text-[var(--fog)]">当前进度没有匹配内容。</p>
          )}
        </div>
      </section>

      <section>
        <h2 className="text-2xl">关系路径</h2>
        <p className="mt-3 text-sm leading-6 text-[var(--fog)]">
          输入两个角色 slug，服务只在当前进度可见的关系内执行受限 BFS。
        </p>
        <form onSubmit={findPath} className="mt-5 grid gap-3 sm:grid-cols-2">
          <label className="text-xs text-[var(--fog)]">
            起点 slug
            <input name="source" required className={`mt-2 w-full ${fieldClass}`} />
          </label>
          <label className="text-xs text-[var(--fog)]">
            终点 slug
            <input name="target" required className={`mt-2 w-full ${fieldClass}`} />
          </label>
          <button
            type="submit"
            className="border border-[var(--cinnabar)] px-5 py-3 text-sm sm:col-span-2"
          >
            寻找最短关系链
          </button>
        </form>
        {path && (
          <div className="mt-6 border border-[var(--line)] p-6">
            {path.found ? (
              <ol className="flex flex-wrap items-center gap-2">
                {path.nodes.map((node, index) => (
                  <li key={node.id} className="flex items-center gap-2">
                    <Link
                      href={`/characters/${node.slug}`}
                      className="border border-[var(--line)] px-3 py-2 text-sm"
                    >
                      {node.name}
                    </Link>
                    {index < path.edges.length && (
                      <span className="text-xs text-[var(--cinnabar-bright)]">
                        —{path.edges[index].label}→
                      </span>
                    )}
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-sm text-[var(--fog)]">当前进度下不存在可见路径。</p>
            )}
          </div>
        )}
      </section>
      {message && <p role="alert" className="text-sm text-red-300 lg:col-span-2">{message}</p>}
    </div>
  );
}

function resultHref(result: SearchResult) {
  if (result.kind === "character") return `/characters/${result.slug}`;
  if (result.kind === "faction") return `/factions/${result.slug}`;
  return "/timeline";
}
