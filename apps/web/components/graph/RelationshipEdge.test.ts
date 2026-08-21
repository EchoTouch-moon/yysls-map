import { describe, expect, it } from "vitest";

import {
  type RelationshipFlowEdge,
  withHoveredEdge,
} from "@/components/graph/RelationshipEdge";

const edges: RelationshipFlowEdge[] = [
  {
    id: "one",
    source: "a",
    target: "b",
    type: "relationship",
    data: {
      label: "旧识",
      relationType: "old_acquaintance",
      confidence: 0.8,
      directional: true,
      isCenterEdge: true,
    },
  },
  {
    id: "two",
    source: "b",
    target: "c",
    type: "relationship",
    data: {
      label: "同盟",
      relationType: "ally",
      confidence: 1,
      directional: false,
      isCenterEdge: false,
    },
  },
];

describe("withHoveredEdge", () => {
  it("updates hover state without losing required edge data", () => {
    const hovered = withHoveredEdge(edges, "two");

    expect(hovered[0].data).toMatchObject({
      label: "旧识",
      directional: true,
      isCenterEdge: true,
      isHovered: false,
    });
    expect(hovered[1].data).toMatchObject({
      label: "同盟",
      directional: false,
      isCenterEdge: false,
      isHovered: true,
    });
  });
});
