import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CharacterProfile } from "@/components/characters/CharacterProfile";

function apiResponse(payload: unknown) {
  return new Response(JSON.stringify({ data: payload, error: null, meta: {} }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

const baseDetail = {
  id: "c1",
  slug: "jiang-yan",
  name: "江晏",
  summary: "养父，保护主角长大的侠客。",
  interpretation: "完整解析：他的失踪与十六年前旧事有关。",
  identity_tags: ["养父", "清河线"],
  faction_name: null,
  first_appear_chapter: "第一章·神仙不渡",
  sources: [],
};

const graphResponse = {
  nodes: [
    { id: "n-jiang", slug: "jiang-yan", label: "江晏" },
    { id: "n-protagonist", slug: "protagonist", label: "主角" },
    { id: "n-wangqing", slug: "wang-qing", label: "王清" },
  ],
  edges: [
    { id: "e1", source: "n-jiang", target: "n-protagonist", label: "抚养" },
    { id: "e2", source: "n-wangqing", target: "n-jiang", label: "十六年前旧事" },
  ],
};

describe("CharacterProfile progressive reading (Wave 1)", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("yysls-progress", "qinghe");
    vi.restoreAllMocks();
  });

  it("renders sections in the order 初识 → 剧情足迹 → 关系 → 解析 → 历史", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/characters/jiang-yan")) {
        return Promise.resolve(
          apiResponse({
            ...baseDetail,
            story_path: [
              {
                arc_slug: "qinghe-main-journey",
                arc_title: "清河主线",
                beat_sort_order: 3,
                role: "turning_point",
                guide: "江晏在雨夜护送主角出城。",
                event_slug: "evt-escape",
                event_title: "江晏携婴出逃",
                event_summary: "事件概要。",
                why_it_matters: "这一幕奠定了全篇的追寻动机。",
                historical: [{ slug: "hist-five-dynasties", title: "五代十国", relation_kind: "setting" }],
              },
            ],
          }),
        );
      }
      if (url.includes("/graph?focus=jiang-yan")) {
        return Promise.resolve(apiResponse(graphResponse));
      }
      return Promise.reject(new Error(`unexpected fetch: ${url}`));
    });

    render(<CharacterProfile slug="jiang-yan" />);

    await waitFor(() => {
      expect(screen.getByText("江晏携婴出逃")).toBeInTheDocument();
    });
    expect(screen.getByRole("heading", { name: "初识" })).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { name: "剧情足迹" })[0]).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /他与谁相连/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /显示该人物的完整解析/ })).toBeInTheDocument();

    const order = [
      screen.getByRole("heading", { name: "初识" }),
      ...screen.getAllByRole("heading", { name: "剧情足迹" }),
      screen.getByRole("heading", { name: /他与谁相连/ }),
    ];
    const positions = order.map((el) => el.compareDocumentPosition(order[0]));
    expect(positions.every((p) => p === 0 || typeof p === "number")).toBe(true);

    // 深链：足迹 → 导读对应幕
    expect(screen.getByText(/在导读中阅读这一幕/)).toHaveAttribute(
      "href",
      "/timeline?beat=evt-escape",
    );
    // 历史背景 chips → /history/[slug]
    expect(screen.getByText("五代十国")).toHaveAttribute("href", "/history/hist-five-dynasties");
  });

  it("hides full interpretation behind an explicit page-level reveal (G4)", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/characters/jiang-yan")) {
        expect(url).not.toContain("reveal=true");
        return Promise.resolve(apiResponse({ ...baseDetail, story_path: [] }));
      }
      if (url.includes("/graph")) {
        return Promise.resolve(apiResponse(graphResponse));
      }
      return Promise.reject(new Error(`unexpected fetch: ${url}`));
    });

    render(<CharacterProfile slug="jiang-yan" />);
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "江晏" })).toBeInTheDocument();
    });
    expect(screen.queryByText(/完整解析：他的失踪/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /显示该人物的完整解析/ }));

    await waitFor(() => {
      expect(screen.getByText(/完整解析：他的失踪/)).toBeInTheDocument();
    });
    const revealCalls = fetchSpy.mock.calls.filter(([input]) =>
      String(input).includes("reveal=true"),
    );
    expect(revealCalls.length).toBeGreaterThan(0);
  });
});
