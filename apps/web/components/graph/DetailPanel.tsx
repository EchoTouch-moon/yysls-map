import Link from "next/link";

import type { GraphEdge, GraphNode, RelationType } from "@/lib/graph";

export type DetailTarget =
  | { kind: "node"; node: GraphNode }
  | { kind: "edge"; edge: GraphEdge };

const LABELS: Record<RelationType, string> = {
  mentor: "师徒",
  family: "亲属",
  enemy: "敌对",
  ally: "同盟",
  old_acquaintance: "旧识",
  exploitation: "利用",
  hierarchy: "上下级",
  same_sect: "同门",
  interest: "利益",
  hidden: "隐藏",
};

export function DetailPanel({
  detail,
  onClose,
}: {
  detail: DetailTarget | null;
  onClose: () => void;
}) {
  if (!detail) return null;
  return (
    <aside
      aria-label="图谱详情"
      className="absolute right-0 top-0 z-40 h-full w-80 overflow-y-auto border-l border-[var(--line)] bg-[var(--ink)] p-5 shadow-2xl"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs tracking-[0.18em] text-[var(--fog)]">
          {detail.kind === "node" ? "角色详情" : "关系详情"}
        </span>
        <button type="button" onClick={onClose} aria-label="关闭详情">×</button>
      </div>
      {detail.kind === "node" ? (
        <>
          <h2 className="mt-8 text-2xl">{detail.node.label}</h2>
          <p className="mt-2 text-xs text-[var(--cinnabar-bright)]">
            {detail.node.faction_name ?? "势力未归档"}
          </p>
          <p className="mt-5 text-sm leading-7 text-[var(--fog)]">
            {detail.node.summary}
          </p>
          <Link
            href={`/characters/${detail.node.slug}`}
            className="mt-7 inline-block border border-[var(--line)] px-4 py-2 text-xs"
          >
            打开完整卷宗
          </Link>
        </>
      ) : (
        <>
          <p className="mt-8 text-xs text-[var(--cinnabar-bright)]">
            {LABELS[detail.edge.relation_type]}
          </p>
          <h2 className="mt-3 text-2xl">{detail.edge.label}</h2>
          <p className="mt-5 text-sm leading-7 text-[var(--fog)]">
            {detail.edge.summary}
          </p>
          <p className="mt-5 text-xs">
            {detail.edge.directional ? "有向关系" : "双向关系"}
          </p>
        </>
      )}
    </aside>
  );
}
