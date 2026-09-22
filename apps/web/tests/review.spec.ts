import { randomUUID } from "node:crypto";
import { test, expect } from "@playwright/test";

test.beforeEach(async ({ request }) => {
  const status = await (await request.get("/api/review/status")).json();
  test.skip(!status.enabled, "PostgreSQL is required for review workflows");
});

async function openCopper(page: import("@playwright/test").Page) {
  await page.goto("/");
  await page.getByLabel("Industry brief").selectOption("kamoa-to-cables");
  await expect(
    page.getByRole("heading", { name: "From copper to cables." }),
  ).toBeVisible();
}

test("accept, propose, review and retain both versions across a reload", async ({
  page,
}) => {
  await openCopper(page);
  await page.getByRole("searchbox").fill("dry port");
  await page
    .getByRole("navigation", { name: "Investigation entities" })
    .getByRole("button")
    .click();
  const inspector = page.getByRole("complementary", {
    name: "Evidence inspector",
  });
  const original = await inspector
    .getByRole("heading", { level: 2 })
    .innerText();
  await page.getByRole("button", { name: "Review & history" }).click();
  await page.getByLabel("Reviewer / author").fill("Browser test reviewer");
  await page
    .getByLabel("Reason for this action")
    .fill("Test acceptance of the fixture candidate");
  await page.getByRole("button", { name: "Accept for baseline" }).click();
  await expect(
    inspector.getByText("Accepted in local review", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Propose correction" }).click();
  await page
    .getByRole("textbox", { name: "Proposed statement", exact: true })
    .fill("Synthetic browser correction; not a factual update.");
  await page
    .getByLabel("Reason for this action")
    .fill("Exercise the correction workflow");
  await page
    .getByLabel("Valid from (optional)", { exact: true })
    .fill("2026-02-01");
  await page.getByRole("button", { name: "Save proposal" }).click();
  await expect(page.getByRole("status")).toHaveText(
    "Saved to PostgreSQL. Earlier versions are preserved.",
  );
  await expect(inspector.getByRole("heading", { level: 2 })).toHaveText(
    original,
  );
  await page
    .getByLabel("Reason for this action")
    .fill("Accept the synthetic correction in this disposable database");
  await page.getByRole("button", { name: "Accept for baseline" }).click();
  await expect(inspector.getByRole("heading", { level: 2 })).toHaveText(
    "Synthetic browser correction; not a factual update.",
  );
  await expect(
    page.getByText("Revision 1 · retained", { exact: true }),
  ).toBeVisible();
  await page.getByText("Revision 1 · retained", { exact: true }).click();
  await expect(
    page.locator(".version").filter({ hasText: "Revision 1" }),
  ).toContainText(original);
  await openCopper(page);
  await page.getByRole("searchbox").fill("dry port");
  await page
    .getByRole("navigation", { name: "Investigation entities" })
    .getByRole("button")
    .click();
  await expect(inspector.getByRole("heading", { level: 2 })).toHaveText(
    "Synthetic browser correction; not a factual update.",
  );
});

test("a concurrent review shows a conflict instead of replacing newer state", async ({
  page,
  request,
}) => {
  await openCopper(page);
  await page.getByRole("searchbox").fill("Trafigura Asia");
  await page
    .getByRole("navigation", { name: "Investigation entities" })
    .getByRole("button")
    .click();
  await page.getByRole("button", { name: "Review & history" }).click();
  await page.getByLabel("Reviewer / author").fill("Stale browser reviewer");
  await page
    .getByLabel("Reason for this action")
    .fill("This page was opened before another review");
  const history = await (await request.get("/api/claims/C09/history")).json();
  const response = await request.post(
    `/api/proposals/${history.proposals[0].id}/decision`,
    {
      headers: { "X-Nexus-Review": "1" },
      data: {
        request_id: randomUUID(),
        expected_revision: 0,
        decision: "accept",
        reviewer: "Other test reviewer",
        reason: "Concurrent test review",
      },
    },
  );
  expect(response.status()).toBe(200);
  await page.getByRole("button", { name: "Accept for baseline" }).click();
  await expect(page.getByRole("alert")).toContainText("409");
  await page
    .getByRole("button", { name: "Reload history and baseline" })
    .click();
  await expect(
    page.getByText("Revision 1 · current", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Accept for baseline" }),
  ).toHaveCount(0);
});
