import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminConsole } from "@/components/admin/AdminConsole";
import { AIDraftWorkbench } from "@/components/admin/AIDraftWorkbench";
import { CharacterProfile } from "@/components/characters/CharacterProfile";
import { DiscoveryWorkbench } from "@/components/discovery/DiscoveryWorkbench";
import { SubmissionForm } from "@/components/forms/SubmissionForm";
import { TimelineExplorer } from "@/components/timeline/TimelineExplorer";

function envelope<T>(data: T) {
  return new Response(
    JSON.stringify({ data, error: null, meta: {} }),
    { status: 200, headers: { "Content-Type": "application/json" } },
  );
}

describe("spoiler-aware workflows", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  function canonicalEnvelope(
    progress: string,
    options: {
      unlocked?: boolean;
      events?: unknown[];
      unplaced?: unknown[];
      beatIndex?: Record<string, string[]>;
    } = {},
  ) {
    const spine = options.events
      ? [
          {
            canonical_key: "wwm:qinghe:chapter-1",
            title: "第一章·神仙不渡",
            node_type: "chapter",
            parent_key: null,
            sort_order: 0,
            events: [],
          },
          {
            canonical_key: "wwm:qinghe:chapter-1:part-1",
            title: "又见新来燕",
            node_type: "main_part",
            parent_key: "wwm:qinghe:chapter-1",
            sort_order: 1,
            events: [],
          },
          {
            canonical_key: "wwm:qinghe:chapter-1:part-1:awaken",
            title: "竹林旧居线索",
            node_type: "main_quest",
            parent_key: "wwm:qinghe:chapter-1:part-1",
            sort_order: 1,
            events: options.events,
          },
        ]
      : [];
    return envelope({
      progress,
      chapter: { slug: "qinghe", title: "第一章·神仙不渡", region: "清河" },
      chapter_unlocked: options.unlocked ?? true,
      spine,
      beat_index: options.beatIndex ?? {},
      unplaced_events: options.unplaced ?? [],
    });
  }

  function eventOverlay(overrides: Record<string, unknown> = {}) {
    return {
      mapping_kind: "exact",
      slug: "p1-awaken",
      title: "红线唤醒",
      summary: "主角在竹林小屋醒来。",
      impact: "终局秘密影响的开始。",
      chapter_slug: "qinghe",
      chapter_title: "第一章·神仙不渡",
      characters: [{ slug: "hero", name: "主角" }],
      sources: [
        {
          source_type: "official_reference",
          title: "终局资料",
          reference: "https://example.com/ending",
        },
      ],
      relationships: [],
      historical_contexts: [
        {
          id: "future-history",
          slug: "future-history",
          title: "终局历史背景",
          period_label: "946",
          summary: "只应在全剧透进度出现。",
          fact_kind: "historical_fact",
          relation_kind: "setting",
          boundary_note: "受限历史说明。",
          editorial_note: null,
          references: [
            {
              reference_type: "史料",
              title: "终局史料",
              url: "https://example.com/history",
            },
          ],
        },
      ],
      beat: {
        role: "clue",
        guide: "为什么重要导读。",
        why_it_matters: "终局秘密为什么重要。",
        bridge: "前情承接。",
        next_question: "接下来？",
      },
      ...overrides,
    };
  }

  it("removes canonical guide content immediately when progress is lowered", async () => {
    let resolveStart: ((response: Response) => void) | undefined;
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/timeline/canonical?progress=unrestricted")) {
        return Promise.resolve(
          canonicalEnvelope("unrestricted", { events: [eventOverlay()] }),
        );
      }
      if (url.includes("/timeline/canonical?progress=start")) {
        return new Promise<Response>((resolve) => {
          resolveStart = resolve;
        });
      }
      throw new Error(`Unexpected request: ${url}`);
    });
    localStorage.setItem("yysls-progress", "unrestricted");
    render(<TimelineExplorer />);
    expect(await screen.findByText("竹林旧居线索")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "这里为什么重要 →" }));
    expect(await screen.findByText("终局资料")).toBeInTheDocument();
    expect(screen.getByText("终局历史背景")).toBeInTheDocument();

    localStorage.setItem("yysls-progress", "start");
    fireEvent(window, new Event("yysls-progress-change"));
    expect(screen.queryByText("竹林旧居线索")).not.toBeInTheDocument();
    expect(screen.queryByText("终局资料")).not.toBeInTheDocument();
    expect(screen.queryByText("终局历史背景")).not.toBeInTheDocument();
    expect(screen.getByText("正在展开故事卷轴…")).toBeInTheDocument();

    resolveStart?.(canonicalEnvelope("start", { unlocked: false }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(screen.getByText("完成本章主线后解锁连续故事导读。")).toBeInTheDocument();
  });

  it("does not render a deferred unrestricted canonical spine after progress is lowered", async () => {
    let resolveOld: ((response: Response) => void) | undefined;
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/timeline/canonical?progress=unrestricted")) {
        return new Promise<Response>((resolve) => {
          resolveOld = resolve;
        });
      }
      if (url.includes("/timeline/canonical?progress=start")) {
        return Promise.resolve(canonicalEnvelope("start", { unlocked: false }));
      }
      throw new Error(`Unexpected request: ${url}`);
    });
    localStorage.setItem("yysls-progress", "unrestricted");
    render(<TimelineExplorer />);
    localStorage.setItem("yysls-progress", "start");
    fireEvent(window, new Event("yysls-progress-change"));

    resolveOld?.(
      canonicalEnvelope("unrestricted", {
        events: [eventOverlay({ title: "延迟终局秘密" })],
      }),
    );
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("延迟终局秘密")).not.toBeInTheDocument();
    expect(screen.getByText("完成本章主线后解锁连续故事导读。")).toBeInTheDocument();
  });

  it("follows the WAI tab keyboard pattern for timeline modes", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/timeline/canonical")) {
        return Promise.resolve(canonicalEnvelope("start", { unlocked: false }));
      }
      if (url.includes("/timeline?")) {
        return Promise.resolve(envelope({ progress: "start", events: [] }));
      }
      throw new Error(`Unexpected request: ${url}`);
    });

    render(<TimelineExplorer />);
    const tablist = screen.getByRole("tablist", { name: "时间线阅读模式" });
    const [guideTab, eventsTab] = within(tablist).getAllByRole("tab");
    expect(within(tablist).getAllByRole("tab")).toHaveLength(2);
    expect(guideTab).toHaveAttribute("id", "guide-timeline-tab");
    expect(guideTab).toHaveAttribute("aria-controls", "story-guide-panel");
    expect(guideTab).toHaveAttribute("tabindex", "0");
    expect(eventsTab).toHaveAttribute("tabindex", "-1");
    expect(screen.getByRole("tabpanel")).toHaveAttribute(
      "aria-labelledby",
      "guide-timeline-tab",
    );

    guideTab.focus();
    fireEvent.keyDown(guideTab, { key: "ArrowRight" });
    await waitFor(() => expect(eventsTab).toHaveFocus());
    expect(eventsTab).toHaveAttribute("aria-selected", "true");
    expect(eventsTab).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("tabpanel")).toHaveAttribute(
      "aria-labelledby",
      "events-timeline-tab",
    );

    fireEvent.keyDown(eventsTab, { key: "Home" });
    await waitFor(() => expect(guideTab).toHaveFocus());
    expect(guideTab).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(guideTab, { key: "End" });
    await waitFor(() => expect(eventsTab).toHaveFocus());
    fireEvent.keyDown(eventsTab, { key: "ArrowLeft" });
    await waitFor(() => expect(guideTab).toHaveFocus());
  });

  it("switches between canonical story reading and complete events", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/timeline/canonical")) {
        return Promise.resolve(
          canonicalEnvelope("unrestricted", {
            events: [
              eventOverlay({
                characters: [
                  { slug: "hero", name: "主角" },
                  { slug: "hongxian", name: "红线" },
                ],
                historical_contexts: [
                  {
                    id: "h1",
                    slug: "h1",
                    title: "滹沱河中渡桥：王清与杜重威",
                    period_label: "946",
                    summary: "史实摘要。",
                    fact_kind: "historical_fact",
                    relation_kind: "fictionalized",
                    boundary_note: "拒援后谋降可证。",
                    editorial_note: null,
                    references: [
                      {
                        reference_type: "史料",
                        title: "《资治通鉴》卷二百八十五",
                        url: "https://example.com/zztj",
                        locator: "开运三年十一月至十二月",
                      },
                    ],
                  },
                ],
              }),
            ],
          }),
        );
      }
      if (url.includes("/timeline?")) {
        return Promise.resolve(
          envelope({
            progress: "unrestricted",
            events: [
              {
                id: "ev-1",
                slug: "p1-awaken",
                title: "红线唤醒主角",
                summary: "完整事件记录。",
                impact: null,
                chapter_slug: "qinghe",
                chapter_title: "第一章·神仙不渡",
                sort_order: 2,
                characters: [],
                sources: [],
              },
            ],
          }),
        );
      }
      throw new Error(`Unexpected request: ${url}`);
    });

    render(<TimelineExplorer />);
    // canonical-first continuous scroll: no beat navigation controls
    expect(await screen.findByText("竹林旧居线索")).toBeInTheDocument();
    expect(screen.getByText("又见新来燕")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "这里为什么重要 →" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /上一节|下一节/ })).not.toBeInTheDocument();

    // click drills into interpretation, it never advances the story
    fireEvent.click(screen.getByRole("button", { name: "这里为什么重要 →" }));
    expect(screen.getByText("终局秘密为什么重要。")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "红线" })).toHaveAttribute(
      "href",
      "/characters/hongxian",
    );
    fireEvent.click(screen.getByText("滹沱河中渡桥：王清与杜重威"));
    expect(screen.getByText(/拒援后谋降可证/)).toBeInTheDocument();
    expect(screen.getByText(/定位：开运三年十一月至十二月/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "《资治通鉴》卷二百八十五" }),
    ).toHaveAttribute("rel", "noopener noreferrer");

    fireEvent.click(screen.getByRole("tab", { name: "完整事件" }));
    expect(await screen.findByText("完整事件记录。")).toBeInTheDocument();
    expect(screen.getByLabelText("章节")).toBeInTheDocument();
    expect(screen.queryByText("竹林旧居线索")).not.toBeInTheDocument();
  });

  it("submits a relationship as a pending moderation item", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        envelope({
          id: "submission-id",
          status: "pending",
          message: "投稿已进入审核。",
        }),
      );
    render(<SubmissionForm />);

    fireEvent.change(screen.getByLabelText("线索标题"), {
      target: { value: "两名角色的旧识线索" },
    });
    fireEvent.change(screen.getByLabelText("起点角色 slug"), {
      target: { value: "demo-character-01-01" },
    });
    fireEvent.change(screen.getByLabelText("终点角色 slug"), {
      target: { value: "demo-character-01-02" },
    });
    fireEvent.change(screen.getByLabelText("内容摘要"), {
      target: { value: "这是一段超过十个字的原创关系摘要。" },
    });
    fireEvent.change(screen.getByLabelText("来源与判断依据"), {
      target: { value: "依据演示任务中的两段对话与共同事件判断。" },
    });
    fireEvent.click(screen.getByRole("button", { name: "提交人工审核" }));

    expect(await screen.findByText("投稿已进入审核。")).toBeInTheDocument();
    const request = fetchMock.mock.calls[0];
    expect(request[0]).toContain("/submissions");
    expect(JSON.parse(String(request[1]?.body))).toMatchObject({
      submission_type: "relationship",
      payload: {
        source_character_slug: "demo-character-01-01",
        target_character_slug: "demo-character-01-02",
      },
    });
  });

  it("shows source evidence in a visible character dossier", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      envelope({
        id: "character-a",
        slug: "character-a",
        name: "甲",
        summary: "当前进度可见的人物摘要。",
        interpretation: null,
        identity_tags: [],
        faction_name: null,
        first_appear_chapter: "第一章",
        sources: [
          {
            source_type: "quest_reference",
            title: "任务现场定位",
            reference: "https://example.com/quest",
          },
        ],
      }),
    );

    render(<CharacterProfile slug="character-a" />);

    expect(await screen.findByText("任务现场定位")).toBeInTheDocument();
    expect(screen.getByText("任务定位")).toBeInTheDocument();
  });

  it("stores the CSRF token and loads pending submissions after login", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = String(input);
      if (url.endsWith("/admin/session") && init?.method === "POST") {
        return Promise.resolve(
          envelope({
            username: "admin",
            csrf_token: "csrf-test-token",
            expires_in_minutes: 30,
          }),
        );
      }
      if (url.includes("/admin/submissions")) {
        return Promise.resolve(envelope([]));
      }
      throw new Error(`Unexpected request: ${url}`);
    });
    render(<AdminConsole />);
    fireEvent.change(screen.getByLabelText("管理员账号"), {
      target: { value: "admin" },
    });
    fireEvent.change(screen.getByLabelText("密码"), {
      target: { value: "correct horse battery staple" },
    });
    fireEvent.click(screen.getByRole("button", { name: "进入审核台" }));

    expect(await screen.findByText("暂无待审核线索。")).toBeInTheDocument();
    expect(sessionStorage.getItem("yysls-admin-csrf")).toBe("csrf-test-token");
  });

  it("renders a bounded relationship path in API order", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      envelope({
        found: true,
        nodes: [
          { id: "a", slug: "character-a", name: "甲" },
          { id: "b", slug: "character-b", name: "乙" },
          { id: "c", slug: "character-c", name: "丙" },
        ],
        edges: [
          {
            id: "ab",
            source: "a",
            target: "b",
            label: "旧识",
            relation_type: "old_acquaintance",
          },
          {
            id: "bc",
            source: "b",
            target: "c",
            label: "同盟",
            relation_type: "ally",
          },
        ],
      }),
    );
    render(<DiscoveryWorkbench />);
    fireEvent.change(screen.getByLabelText("起点 slug"), {
      target: { value: "character-a" },
    });
    fireEvent.change(screen.getByLabelText("终点 slug"), {
      target: { value: "character-c" },
    });
    fireEvent.click(screen.getByRole("button", { name: "寻找最短关系链" }));
    expect(await screen.findByText("—旧识→")).toBeInTheDocument();
    expect(screen.getByText("—同盟→")).toBeInTheDocument();
  });

  it("shows the disabled AI boundary without creating candidates", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "AI 辅助功能尚未启用。" }), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      }),
    );
    render(<AIDraftWorkbench csrf="csrf-token" />);
    fireEvent.change(screen.getByLabelText("原创笔记"), {
      target: { value: "这是一段超过二十个字、只用于测试关闭状态的原创玩家笔记。" },
    });
    fireEvent.click(screen.getByRole("button", { name: "生成待审草稿" }));
    expect(await screen.findByText("AI 辅助功能尚未启用。")).toBeInTheDocument();
    expect(screen.queryByText("接受候选")).not.toBeInTheDocument();
  });
});
