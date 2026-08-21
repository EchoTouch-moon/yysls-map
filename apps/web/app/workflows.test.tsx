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

  it("removes old guide and historical context immediately when progress is lowered", async () => {
    let resolveStart: ((response: Response) => void) | undefined;
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        envelope({
          progress: "unrestricted",
          arcs: [
            {
              id: "ending-journey",
              slug: "ending-journey",
              title: "终局导读",
              summary: "仅限全剧透进度的导读。",
              core_question: "终局的真相是什么？",
              estimated_minutes: 12,
              beat_count: 1,
            },
          ],
        }),
      )
      .mockResolvedValueOnce(
        envelope({
          id: "ending-journey",
          slug: "ending-journey",
          title: "终局导读",
          summary: "仅限全剧透进度的导读。",
          core_question: "终局的真相是什么？",
          estimated_minutes: 12,
          beats: [
            {
              id: "ending-beat",
              sort_order: 1,
              role: "回收",
              guide: "终局秘密只应在全部可见时出现。",
              why_it_matters: "这是结局的意义。",
              bridge: "前情承接。",
              next_question: "还有什么秘密？",
              event: {
                slug: "future-event",
                title: "终局秘密",
                summary: "只应在全部可见时出现。",
                impact: null,
                characters: [],
                sources: [
                  {
                    source_type: "official_reference",
                    title: "终局资料",
                    reference: "https://example.com/ending",
                  },
                ],
              },
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
            },
          ],
        }),
      )
      .mockImplementationOnce(
        () =>
          new Promise<Response>((resolve) => {
            resolveStart = resolve;
          }),
      );
    localStorage.setItem("yysls-progress", "unrestricted");
    render(<TimelineExplorer />);
    expect((await screen.findAllByText("终局秘密")).length).toBeGreaterThan(0);
    expect(screen.getByText("终局资料")).toBeInTheDocument();
    expect(screen.getByText("终局历史背景")).toBeInTheDocument();

    localStorage.setItem("yysls-progress", "start");
    fireEvent(window, new Event("yysls-progress-change"));
    expect(screen.queryByText("终局秘密")).not.toBeInTheDocument();
    expect(screen.queryByText("终局资料")).not.toBeInTheDocument();
    expect(screen.queryByText("终局历史背景")).not.toBeInTheDocument();
    expect(screen.getByText("正在展开故事卷轴…")).toBeInTheDocument();

    resolveStart?.(envelope({ progress: "start", arcs: [] }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  });

  it("does not render a deferred unrestricted detail after progress is lowered", async () => {
    let resolveOldDetail: ((response: Response) => void) | undefined;
    const oldDetail = {
      id: "ending-journey",
      slug: "ending-journey",
      title: "终局导读",
      summary: "旧导读。",
      core_question: "旧问题？",
      estimated_minutes: 12,
      beats: [
        {
          id: "ending-beat",
          sort_order: 10,
          role: "resolution",
          guide: "延迟抵达的终局受限导读。",
          why_it_matters: "旧重要性。",
          bridge: "旧承接。",
          next_question: "旧问题？",
          event: {
            slug: "future-event",
            title: "延迟终局秘密",
            summary: "旧摘要。",
            impact: null,
            characters: [],
            sources: [],
          },
          relationships: [],
          historical_contexts: [],
        },
      ],
    };
    const startDetail = {
      id: "start-journey",
      slug: "start-journey",
      title: "开篇导读",
      summary: "安全导读。",
      core_question: "开篇问题？",
      estimated_minutes: 3,
      beats: [
        {
          id: "start-beat",
          sort_order: 1,
          role: "setup",
          guide: "进度降级后允许的开篇导读。",
          why_it_matters: "安全的重要性。",
          bridge: "安全承接。",
          next_question: "安全问题？",
          event: {
            slug: "start-event",
            title: "开篇线索",
            summary: "安全摘要。",
            impact: null,
            characters: [],
            sources: [],
          },
          relationships: [],
          historical_contexts: [],
        },
      ],
    };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/story-arcs?progress=unrestricted")) {
        return Promise.resolve(
          envelope({
            progress: "unrestricted",
            arcs: [
              {
                id: "ending-journey",
                slug: "ending-journey",
                title: "终局导读",
                summary: "旧导读。",
                core_question: "旧问题？",
                estimated_minutes: 12,
                beat_count: 1,
              },
            ],
          }),
        );
      }
      if (url.includes("/story-arcs/ending-journey?progress=unrestricted")) {
        return new Promise<Response>((resolve) => {
          resolveOldDetail = resolve;
        });
      }
      if (url.includes("/story-arcs?progress=start")) {
        return Promise.resolve(
          envelope({
            progress: "start",
            arcs: [
              {
                id: "start-journey",
                slug: "start-journey",
                title: "开篇导读",
                summary: "安全导读。",
                core_question: "开篇问题？",
                estimated_minutes: 3,
                beat_count: 1,
              },
            ],
          }),
        );
      }
      if (url.includes("/story-arcs/start-journey?progress=start")) {
        return Promise.resolve(envelope(startDetail));
      }
      throw new Error(`Unexpected request: ${url}`);
    });

    localStorage.setItem("yysls-progress", "unrestricted");
    render(<TimelineExplorer />);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));

    localStorage.setItem("yysls-progress", "start");
    fireEvent(window, new Event("yysls-progress-change"));
    expect(await screen.findByText("进度降级后允许的开篇导读。")).toBeInTheDocument();

    resolveOldDetail?.(envelope(oldDetail));
    await waitFor(() => {
      expect(screen.getByText("进度降级后允许的开篇导读。")).toBeInTheDocument();
      expect(screen.queryByText("延迟抵达的终局受限导读。")).not.toBeInTheDocument();
      expect(screen.queryByText("延迟终局秘密")).not.toBeInTheDocument();
    });
  });

  it("follows the WAI tab keyboard pattern for timeline modes", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      return Promise.resolve(
        envelope(
          url.includes("/timeline?")
            ? { progress: "start", events: [] }
            : { progress: "start", arcs: [] },
        ),
      );
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

  it("switches between story reading and complete events, and navigates beats", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        envelope({
          progress: "start",
          arcs: [
            {
              id: "qinghe-main-journey",
              slug: "qinghe-main-journey",
              title: "清河主线 · 一枚玉佩引出的江湖",
              summary: "从黑衣人袭击开始。",
              core_question: "镇冠珏为何重要？",
              estimated_minutes: 12,
              beat_count: 2,
            },
          ],
        }),
      )
      .mockResolvedValueOnce(
        envelope({
          id: "qinghe-main-journey",
          slug: "qinghe-main-journey",
          title: "清河主线 · 一枚玉佩引出的江湖",
          summary: "从黑衣人袭击开始。",
          core_question: "镇冠珏为何重要？",
          estimated_minutes: 12,
          beats: [
            {
              id: "beat-1",
              sort_order: 1,
              role: "导火索",
              guide: "第一节导读文字。",
              why_it_matters: "第一节的重要性。",
              bridge: "第一节承接。",
              next_question: "第一节的问题？",
              event: {
                slug: "prologue-attack",
                title: "黑衣人袭击",
                summary: "第一节事件摘要。",
                impact: null,
                characters: [{ slug: "hero", name: "主角" }],
                sources: [],
              },
              relationships: [],
              historical_contexts: [],
            },
            {
              id: "beat-2",
              sort_order: 2,
              role: "回望",
              guide: "第二节导读文字。",
              why_it_matters: "第二节的重要性。",
              bridge: "第二节承接。",
              next_question: "第二节的问题？",
              event: {
                slug: "wangqing-battle",
                title: "中渡桥旧战",
                summary: "第二节事件摘要。",
                impact: "第二节影响。",
                characters: [],
                sources: [],
              },
              relationships: [
                {
                  id: "relationship-1",
                  relation_type: "old_acquaintance",
                  label: "旧识",
                  source_slug: "wang-qing",
                  source_name: "王清",
                  target_slug: "du-zhongwei",
                  target_name: "杜重威",
                },
              ],
              historical_contexts: [
                {
                  id: "zhongdu-bridge",
                  slug: "zhongdu-bridge",
                  title: "滹沱河中渡桥：王清与杜重威",
                  period_label: "后晋开运三年（946）",
                  summary: "王清请率两千步卒夺桥开路。",
                  fact_kind: "historical_fact",
                  relation_kind: "fictionalized",
                  boundary_note: "拒援后谋降可证，事前勾结动机不可证；十万与二十万的史料记载存在分歧。",
                  editorial_note: null,
                  references: [
                    {
                      reference_type: "史料",
                      title: "《资治通鉴》卷二百八十五",
                      url: "https://example.com/history",
                      locator: "开运三年十一月至十二月",
                    },
                    {
                      reference_type: "不安全来源",
                      title: "不应成为链接",
                      url: "javascript:alert(1)",
                    },
                  ],
                },
              ],
            },
          ],
        }),
      )
      .mockResolvedValueOnce(
        envelope({
          progress: "start",
          events: [
            {
              id: "event-1",
              slug: "prologue-attack",
              title: "完整事件记录",
              summary: "完整时间线事件。",
              impact: null,
              chapter_slug: "qinghe-1",
              chapter_title: "清河第一章",
              sort_order: 1,
              characters: [],
              sources: [],
            },
          ],
        }),
      );

    render(<TimelineExplorer />);
    expect(await screen.findByText("第一节导读文字。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "← 上一节" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "下一节 →" }));
    expect(await screen.findByText("第二节导读文字。")).toBeInTheDocument();
    expect(screen.getAllByText("历史事实").length).toBeGreaterThan(0);
    expect(screen.getAllByText("虚构改写").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "王清" })).toHaveAttribute(
      "href",
      "/characters/wang-qing",
    );
    fireEvent.click(screen.getByText("滹沱河中渡桥：王清与杜重威"));
    expect(screen.getByText(/拒援后谋降可证/)).toBeInTheDocument();
    expect(screen.getByText(/开运三年十一月至十二月/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "《资治通鉴》卷二百八十五" })).toHaveAttribute(
      "rel",
      "noopener noreferrer",
    );
    expect(screen.queryByRole("link", { name: "不应成为链接" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "完整事件" }));
    expect(await screen.findByText("完整事件记录")).toBeInTheDocument();
    expect(screen.getByLabelText("章节")).toBeInTheDocument();
    expect(screen.queryByText("第二节导读文字。")).not.toBeInTheDocument();
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
