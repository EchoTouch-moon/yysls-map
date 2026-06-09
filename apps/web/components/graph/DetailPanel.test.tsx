import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DetailPanel } from "@/components/graph/DetailPanel";

describe("DetailPanel", () => {
  it("labels player interpretation relationships by confidence", () => {
    render(
      <DetailPanel
        detail={{
          kind: "edge",
          edge: {
            id: "relationship-1",
            source: "character-a",
            target: "character-b",
            relation_type: "hidden",
            label: "身份推断",
            summary: "依据玩家亲历和场景线索整理。",
            directional: false,
            confidence: 0.6,
          },
        }}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByText("待考解读")).toBeInTheDocument();
    expect(screen.getByText("60%")).toBeInTheDocument();
    expect(screen.getByText(/玩家亲历与社区解读也会收录/)).toBeInTheDocument();
  });
});
