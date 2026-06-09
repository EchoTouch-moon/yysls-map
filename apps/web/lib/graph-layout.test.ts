import { describe, expect, it } from "vitest";

import { getCenteredGraphPositions } from "@/lib/graph-layout";
import type { GraphEdge, GraphNode } from "@/lib/graph";

const nodes: GraphNode[] = [
  {
    id: "hero",
    slug: "protagonist",
    label: "主角",
    faction_id: null,
    faction_name: null,
    importance: 5,
    summary: "",
  },
  {
    id: "jiang",
    slug: "jiang-yan",
    label: "江晏",
    faction_id: null,
    faction_name: null,
    importance: 5,
    summary: "",
  },
  {
    id: "hongxian",
    slug: "zhou-hongxian",
    label: "周红线",
    faction_id: null,
    faction_name: null,
    importance: 5,
    summary: "",
  },
];

const edges: GraphEdge[] = [
  {
    id: "one",
    source: "hero",
    target: "jiang",
    relation_type: "family",
    label: "养父子",
    summary: "",
    directional: true,
    confidence: 1,
  },
  {
    id: "two",
    source: "hero",
    target: "hongxian",
    relation_type: "ally",
    label: "同伴",
    summary: "",
    directional: false,
    confidence: 1,
  },
];

describe("getCenteredGraphPositions", () => {
  it("places the requested focus at the origin", () => {
    const positions = getCenteredGraphPositions(nodes, edges, "protagonist");
    expect(positions.get("hero")).toEqual({ x: 0, y: 0 });
  });

  it("places direct relations around the center", () => {
    const positions = getCenteredGraphPositions(nodes, edges, "protagonist");
    expect(positions.get("jiang")).not.toEqual({ x: 0, y: 0 });
    expect(positions.get("hongxian")).not.toEqual({ x: 0, y: 0 });
  });

  it("falls back to the first visible node for an unknown focus", () => {
    const positions = getCenteredGraphPositions(nodes, edges, "unknown");
    expect(positions.get("hero")).toEqual({ x: 0, y: 0 });
  });
});
