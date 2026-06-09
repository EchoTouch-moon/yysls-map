import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SiteHeader } from "./SiteHeader";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  usePathname: () => "/graph",
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe("SiteHeader", () => {
  it("renders the navigation links", () => {
    render(<SiteHeader />);
    expect(screen.getByRole("link", { name: "关系图谱" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "剧情时间线" })).toBeInTheDocument();
  });

  it("applies active class to the current page link based on pathname", () => {
    render(<SiteHeader />);
    const activeLink = screen.getByRole("link", { name: "关系图谱" });
    const inactiveLink = screen.getByRole("link", { name: "剧情时间线" });

    expect(activeLink).toHaveClass("nav-bookmark-active");
    expect(inactiveLink).not.toHaveClass("nav-bookmark-active");
  });
});
