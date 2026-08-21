import { expect, test } from "@playwright/test";

test.use({ viewport: { width: 393, height: 852 } });

test("mobile story guide contains page overflow while its beat ribbon scrolls", async ({
  page,
}, testInfo) => {
  await page.goto("/timeline");
  await expect(
    page.getByRole("heading", { name: "清河主线：从失玉到离乡" }),
  ).toBeVisible();

  await page.evaluate(() => {
    localStorage.setItem("yysls-progress", "unrestricted");
    window.dispatchEvent(new Event("yysls-progress-change"));
  });
  await expect(page.getByText("10 节")).toBeVisible();

  const ribbon = page.getByRole("navigation", { name: "故事幕次导航" }).locator("ol");
  await expect.poll(() => ribbon.evaluate((element) => element.scrollWidth > element.clientWidth)).toBe(true);
  await ribbon.evaluate((element) => {
    element.scrollLeft = element.scrollWidth;
  });
  await expect.poll(() => ribbon.evaluate((element) => element.scrollLeft > 0)).toBe(true);

  await page.getByRole("button", { name: /第 10 幕.*酒香塔击败千夜/ }).click();
  await expect(
    page.getByRole("heading", { name: "酒香塔击败千夜" }),
  ).toBeVisible();
  await expect.poll(() => page.evaluate(
    () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
  )).toBe(true);
  await page.screenshot({
    path: testInfo.outputPath("story-guide-393px.png"),
    fullPage: true,
  });
});
