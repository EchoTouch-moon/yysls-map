import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DetailPanel } from "@/components/graph/DetailPanel";

describe("DetailPanel", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("labels relationship confidence and loads its evidence", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          data: {
            sources: [
              {
                source_type: "community_analysis",
                title: "清河剧情整理",
                reference: "https://example.com/qinghe",
              },
            ],
          },
          error: null,
          meta: {},
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
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
    expect(await screen.findByText("社区整理")).toBeInTheDocument();
    expect(screen.getByText(/外部页面可能包含超出当前进度/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "清河剧情整理" })).toHaveAttribute(
      "href",
      "https://example.com/qinghe",
    );
  });
});
