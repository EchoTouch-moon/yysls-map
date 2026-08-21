import { expect, test } from "@playwright/test";

test("mobile navigation exposes the main routes and graph fallback", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("button", { name: "打开导航菜单" }).click();
  const drawer = page.getByRole("dialog", { name: "移动端导航" });
  await expect(drawer).toBeVisible();
  await drawer.getByRole("link", { name: "关系图谱" }).click();
  await expect(
    page.getByText(/完整人物关系卷需在较宽画布展开/),
  ).toBeVisible();

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(overflow).toBe(false);
});
