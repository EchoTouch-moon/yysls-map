import { describe, expect, it } from "vitest";

import { getRelationshipEdgeGeometry } from "@/lib/graph-edge-geometry";

describe("getRelationshipEdgeGeometry", () => {
  it("keeps edges connected to the center straight", () => {
    const geometry = getRelationshipEdgeGeometry({
      id: "center-edge",
      sourceX: 80,
      sourceY: 40,
      targetX: 360,
      targetY: 40,
      isCenterEdge: true,
    });

    expect(geometry.path).toBe("M 80 40 L 360 40");
    expect(geometry.arrowY).toBe(40);
    expect(geometry.arrowAngle).toBe(0);
  });

  it("curves outer-ring edges and returns finite arrow geometry", () => {
    const geometry = getRelationshipEdgeGeometry({
      id: "outer-edge",
      sourceX: -200,
      sourceY: 120,
      targetX: 200,
      targetY: 120,
      isCenterEdge: false,
    });

    expect(geometry.path).toContain(" Q ");
    expect(geometry.path).not.toContain(" Q 0 120 ");
    expect(Number.isFinite(geometry.arrowX)).toBe(true);
    expect(Number.isFinite(geometry.arrowY)).toBe(true);
    expect(Number.isFinite(geometry.arrowAngle)).toBe(true);
  });

  it("places labels deterministically from the edge id", () => {
    const input = {
      id: "stable-edge",
      sourceX: 10,
      sourceY: 20,
      targetX: 300,
      targetY: 180,
      isCenterEdge: false,
    };

    expect(getRelationshipEdgeGeometry(input)).toEqual(
      getRelationshipEdgeGeometry(input),
    );
    expect(
      getRelationshipEdgeGeometry({ ...input, id: "different-edge" }).labelX,
    ).not.toBe(getRelationshipEdgeGeometry(input).labelX);
  });
});
