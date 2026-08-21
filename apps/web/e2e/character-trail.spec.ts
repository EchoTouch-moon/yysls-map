import { expect, test } from "@playwright/test";

test("character page derives the story trail and gates full analysis", async ({
  page,
}) => {
  await page.addInitScript(() => {
    localStorage.setItem("yysls-progress", "qinghe");
  });

  await page.goto("/characters/protagonist");
  await expect(page.getByRole("heading", { name: "初识" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "剧情足迹" })).toBeVisible();
  await expect(
    page.getByRole("button", { name: /显示该人物的完整解析/ }),
  ).toBeVisible();

  // G4：解析内容在显式触发前不得出现
  await expect(page.getByText(/身世之谜是贯穿全剧的核心悬念/)).toHaveCount(0);

  await page.getByRole("button", { name: /显示该人物的完整解析/ }).click();
  await expect(page.getByText(/身世之谜是贯穿全剧的核心悬念/)).toBeVisible();

  // G5：足迹 → 导读对应幕
  const trailLink = page.getByText(/在导读中阅读这一幕/).first();
  const trailHref = await trailLink.getAttribute("href");
  expect(trailHref).toContain("/timeline?beat=");
});

test("guide beat deep-links into history and back to the story", async ({
  page,
}) => {
  await page.addInitScript(() => {
    localStorage.setItem("yysls-progress", "unrestricted");
  });

  // 人物页历史 chips → /history/[slug]
  await page.goto("/characters/wang-qing");
  const historyChip = page.getByRole("link", { name: /史籍中的中度桥/ }).first();
  if (await historyChip.isVisible()) {
    await historyChip.click();
    await expect(page.getByText(/边界说明/)).toBeVisible();
    // 历史卡 → 回到导读对应幕
    const backLink = page.getByRole("link", { name: /回到导读/ }).first();
    await backLink.click();
    await expect(page).toHaveURL(/\/timeline\?beat=/);
  }

  // ?beat= 深链直接定位幕次
  await page.goto("/timeline?beat=wangqing-battle");
  await expect(
    page.getByRole("heading", { name: "作品中的中渡桥之战" }),
  ).toBeVisible();
});
