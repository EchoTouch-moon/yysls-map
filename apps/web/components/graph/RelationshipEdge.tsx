import { memo } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  type Edge,
  type EdgeProps,
} from "@xyflow/react";

import type { RelationType } from "@/lib/graph";
import { getRelationshipEdgeGeometry } from "@/lib/graph-edge-geometry";

export type RelationshipEdgeData = Record<string, unknown> & {
  label: string;
  relationType: RelationType;
  confidence: number;
  directional: boolean;
  isCenterEdge: boolean;
  isHovered?: boolean;
};

export type RelationshipFlowEdge = Edge<
  RelationshipEdgeData,
  "relationship"
> & {
  data: RelationshipEdgeData;
};

export function withHoveredEdge(
  edges: RelationshipFlowEdge[],
  hoveredId: string | null,
) {
  return edges.map((edge) => ({
    ...edge,
    data: {
      ...edge.data,
      isHovered: edge.id === hoveredId,
    },
  }));
}

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
  data,
  selected,
}: EdgeProps<RelationshipFlowEdge>) {
  const isHovered = Boolean(data?.isHovered);
  const geometry = getRelationshipEdgeGeometry({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    isCenterEdge: data?.isCenterEdge ?? false,
  });
  const color = COLORS[data?.relationType ?? "hidden"];
  const confidence = data?.confidence ?? 1;
  const active = selected || isHovered;
  const labelClassName = active
    ? "pointer-events-none absolute border border-[var(--cinnabar-bright)] bg-[var(--cinnabar)] px-3 py-1 text-[11px] font-bold tracking-[0.1em] text-white shadow-[0_4px_20px_rgba(229,90,66,0.6)] rounded-sm transition-all duration-300"
    : "pointer-events-none absolute border border-[rgba(217,201,164,.28)] bg-[rgba(28,25,20,.94)] px-2 py-0.5 text-[9px] tracking-[0.08em] text-[var(--paper-deep)] shadow-lg rounded-sm transition-all duration-300";

  return (
    <>
      {active && (
        <BaseEdge
          id={`${id}-glow`}
          path={geometry.path}
          style={{
            stroke: color,
            strokeOpacity: 0.45,
            strokeWidth: 8,
          }}
        />
      )}

      <BaseEdge
        id={id}
        path={geometry.path}
        interactionWidth={25}
        style={{
          stroke: color,
          strokeOpacity: active ? 1 : 0.72,
          strokeWidth: active ? 3 : 1.5,
          strokeDasharray: confidence < 0.7 ? "4 5" : undefined,
          zIndex: active ? 40 : 10,
        }}
      />

      {data?.directional && (
        <polygon
          points="-5,-4 5,0 -5,4"
          fill={color}
          transform={`translate(${geometry.arrowX}, ${geometry.arrowY}) rotate(${geometry.arrowAngle})`}
          style={{ pointerEvents: "none", zIndex: active ? 40 : 10 }}
        />
      )}

      <EdgeLabelRenderer>
        <span
          className={labelClassName}
          style={{
            zIndex: active ? 50 : 20,
            transform: `translate(-50%, -50%) translate(${geometry.labelX}px, ${geometry.labelY}px) scale(${active ? 1.15 : 1})`,
          }}
        >
          {data?.label}
        </span>
      </EdgeLabelRenderer>
    </>
  );
}

export const RelationshipEdge = memo(RelationshipEdgeInner);
