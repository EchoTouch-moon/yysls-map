import type { GraphEdge, GraphNode } from "@/lib/graph";

export type GraphPosition = {
  x: number;
  y: number;
};

export function getCenteredGraphPositions(
  nodes: GraphNode[],
  edges: GraphEdge[],
  focusSlug: string,
): Map<string, GraphPosition> {
  const positions = new Map<string, GraphPosition>();
  const center = nodes.find((node) => node.slug === focusSlug) ?? nodes[0];
  if (!center) return positions;

  positions.set(center.id, { x: 0, y: 0 });

  const degrees = new Map<string, number>();
  for (const edge of edges) {
    degrees.set(edge.source, (degrees.get(edge.source) ?? 0) + 1);
    degrees.set(edge.target, (degrees.get(edge.target) ?? 0) + 1);
  }

  const orbit = nodes
    .filter((node) => node.id !== center.id)
    .sort(
      (left, right) =>
        (degrees.get(right.id) ?? 0) - (degrees.get(left.id) ?? 0) ||
        right.importance - left.importance ||
        left.label.localeCompare(right.label, "zh-CN"),
    );

  const innerCount = Math.min(12, orbit.length);
  placeRing(positions, orbit.slice(0, innerCount), 360, -Math.PI / 2);
  placeRing(
    positions,
    orbit.slice(innerCount),
    590,
    -Math.PI / 2 + Math.PI / Math.max(1, orbit.length - innerCount),
  );

  return positions;
}

function placeRing(
  positions: Map<string, GraphPosition>,
  nodes: GraphNode[],
  radius: number,
  offset: number,
) {
  nodes.forEach((node, index) => {
    const angle = offset + (index / nodes.length) * Math.PI * 2;
    positions.set(node.id, {
      x: Math.cos(angle) * radius,
      y: Math.sin(angle) * radius,
    });
  });
}
