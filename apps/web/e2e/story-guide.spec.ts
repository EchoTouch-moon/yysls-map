import { expect, test } from "@playwright/test";

test("reads the spoiler-aware Qinghe guide, history context, and full event record", async ({
  page,
}, testInfo) => {
  await page.goto("/timeline");

  await expect(page.getByRole("tab", { name: "跟着故事读" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(
    page.getByRole("heading", { name: "清河主线：从失玉到离乡" }),
  ).toBeVisible();
  await expect(page.getByText("已解锁", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: /第 06 幕/ }),
  ).not.toBeVisible();
  await expect(
    page.getByRole("heading", { name: "作品中的中渡桥之战" }),
  ).not.toBeVisible();

  await page.evaluate(() => {
    localStorage.setItem("yysls-progress", "unrestricted");
    window.dispatchEvent(new Event("yysls-progress-change"));
  });

  await expect(page.getByText("10 节")).toBeVisible();
  await page.getByRole("button", { name: /第 08 幕.*作品中的中渡桥之战/ }).click();
  await expect(
    page.getByRole("heading", { name: "作品中的中渡桥之战" }),
  ).toBeVisible();
  await expect(page.getByText("相关历史背景")).toBeVisible();

  await page.getByText("史籍中的中度桥、王清与杜威").click();
  await expect(page.getByText("后晋开运三年（946）").first()).toBeVisible();
  await expect(
    page.getByText(/不能证明杜重威事先勾结并蓄意害死王清/),
  ).toBeVisible();
  const primarySource = page.getByRole("link", { name: "《资治通鉴》卷二百八十五" });
  await expect(primarySource).toHaveAttribute("target", "_blank");
  await expect(primarySource).toHaveAttribute("rel", "noopener noreferrer");
  await expect(primarySource).toHaveAttribute("href", /^https:\/\//);
  await page.screenshot({
    path: testInfo.outputPath("story-guide-history.png"),
    fullPage: true,
  });

  await page.getByRole("button", { name: /第 10 幕.*酒香塔击败千夜/ }).click();
  await expect(
    page.getByRole("heading", { name: "酒香塔击败千夜" }),
  ).toBeVisible();

  await page.getByRole("tab", { name: "完整事件" }).click();
  await expect(page.getByLabel("章节")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "作品中的中渡桥之战" }),
  ).toBeVisible();
  await expect(page.getByText("相关历史背景")).not.toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("story-guide-full-events.png"),
    fullPage: true,
  });
});
