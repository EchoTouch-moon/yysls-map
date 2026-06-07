import { memo } from "react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";

export type CharacterNodeData = Record<string, unknown> & {
  label: string;
  factionName: string | null;
  importance: number;
};

export type CharacterFlowNode = Node<CharacterNodeData, "character">;

function CharacterNodeInner({ data, selected }: NodeProps<CharacterFlowNode>) {
  const size = 62 + Math.max(0, data.importance - 1) * 8;
  return (
    <div
      className={`grid place-items-center border bg-[var(--ink-soft)] text-center shadow-xl transition ${
        selected
          ? "border-[var(--cinnabar-bright)] outline outline-4 outline-[rgba(203,74,55,.16)]"
          : "border-[var(--line)] hover:border-[var(--paper)]"
      }`}
      style={{ width: size, height: size }}
    >
      <Handle type="target" position={Position.Top} className="!opacity-0" />
      <Handle type="source" position={Position.Bottom} className="!opacity-0" />
      <div className="min-w-0 px-2">
        <span className="block truncate text-xs">{data.label}</span>
        {data.factionName && (
          <span className="mt-1 block truncate text-[9px] text-[var(--fog)]">
            {data.factionName}
          </span>
        )}
      </div>
    </div>
  );
}

export const CharacterNode = memo(CharacterNodeInner);
