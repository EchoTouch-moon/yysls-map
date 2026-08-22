import { expect, test } from "@playwright/test";

test("reads the canonical Qinghe main spine with spoiler-safe overlays", async ({
  page,
}, testInfo) => {
  await page.goto("/timeline");

  await expect(page.getByRole("tab", { name: "跟着故事读" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  // continuous scroll: the full spine is reachable without beat navigation
  await expect(page.getByRole("navigation", { name: "故事幕次导航" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /上一节|下一节/ })).toHaveCount(0);

  await page.evaluate(() => {
    localStorage.setItem("yysls-progress", "unrestricted");
    window.dispatchEvent(new Event("yysls-progress-change"));
  });

  await expect(
    page.getByRole("heading", { name: "第一章·神仙不渡" }),
  ).toBeVisible();
  await expect(page.getByText("又见新来燕", { exact: true })).toBeVisible();
  await expect(page.getByText("为谁归去", { exact: true })).toBeVisible();

  // D-G4: zero-link canonical node renders with an explicit gap placeholder
  await expect(
    page.getByRole("heading", { name: "破庙救红线与广胡子" }),
  ).toBeVisible();
  await expect(
    page.getByText("当前还没有整理这一段的完整剧情解析。"),
  ).toBeVisible();

  // editorial-only event stays off the canonical spine (zero link)
  await expect(
    page.getByRole("heading", { name: "作品中的中渡桥之战" }),
  ).not.toBeVisible();

  // click drills into interpretation instead of advancing the story
  const arenaCard = page.getByRole("article", { name: "剧情节点：将军祠擂台" });
  await arenaCard.scrollIntoViewIfNeeded();
  await arenaCard
    .getByRole("button", { name: "这里为什么重要 →" })
    .click();
  await expect(page.getByText("本节人物")).toBeVisible();
  await expect(
    page.getByRole("link", { name: "方旭" }),
  ).toHaveAttribute("href", "/characters/fang-xu");
  await expect(page.getByText(/自己的名声和关系网/)).toBeVisible();

  await page.screenshot({
    path: testInfo.outputPath("canonical-spine.png"),
    fullPage: true,
  });

  await page.getByRole("tab", { name: "完整事件" }).click();
  await expect(page.getByLabel("章节")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "作品中的中渡桥之战" }),
  ).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("canonical-full-events.png"),
    fullPage: true,
  });
});
