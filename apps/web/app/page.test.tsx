import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Home", () => {
  it("presents the primary graph action", () => {
    render(<Home />);
    expect(screen.getByRole("link", { name: "展开关系图" })).toHaveAttribute(
      "href",
      "/graph",
    );
  });
});

