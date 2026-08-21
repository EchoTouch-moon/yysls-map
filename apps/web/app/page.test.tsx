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
  it("presents the story-first primary action pointing at the guide", () => {
    render(<Home />);
    expect(screen.getByRole("link", { name: /看懂清河故事/ })).toHaveAttribute(
      "href",
      "/timeline",
    );
  });

  it("presents character exploration as the second entry", () => {
    render(<Home />);
    expect(screen.getByRole("link", { name: "了解一个人物" })).toHaveAttribute(
      "href",
      "/characters",
    );
  });

  it("keeps spoiler protection as a demoted optional control", () => {
    render(<Home />);
    fireEvent.click(screen.getByText(/避免看到重大揭示/));
    expect(
      screen.getByText(/涉及后续揭示的内容会整体隐藏/),
    ).toBeInTheDocument();
  });

  it("renders the non-official disclaimer", () => {
    render(<Home />);
    expect(
      screen.getByText(/玩家自发整理的非官方剧情解析项目/),
    ).toBeInTheDocument();
  });

  it("renders feature archive cards with correct links", () => {
    render(<Home />);
    expect(screen.getAllByRole("link", { name: /故事导读/ })[0]).toHaveAttribute(
      "href",
      "/timeline",
    );
    expect(screen.getAllByRole("link", { name: /人物卷宗/ })[0]).toHaveAttribute(
      "href",
      "/characters",
    );
    expect(screen.getAllByRole("link", { name: /历史背景/ })[0]).toHaveAttribute(
      "href",
      "/history",
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

  it("renders only the progress states supported by the current release", () => {
    render(<ProgressSelect variant="compact" />);
    const select = screen.getByRole("combobox");
    expect(select).toBeInTheDocument();
    const options = within(select).getAllByRole("option");
    expect(options).toHaveLength(3);
    expect(options.map((o) => o.textContent)).toEqual([
      "清河篇未通关",
      "清河篇已通关",
      "不防剧透",
    ]);
  });

  it("defaults to 'start' before hydration", () => {
    render(<ProgressSelect variant="compact" />);
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.value).toBe("start");
  });

  it("hydrates from localStorage after mount", async () => {
    localStorage.setItem("yysls-progress", "qinghe");
    render(<ProgressSelect variant="compact" />);
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    await vi.waitFor(() => {
      expect(select.value).toBe("qinghe");
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
    expect(buttons).toHaveLength(3);
    expect(screen.getByText(/进行中的章节请选择上一档/)).toBeInTheDocument();
    expect(buttons[0]).toHaveAttribute("aria-pressed", "true");
    expect(buttons[1]).toHaveAttribute("aria-pressed", "false");
  });

  it("updates selection in card variant on click", () => {
    render(<ProgressSelect variant="card" />);
    const buttons = screen.getAllByRole("button");
    fireEvent.click(buttons[1]);
    expect(buttons[1]).toHaveAttribute("aria-pressed", "true");
    expect(buttons[0]).toHaveAttribute("aria-pressed", "false");
    expect(localStorage.getItem("yysls-progress")).toBe("qinghe");
  });

  it("ignores invalid localStorage values", async () => {
    localStorage.setItem("yysls-progress", "current");
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
