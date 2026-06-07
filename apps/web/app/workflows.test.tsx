import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AdminConsole } from "@/components/admin/AdminConsole";
import { AIDraftWorkbench } from "@/components/admin/AIDraftWorkbench";
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

  it("removes old timeline data immediately when progress is lowered", async () => {
    let resolveStart: ((response: Response) => void) | undefined;
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        envelope({
          progress: "unrestricted",
          events: [
            {
              id: "future-event",
              slug: "future-event",
              title: "终局秘密",
              summary: "只应在全部可见时出现。",
              impact: null,
              chapter_slug: "ending",
              chapter_title: "终局",
              sort_order: 1,
              characters: [],
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
    expect(await screen.findByText("终局秘密")).toBeInTheDocument();

    localStorage.setItem("yysls-progress", "start");
    fireEvent(window, new Event("yysls-progress-change"));
    expect(screen.queryByText("终局秘密")).not.toBeInTheDocument();
    expect(screen.getByText("正在整理事件次序…")).toBeInTheDocument();

    resolveStart?.(envelope({ progress: "start", events: [] }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
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
