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
};

export type RelationshipFlowEdge = Edge<
  RelationshipEdgeData,
  "relationship"
>;

const COLORS: Record<RelationType, string> = {
  mentor: "#66705a",
  family: "#cb4a37",
  enemy: "#b91c1c",
  ally: "#3b82f6",
  old_acquaintance: "#a9a68e",
  exploitation: "#d97706",
  hierarchy: "#8b5cf6",
  same_sect: "#2dd4bf",
  interest: "#ec4899",
  hidden: "#6b7280",
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
  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        markerEnd={markerEnd}
        style={{
          stroke: color,
          strokeOpacity: selected ? 1 : 0.72,
          strokeWidth: selected ? 2.5 : 1.5,
        }}
      />
      <EdgeLabelRenderer>
        <span
          className="pointer-events-none absolute border border-[var(--line)] bg-[var(--ink)] px-1.5 py-0.5 text-[9px] text-[var(--fog)]"
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
