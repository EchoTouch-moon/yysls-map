import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EvidenceList } from "@/components/ui/EvidenceList";

describe("EvidenceList", () => {
  it("opens valid web references safely", () => {
    render(
      <EvidenceList
        sources={[
          {
            source_type: "official_reference",
            title: "官方剧情资料",
            reference: "https://example.com/story",
          },
        ]}
      />,
    );

    const link = screen.getByRole("link", { name: "官方剧情资料" });
    expect(link).toHaveAttribute("href", "https://example.com/story");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("does not turn unsafe reference schemes into links", () => {
    render(
      <EvidenceList
        sources={[
          {
            source_type: "player_note",
            title: "玩家现场记录",
            reference: "javascript:alert('unsafe')",
          },
        ]}
      />,
    );

    expect(screen.getByText("玩家现场记录")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "玩家现场记录" })).toBeNull();
  });
});
