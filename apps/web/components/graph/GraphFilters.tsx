import { useMemo, useState } from "react";

import type { GraphNode, RelationType } from "@/lib/graph";

const RELATIONS: { value: RelationType; label: string }[] = [
  { value: "mentor", label: "师徒" },
  { value: "family", label: "亲属" },
  { value: "enemy", label: "敌对" },
  { value: "ally", label: "同盟" },
  { value: "old_acquaintance", label: "旧识" },
  { value: "exploitation", label: "利用" },
  { value: "hierarchy", label: "上下级" },
  { value: "same_sect", label: "同门" },
  { value: "interest", label: "利益" },
  { value: "hidden", label: "隐藏" },
];

export function GraphFilters({
  nodes,
  search,
  faction,
  relation,
  onSearch,
  onFaction,
  onRelation,
  onSelect,
}: {
  nodes: GraphNode[];
  search: string;
  faction: string;
  relation: RelationType | "";
  onSearch: (value: string) => void;
  onFaction: (value: string) => void;
  onRelation: (value: RelationType | "") => void;
  onSelect: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const factions = useMemo(
    () =>
      Array.from(
        new Set(nodes.map((node) => node.faction_name).filter(Boolean)),
      ).sort() as string[],
    [nodes],
  );
  const results = useMemo(
    () =>
      search.trim()
        ? nodes
            .filter((node) => node.label.includes(search.trim()))
            .slice(0, 8)
        : [],
    [nodes, search],
  );

  const fieldClass =
    "border border-[var(--line)] bg-[rgba(21,19,15,.78)] px-3 py-2 text-xs text-[var(--paper)] outline-none transition focus:border-[var(--paper-deep)]";

  return (
    <div className="flex flex-wrap gap-3">
      <div className="relative">
        <label className="sr-only" htmlFor="graph-search">搜索角色</label>
        <input
          id="graph-search"
          value={search}
          onChange={(event) => {
            onSearch(event.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => window.setTimeout(() => setOpen(false), 120)}
          className={`w-44 ${fieldClass}`}
          placeholder="搜索角色…"
        />
        {open && results.length > 0 && (
          <ul className="absolute z-50 mt-1 w-64 border border-[var(--line-strong)] bg-[var(--ink)] shadow-2xl">
            {results.map((node) => (
              <li key={node.id}>
                <button
                  type="button"
                  onMouseDown={(event) => {
                    event.preventDefault();
                    onSelect(node.id);
                    setOpen(false);
                  }}
                  className="flex w-full justify-between px-3 py-2 text-left text-xs hover:bg-[var(--ink-soft)]"
                >
                  <span>{node.label}</span>
                  <span className="text-[var(--fog)]">{node.faction_name}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <label className="sr-only" htmlFor="graph-faction">势力筛选</label>
      <select
        id="graph-faction"
        value={faction}
        onChange={(event) => onFaction(event.target.value)}
        className={fieldClass}
      >
        <option value="">全部势力</option>
        {factions.map((name) => <option key={name}>{name}</option>)}
      </select>
      <label className="sr-only" htmlFor="graph-relation">关系筛选</label>
      <select
        id="graph-relation"
        value={relation}
        onChange={(event) => onRelation(event.target.value as RelationType | "")}
        className={fieldClass}
      >
        <option value="">全部关系</option>
        {RELATIONS.map((item) => (
          <option key={item.value} value={item.value}>{item.label}</option>
        ))}
      </select>
    </div>
  );
}
