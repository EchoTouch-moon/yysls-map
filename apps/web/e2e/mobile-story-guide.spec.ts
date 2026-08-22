import { expect, test } from "@playwright/test";

test.use({ viewport: { width: 393, height: 852 } });

test("mobile canonical guide reads as a continuous vertical scroll", async ({
  page,
}, testInfo) => {
  await page.goto("/timeline");

  await page.evaluate(() => {
    localStorage.setItem("yysls-progress", "unrestricted");
    window.dispatchEvent(new Event("yysls-progress-change"));
  });
  await expect(
    page.getByRole("heading", { name: "第一章·神仙不渡" }),
  ).toBeVisible();
  await expect(page.getByText("又见新来燕", { exact: true })).toBeVisible();
  await expect(page.getByText("为谁归去", { exact: true })).toBeVisible();

  // continuous vertical reading: no horizontal overflow anywhere
  await expect.poll(() => page.evaluate(
    () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
  )).toBe(true);
  await page.screenshot({
    path: testInfo.outputPath("canonical-393px.png"),
    fullPage: true,
  });
});
