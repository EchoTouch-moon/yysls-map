import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ContentManager } from "@/components/admin/ContentManager";

const apiFetchMock = vi.fn();

vi.mock("@/lib/http", () => ({
  apiFetch: (...args: unknown[]) => apiFetchMock(...args),
}));

const bootstrap = {
  chapters: [
    {
      id: "chapter-1",
      slug: "qinghe",
      title: "清河",
      region: "清河",
      sort_order: 1,
      progress_key: "qinghe",
      progress_rank: 10,
      status: "published",
    },
  ],
  factions: [
    {
      id: "faction-1",
      slug: "tianquan",
      name: "天泉",
      faction_type: "门派",
      summary: "演示势力",
      spoiler_level: 0,
      visible_after_chapter_id: "chapter-1",
      status: "published",
    },
  ],
  characters: [
    {
      id: "character-1",
      slug: "renyi",
      name: "任意",
      summary: "演示角色一",
      interpretation: null,
      identity_tags: ["侠客"],
      faction_id: "faction-1",
      importance: 3,
      spoiler_level: 0,
      first_appear_chapter_id: "chapter-1",
      visible_after_chapter_id: "chapter-1",
      status: "published",
    },
    {
      id: "character-2",
      slug: "wuming",
      name: "无名",
      summary: "演示角色二",
      interpretation: null,
      identity_tags: [],
      faction_id: null,
      importance: 2,
      spoiler_level: 0,
      first_appear_chapter_id: "chapter-1",
      visible_after_chapter_id: "chapter-1",
      status: "published",
    },
  ],
  events: [
    {
      id: "event-1",
      slug: "first-meeting",
      title: "初遇",
      summary: "两人初次相遇。",
      impact: null,
      chapter_id: "chapter-1",
      sort_order: 1,
      spoiler_level: 0,
      visible_after_chapter_id: "chapter-1",
      status: "published",
      character_ids: ["character-1"],
      faction_ids: [],
    },
  ],
  relationships: [
    {
      id: "relationship-1",
      source_character_id: "character-1",
      target_character_id: "character-2",
      relation_type: "ally",
      label: "并肩",
      summary: "两人短暂同行。",
      stage: null,
      is_directional: false,
      chapter_id: "chapter-1",
      visible_after_chapter_id: "chapter-1",
      spoiler_level: 0,
      confidence: 0.8,
      status: "published",
      event_ids: ["event-1"],
    },
  ],
};

function successfulResponse() {
  return Promise.resolve({ data: bootstrap, error: null, meta: {} });
}

describe("ContentManager", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiFetchMock.mockImplementation(successfulResponse);
  });

  it("loads resources and switches tabs", async () => {
    render(<ContentManager csrf="csrf-token" />);

    expect(screen.getByText("正在读取内容…")).toBeInTheDocument();
    expect(await screen.findByText("清河")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "关系" }));
    expect(screen.getByText("并肩")).toBeInTheDocument();
    expect(screen.getByText("任意 → 无名")).toBeInTheDocument();
  });

  it("creates a chapter with typed values and CSRF", async () => {
    render(<ContentManager csrf="create-csrf" />);
    await screen.findByText("清河");

    fireEvent.change(screen.getByLabelText("Slug"), {
      target: { value: "kaifeng-extra" },
    });
    fireEvent.change(screen.getByLabelText("章节标题"), {
      target: { value: "开封别记" },
    });
    fireEvent.change(screen.getByLabelText("排序"), {
      target: { value: "12" },
    });
    fireEvent.change(screen.getByLabelText("进度值"), {
      target: { value: "20" },
    });
    fireEvent.click(screen.getByRole("button", { name: "创建" }));

    await waitFor(() => {
      const call = apiFetchMock.mock.calls.find(
        ([path, init]) =>
          path === "/admin/content/chapters" &&
          (init as RequestInit | undefined)?.method === "POST",
      );
      expect(call).toBeDefined();
      expect(call?.[1]).toMatchObject({
        headers: { "X-CSRF-Token": "create-csrf" },
      });
      expect(JSON.parse((call?.[1] as RequestInit).body as string)).toMatchObject(
        {
          slug: "kaifeng-extra",
          title: "开封别记",
          region: null,
          sort_order: 12,
          progress_key: "start",
          progress_rank: 20,
          status: "draft",
        },
      );
    });
  });

  it("updates an event and preserves multi-reference values", async () => {
    render(<ContentManager csrf="edit-csrf" />);
    await screen.findByText("清河");
    fireEvent.click(screen.getByRole("tab", { name: "事件" }));
    fireEvent.click(screen.getByRole("button", { name: "编辑" }));

    const characters = screen.getByLabelText(
      "关联角色",
    ) as HTMLSelectElement;
    for (const option of characters.options) {
      option.selected = ["character-1", "character-2"].includes(option.value);
    }
    fireEvent.change(characters);
    fireEvent.change(screen.getByLabelText("事件标题"), {
      target: { value: "再会" },
    });
    fireEvent.click(screen.getByRole("button", { name: "更新" }));

    await waitFor(() => {
      const call = apiFetchMock.mock.calls.find(
        ([path, init]) =>
          path === "/admin/content/events/event-1" &&
          (init as RequestInit | undefined)?.method === "PATCH",
      );
      const body = JSON.parse((call?.[1] as RequestInit).body as string);
      expect(body.title).toBe("再会");
      expect(body.character_ids).toEqual(["character-1", "character-2"]);
      expect(call?.[1]).toMatchObject({
        headers: { "X-CSRF-Token": "edit-csrf" },
      });
    });
  });

  it("requires confirmation before archiving", async () => {
    render(<ContentManager csrf="archive-csrf" />);
    await screen.findByText("清河");

    fireEvent.click(screen.getByRole("button", { name: "归档" }));
    expect(
      screen.getByRole("dialog", { name: "确认归档" }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "确认归档" }));

    await waitFor(() => {
      expect(apiFetchMock).toHaveBeenCalledWith(
        "/admin/content/chapters/chapter-1",
        {
          method: "DELETE",
          headers: { "X-CSRF-Token": "archive-csrf" },
        },
      );
    });
  });
});
