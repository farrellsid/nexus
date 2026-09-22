import { test, expect } from "@playwright/test";

async function openCopper(page: import("@playwright/test").Page) {
  await page.goto("/");
  await page.getByLabel("Industry brief").selectOption("kamoa-to-cables");
  await expect(
    page.getByRole("heading", { name: "From copper to cables." }),
  ).toBeVisible();
}

test("explore a commercial link and inspect its retained evidence", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await openCopper(page);
  const inspector = page.getByRole("complementary", {
    name: "Evidence inspector",
  });
  await expect(inspector.getByText("Source-checked candidate")).toBeVisible();
  await expect(inspector.getByRole("link").first()).toHaveAttribute(
    "href",
    /trafigura.com/,
  );
  await page.getByRole("searchbox").fill("Prysmian");
  await page
    .getByRole("navigation", { name: "Investigation entities" })
    .getByRole("button")
    .click();
  await expect(
    page.getByRole("img", { name: /Relationship overview for Prysmian/ }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Exploration depth" })
    .selectOption("2");
  await expect(page.getByRole("button", { name: /C18/ })).toBeVisible();
  await page.getByRole("button", { name: /C18/ }).click();
  await expect(
    inspector.getByText(
      "Educational relation only; no customer or shipment identity.",
    ),
  ).toBeVisible();
  await page
    .getByRole("navigation", { name: "Investigation entities" })
    .getByRole("button")
    .click();
  await expect(page.getByRole("img")).toBeVisible();
  expect(errors).toEqual([]);
});

test("timeline distinguishes forecast from actual and keeps quarter precision", async ({
  page,
}) => {
  await openCopper(page);
  await page.getByRole("tab", { name: "Timeline" }).click();
  await expect(
    page.getByText("First anode expected in October. Preserve as a forecast."),
  ).toBeVisible();
  await expect(page.getByText("2026-Q1", { exact: true })).toBeVisible();
  await expect(page.getByText("2025-12-29", { exact: true })).toBeVisible();
});

test("curated guide does not invent missing downstream impact", async ({
  page,
}) => {
  await openCopper(page);
  await page.getByRole("tab", { name: "Reading guide" }).click();
  await page.getByLabel("Explore a question").selectOption("Q07");
  await expect(
    page.getByText(
      "Unknown; the corpus lacks dependence shares, inventory, substitutes and attributable production effects.",
    ),
  ).toBeVisible();
  await expect(
    page.getByText("Curated reading guide · no AI generation"),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: /Inspect C/ })).toHaveCount(0);
});

test("narrow viewport remains usable without horizontal overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await openCopper(page);
  await expect(page.getByRole("img")).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.getByRole("tab", { name: "Reading guide" }).click();
  await expect(page.getByLabel("Explore a question")).toBeVisible();
});

test("backend failure is visible instead of showing fabricated fallback data", async ({
  page,
}) => {
  await page.route("**/api/investigation?*", (route) =>
    route.fulfill({ status: 503, body: "Unavailable" }),
  );
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Evidence service unavailable" }),
  ).toBeVisible();
});

test("oil brief opens with sourced metrics and preserves status labels", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Oil under constraint/ }),
  ).toBeVisible();
  await expect(page.getByRole("tab", { name: "Metrics" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(page.getByText("Strait of Hormuz oil flow")).toBeVisible();
  await expect(
    page.getByText("Major maritime oil routes before the disruption window"),
  ).toBeVisible();
  await expect(page.getByText("21.6", { exact: true })).toBeVisible();
  await expect(page.getByText("forecast", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Geography" }).click();
  await expect(
    page.getByRole("img", { name: /Interactive (world globe|Natural Earth world map)/ }),
  ).toBeVisible();
  await expect(page.getByText(/sourced illustrative corridors/).first()).toBeVisible();
  await expect(page.locator(".geo-map-status")).toContainText(
    /Esri satellite globe|OpenStreetMap globe fallback|Natural Earth local map/,
  );
  await page
    .getByLabel("Guided geography stops")
    .getByRole("button", { name: /Strait of Malacca/ })
    .click();
  await expect(page.getByText(/roughly 930-kilometre strait/)).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Suez Canal / SUMED corridor" }),
  ).toBeVisible();
  await expect(
    page.getByText(/does not run straight/),
  ).toBeVisible();
  await page
    .locator(".geo-explanation")
    .getByRole("button", { name: "Explore relationships" })
    .click();
  await expect(
    page.getByRole("img", {
      name: /Relationship overview for Strait of Malacca/,
    }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: /O-C17/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /O-C20/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /O-C21/ })).toBeVisible();
  await page.getByRole("tab", { name: "Reading guide" }).click();
  await page.getByLabel("Explore a question").selectOption("O-Q11");
  await expect(
    page.getByText(/Sunda and Lombok as smaller maritime alternatives/),
  ).toBeVisible();
});
