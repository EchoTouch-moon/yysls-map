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

function confidenceLabel(confidence: number): string {
  if (confidence >= 0.9) return "明确事实";
  if (confidence >= 0.7) return "可信整理";
  return "待考解读";
}

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
      className="xuan-paper absolute right-0 top-0 z-40 h-full w-80 overflow-y-auto border-l border-[var(--line-strong)] p-6 pl-8 shadow-[-10px_0_30px_rgba(0,0,0,0.5)] transition-[transform,opacity] duration-300"
    >
      {/* Decorative vertical binding threads on the left of detail panel */}
      <div className="absolute left-0 top-0 bottom-0 w-4 border-r border-[var(--line)] bg-black/10 pointer-events-none" />
      <div className="absolute left-1.5 top-[15%] w-1.5 h-0.5 bg-[var(--paper-deep)] opacity-40 pointer-events-none" />
      <div className="absolute left-1.5 top-[50%] w-1.5 h-0.5 bg-[var(--paper-deep)] opacity-40 pointer-events-none" />
      <div className="absolute left-1.5 top-[85%] w-1.5 h-0.5 bg-[var(--paper-deep)] opacity-40 pointer-events-none" />

      <div className="flex items-center justify-between">
        <span className="text-xs tracking-[0.18em] text-[var(--cinnabar-bright)] font-medium">
          {detail.kind === "node" ? "角色详情" : "关系详情"}
        </span>
        <button
          type="button"
          onClick={onClose}
          aria-label="关闭详情"
          className="grid size-8 place-items-center border border-[var(--line)] text-[var(--fog)] transition hover:border-[var(--paper-deep)] hover:text-[var(--paper)]"
        >
          ×
        </button>
      </div>
      {detail.kind === "node" ? (
        <>
          <h2 className="mt-8 text-2xl font-semibold text-[var(--paper-light)] tracking-wide">{detail.node.label}</h2>
          <p className="mt-2 text-xs text-[var(--cinnabar-bright)] font-medium">
            {detail.node.faction_name ?? "势力未归档"}
          </p>
          <p className="mt-5 text-sm leading-7 text-[var(--paper)]">
            {detail.node.summary}
          </p>
          <Link
            href={`/characters/${detail.node.slug}`}
            className="archive-button mt-7 inline-block shadow-sm"
          >
            打开完整卷宗
          </Link>
        </>
      ) : (
        <>
          <p className="mt-8 text-xs text-[var(--cinnabar-bright)] font-medium">
            {LABELS[detail.edge.relation_type]}
          </p>
          <h2 className="mt-3 text-2xl font-semibold text-[var(--paper-light)] tracking-wide">{detail.edge.label}</h2>
          <p className="mt-5 text-sm leading-7 text-[var(--paper)]">
            {detail.edge.summary}
          </p>
          <p className="mt-5 text-xs text-[var(--fog)]">
            {detail.edge.directional ? "有向关系" : "双向关系"}
          </p>
          <div className="mt-5 border-t border-[var(--line)] pt-4">
            <p className="text-xs tracking-[0.16em] text-[var(--fog)]">
              资料性质
            </p>
            <p className="mt-2 text-sm text-[var(--paper-light)] font-medium">
              {confidenceLabel(detail.edge.confidence)}
              <span className="ml-2 text-xs text-[var(--cinnabar-bright)]">
                {Math.round(detail.edge.confidence * 100)}%
              </span>
              <span className="ml-1 text-xs text-[var(--fog)] font-normal">
                可信度
              </span>
            </p>
            <p className="mt-2 text-xs leading-6 text-[var(--fog)]">
              玩家亲历与社区解读也会收录；可信度用于区分明确剧情和待考推断。
            </p>
          </div>
        </>
      )}

      {/* Small authenticity seal at the bottom */}
      <div className="mt-12 flex justify-end opacity-[0.28] pointer-events-none select-none" aria-hidden="true">
        <div className="border border-[var(--cinnabar-bright)] px-2 py-1 text-[9px] text-[var(--cinnabar-bright)] font-bold tracking-widest rotate-[-6deg]">
          燕云已阅
        </div>
      </div>
    </aside>
  );
}
