import { memo } from "react";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";

export type CharacterNodeData = Record<string, unknown> & {
  label: string;
  factionName: string | null;
  importance: number;
  isCenter: boolean;
};

export type CharacterFlowNode = Node<CharacterNodeData, "character">;

function CharacterNodeInner({ data, selected }: NodeProps<CharacterFlowNode>) {
  const width = data.isCenter ? 142 : 82 + Math.max(0, data.importance - 1) * 6;
  const height = data.isCenter ? 116 : 68 + Math.max(0, data.importance - 1) * 4;
  return (
    <div
      className={`character-slip grid place-items-center text-center transition-[transform,border-color,background-color,box-shadow,opacity] ${
        data.isCenter ? "character-slip-center" : ""
      } ${
        selected
          ? "character-slip-selected"
          : ""
      }`}
      style={{ width, height }}
    >
      <Handle type="target" position={Position.Top} className="!opacity-0" />
      <Handle type="source" position={Position.Bottom} className="!opacity-0" />

      {/* Decorative watermark for the center character */}
      {data.isCenter && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none select-none animate-seal-breath" aria-hidden="true">
          <svg width="86" height="86" viewBox="0 0 100 100" fill="none" stroke="currentColor" className="text-[var(--cinnabar-bright)]">
            <circle cx="50" cy="50" r="42" strokeWidth="2.5" />
            <circle cx="50" cy="50" r="35" strokeWidth="1" strokeDasharray="3 3" />
            <text x="50" y="55" textAnchor="middle" fill="currentColor" stroke="none" fontSize="15" fontFamily="Songti SC, serif" fontWeight="bold" letterSpacing="2">卷主</text>
          </svg>
        </div>
      )}

      <div className="relative z-10 min-w-0 px-2">
        {data.isCenter && (
          <span className="mb-2 block text-[9px] tracking-[0.28em] text-[var(--cinnabar-bright)]">
            当前卷主
          </span>
        )}
        <span className={`block truncate ${data.isCenter ? "text-lg" : "text-xs"} font-medium`}>
          {data.label}
        </span>
        {data.factionName && (
          <span className="mt-1.5 block truncate text-[9px] text-[var(--fog)]">
            {data.factionName}
          </span>
        )}
      </div>
    </div>
  );
}

export const CharacterNode = memo(CharacterNodeInner);
