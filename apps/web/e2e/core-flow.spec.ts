import { expect, test } from "@playwright/test";

test("explores visible content, submits a clue, and moderates it", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /看不懂燕云剧情/ }),
  ).toBeVisible();

  await page.getByRole("link", { name: "展开关系图" }).click();
  await expect(page.getByRole("heading", { name: "角色关系图谱" })).toBeVisible();
  await expect(page.getByLabel("角色关系图谱")).toBeVisible();

  await page.goto("/timeline");
  await expect(page.getByText(/演示卷一：雾渡事件1/)).toBeVisible();
  await expect(page.getByText(/演示卷五：终局事件1/)).not.toBeVisible();

  await page.goto("/submit");
  await page.getByLabel("线索标题").fill("E2E 审核线索");
  await page.getByLabel("起点角色 slug").fill("demo-character-01-01");
  await page.getByLabel("终点角色 slug").fill("demo-character-01-02");
  await page.getByLabel("内容摘要").fill("这是一段用于端到端审核流程的原创关系摘要。");
  await page
    .getByLabel("来源与判断依据")
    .fill("依据演示事件中的共同出场与对话线索进行判断。");
  await page.getByRole("button", { name: "提交人工审核" }).click();
  await expect(page.getByText(/投稿已进入人工审核/)).toBeVisible();

  await page.goto("/admin");
  await page.getByLabel("管理员账号").fill("admin");
  await page.getByLabel("密码").fill("ci-admin-password");
  await page.getByRole("button", { name: "进入审核台" }).click();
  await expect(page.getByRole("heading", { name: "E2E 审核线索" })).toBeVisible();
  await page.getByPlaceholder("填写审核说明（至少 2 个字）").fill("端到端验证后拒绝");
  await page.getByRole("button", { name: "拒绝" }).click();
  await expect(page.getByText("投稿已拒绝。")).toBeVisible();
});
