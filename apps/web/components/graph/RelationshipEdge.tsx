import { memo } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  type Edge,
  type EdgeProps,
} from "@xyflow/react";

import type { RelationType } from "@/lib/graph";

export type RelationshipEdgeData = Record<string, unknown> & {
  label: string;
  relationType: RelationType;
  confidence: number;
};

export type RelationshipFlowEdge = Edge<
  RelationshipEdgeData,
  "relationship"
>;

const COLORS: Record<RelationType, string> = {
  mentor: "#7f8a6b",
  family: "#c04a36",
  enemy: "#9f322b",
  ally: "#78908a",
  old_acquaintance: "#a99c7d",
  exploitation: "#a26b35",
  hierarchy: "#786b58",
  same_sect: "#607d6a",
  interest: "#9a7258",
  hidden: "#746f64",
};

function RelationshipEdgeInner({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  data,
  selected,
}: EdgeProps<RelationshipFlowEdge>) {
  const [path, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    borderRadius: 12,
  });
  const color = COLORS[data?.relationType ?? "hidden"];
  const confidence = data?.confidence ?? 1;

  const labelClassName = selected
    ? "pointer-events-none absolute border border-[var(--cinnabar-bright)] bg-[var(--cinnabar)] px-2.5 py-0.5 text-[10px] tracking-[0.08em] text-white shadow-xl rounded-sm transition-[border-color,background-color,color,box-shadow] duration-200"
    : "pointer-events-none absolute border border-[rgba(217,201,164,.28)] bg-[rgba(28,25,20,.94)] px-2 py-0.5 text-[9px] tracking-[0.08em] text-[var(--paper-deep)] shadow-lg rounded-sm transition-[border-color,background-color,color,box-shadow] duration-200";

  return (
    <>
      {/* Background shadow glow line when selected */}
      {selected && (
        <BaseEdge
          id={`${id}-glow`}
          path={path}
          style={{
            stroke: color,
            strokeOpacity: 0.35,
            strokeWidth: 6,
          }}
        />
      )}
      <BaseEdge
        id={id}
        path={path}
        markerEnd={markerEnd}
        style={{
          stroke: color,
          strokeOpacity: selected ? 1 : 0.72,
          strokeWidth: selected ? 2.5 : 1.5,
          strokeDasharray: confidence < 0.7 ? "4 5" : undefined,
        }}
      />
      <EdgeLabelRenderer>
        <span
          className={labelClassName}
          style={{
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
          }}
        >
          {data?.label}
        </span>
      </EdgeLabelRenderer>
    </>
  );
}

export const RelationshipEdge = memo(RelationshipEdgeInner);
