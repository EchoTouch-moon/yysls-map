import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import Home from "./page";
import { ArchiveCard, ArchiveCardList } from "@/components/ui/ArchiveCard";
import { ProgressSelect } from "@/components/ui/ProgressSelect";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { Drawer } from "@/components/ui/Drawer";

/* ------------------------------------------------------------------ */
/*  Home page                                                          */
/* ------------------------------------------------------------------ */

describe("Home", () => {
  it("presents the primary graph action", () => {
    render(<Home />);
    expect(screen.getByRole("link", { name: "展开关系图" })).toHaveAttribute(
      "href",
      "/graph",
    );
  });

  it("presents the secondary timeline action", () => {
    render(<Home />);
    expect(screen.getByRole("link", { name: "查看时间线" })).toHaveAttribute(
      "href",
      "/timeline",
    );
  });

  it("renders the non-official disclaimer", () => {
    render(<Home />);
    expect(
      screen.getByText(/玩家自发整理的非官方剧情关系图谱项目/),
    ).toBeInTheDocument();
  });

  it("renders feature archive cards with correct links", () => {
    render(<Home />);
    expect(screen.getByRole("link", { name: /关系图谱/ })).toHaveAttribute(
      "href",
      "/graph",
    );
    expect(screen.getByRole("link", { name: /剧情时间线/ })).toHaveAttribute(
      "href",
      "/timeline",
    );
    expect(screen.getByRole("link", { name: /人物卷宗/ })).toHaveAttribute(
      "href",
      "/characters",
    );
  });
});

/* ------------------------------------------------------------------ */
/*  SectionHeading                                                     */
/* ------------------------------------------------------------------ */

describe("SectionHeading", () => {
  it("renders an eyebrow, heading, and description", () => {
    render(
      <SectionHeading eyebrow="Eyebrow" description="Desc text">
        Main title
      </SectionHeading>,
    );
    expect(screen.getByText("Eyebrow")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2, name: "Main title" })).toBeInTheDocument();
    expect(screen.getByText("Desc text")).toBeInTheDocument();
  });

  it("respects the level prop", () => {
    render(<SectionHeading level={1}>H1 heading</SectionHeading>);
    expect(screen.getByRole("heading", { level: 1, name: "H1 heading" })).toBeInTheDocument();
  });

  it("omits eyebrow and description when not provided", () => {
    render(<SectionHeading>Just heading</SectionHeading>);
    expect(screen.getByRole("heading", { name: "Just heading" })).toBeInTheDocument();
    // No extra text nodes beyond the heading
    expect(screen.queryByText("Eyebrow")).not.toBeInTheDocument();
  });
});

/* ------------------------------------------------------------------ */
/*  ArchiveCard / ArchiveCardList                                      */
/* ------------------------------------------------------------------ */

describe("ArchiveCard", () => {
  it("renders a link with title and description", () => {
    render(
      <ArchiveCard index={0} title="关系图谱" description="Desc" href="/graph" />,
    );
    const link = screen.getByRole("link", { name: /关系图谱/ });
    expect(link).toHaveAttribute("href", "/graph");
    expect(screen.getByText("Desc")).toBeInTheDocument();
  });

  it("displays a zero-padded index", () => {
    render(
      <ArchiveCard index={2} title="人物卷宗" description="D" href="/characters" />,
    );
    expect(screen.getByText("03")).toBeInTheDocument();
  });
});

describe("ArchiveCardList", () => {
  it("renders all entries as links", () => {
    const entries = [
      { title: "A", description: "a", href: "/a" },
      { title: "B", description: "b", href: "/b" },
    ];
    render(<ArchiveCardList entries={entries} />);
    expect(screen.getByRole("link", { name: /A/ })).toHaveAttribute("href", "/a");
    expect(screen.getByRole("link", { name: /B/ })).toHaveAttribute("href", "/b");
  });
});

/* ------------------------------------------------------------------ */
/*  ProgressSelect                                                     */
/* ------------------------------------------------------------------ */

describe("ProgressSelect", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders the compact select with all options", () => {
    render(<ProgressSelect variant="compact" />);
    const select = screen.getByRole("combobox");
    expect(select).toBeInTheDocument();
    // All five progress options should be present.
    const options = within(select).getAllByRole("option");
    expect(options).toHaveLength(5);
    expect(options.map((o) => o.textContent)).toEqual([
      "初入江湖",
      "清河篇",
      "开封篇",
      "当前进度",
      "全部可见",
    ]);
  });

  it("defaults to 'start' before hydration", () => {
    render(<ProgressSelect variant="compact" />);
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("start");
  });

  it("hydrates from localStorage after mount", async () => {
    localStorage.setItem("yysls-progress", "kaifeng");
    render(<ProgressSelect variant="compact" />);
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    // After useEffect runs the value should update.
    await vi.waitFor(() => {
      expect(select.value).toBe("kaifeng");
    });
  });

  it("persists selection to localStorage on change", () => {
    render(<ProgressSelect variant="compact" />);
    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "qinghe" } });
    expect(localStorage.getItem("yysls-progress")).toBe("qinghe");
  });

  it("renders the card variant with buttons", () => {
    render(<ProgressSelect variant="card" />);
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(5);
    // First option should be pressed (default).
    expect(buttons[0]).toHaveAttribute("aria-pressed", "true");
    expect(buttons[1]).toHaveAttribute("aria-pressed", "false");
  });

  it("updates selection in card variant on click", () => {
    render(<ProgressSelect variant="card" />);
    const buttons = screen.getAllByRole("button");
    fireEvent.click(buttons[2]); // 开封篇
    expect(buttons[2]).toHaveAttribute("aria-pressed", "true");
    expect(buttons[0]).toHaveAttribute("aria-pressed", "false");
    expect(localStorage.getItem("yysls-progress")).toBe("kaifeng");
  });

  it("ignores invalid localStorage values", async () => {
    localStorage.setItem("yysls-progress", "totally-invalid");
    render(<ProgressSelect variant="compact" />);
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    await vi.waitFor(() => {
      // Should stay on default since the stored value is invalid.
      expect(select.value).toBe("start");
    });
  });
});

/* ------------------------------------------------------------------ */
/*  Drawer                                                             */
/* ------------------------------------------------------------------ */

describe("Drawer", () => {
  it("renders a dialog element with aria-label", () => {
    render(
      <Drawer open={false} onClose={() => {}} aria-label="测试抽屉">
        <p>内容</p>
      </Drawer>,
    );
    // The <dialog> element is present even when closed.
    const dialog = document.querySelector("dialog");
    expect(dialog).toBeInTheDocument();
  });

  it("renders children inside the dialog", () => {
    render(
      <Drawer open={false} onClose={() => {}} aria-label="测试抽屉">
        <p>抽屉内容</p>
      </Drawer>,
    );
    expect(screen.getByText("抽屉内容")).toBeInTheDocument();
  });
});
