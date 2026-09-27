import { expect, test, type Page } from "@playwright/test";
import type {
  ChartEntry,
  Envelope,
  PlayerView,
  SearchItem,
} from "@nidana/contracts/api";
import { signIn } from "./session";

/**
 * N1.5 acceptance: the pilot's benchmark path (case-library/cases/PMC12949993/ANALYSIS.md §10)
 * played through the web build, from the case list to the debrief.
 */

const API = "http://localhost:3199";
const SHOTS = "test-results/screenshots";

async function apiGet<T>(token: string, path: string): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    headers: { authorization: `Bearer ${token}` },
  });
  const body = (await response.json()) as Envelope<T>;
  if (!body.success || body.data === null)
    throw new Error(`${path}: ${body.error?.message}`);
  return body.data;
}

async function mode(page: Page, name: string) {
  await page.getByTestId(`mode-${name}`).click();
}

async function pick(page: Page, names: Map<string, string>, id: string) {
  const search = page.getByTestId("search");
  await search.fill(names.get(id) ?? id);
  await page.getByTestId(`pick-${id}`).click();
}

async function waitForAll(page: Page) {
  await mode(page, "wait");
  for (
    let i = 0;
    i < 10 && (await page.getByTestId("wait-next").isEnabled());
    i += 1
  ) {
    await page.getByTestId("wait-next").click();
    await expect(page.getByTestId("actions")).not.toHaveClass(/opacity-60/);
  }
}

test("the benchmark path, from the case list to the debrief", async ({
  page,
}) => {
  const token = await signIn(page);
  const catalogue = await apiGet<SearchItem[]>(token, "/api/catalogue");
  const names = new Map(catalogue.map((i) => [i.id, i.name]));
  const cases = await apiGet<{ slug: string; title: string }[]>(
    token,
    "/api/cases",
  );
  // The pilot's opaque slug (PMC12949993); it is fixed for the case across revisions.
  const pilot = cases.find((c) => c.slug === "c-6gizm");
  expect(pilot).toBeDefined();

  // First visit: the consent screen, then the profile (N1.6).
  await page.goto("/");
  await expect(page.getByTestId("consent-terms")).toBeVisible();
  await expect(page.getByTestId("disclaimer")).toBeVisible();
  await expect(page.getByTestId("join")).toBeDisabled();
  await page.getByTestId("nickname").fill("Benchmark tester");
  await page.getByTestId("level-resident").click();
  await page.getByTestId("agree").click();
  await page.getByTestId("join").click();
  await expect(page.getByTestId("error")).toHaveCount(0, { timeout: 15_000 });
  await page.getByTestId(`case-${pilot?.slug}`).click();
  await expect(page.getByTestId("case-card")).toBeVisible();
  await page.getByTestId("difficulty-standard").click();
  await page.getByTestId("start").click();
  await expect(page.getByTestId("case-intro")).toBeVisible();
  const encounterId = page.url().split("/play/")[1]?.split(/[/?#]/)[0] ?? "";

  // History and examination.
  await mode(page, "ask");
  for (const id of ["HX.PC.PAIN_DETAILS", "HX.MEDS.CURRENT", "HX.GI.BLEEDING"])
    await pick(page, names, id);
  await mode(page, "examine");
  for (const id of ["EX.GEN.VITALS", "EX.GEN.PALLOR", "EX.ABD.PALPATION"])
    await pick(page, names, id);
  await expect(page.getByTestId("clock")).toHaveText("Day 0, 00:45");

  // First bloods, with price and turnaround confirmed before each order.
  await mode(page, "order");
  for (const id of [
    "LAB.HAEM.CBC",
    "LAB.HAEM.RETIC",
    "LAB.CHEM.LFT",
    "LAB.CHEM.LDH",
    "LAB.CHEM.HAPTOGLOBIN",
    "LAB.TBS.DAT",
    "LAB.HAEM.FILM",
    "LAB.CHEM.RENAL",
  ]) {
    await pick(page, names, id);
    await expect(page.getByTestId("confirm-card")).toContainText(
      "result arrives in",
    );
    await page.getByTestId("confirm").click();
  }
  // A search with no match (N1.7): the no-match message, a report with the query only, no cost.
  await expect(page.getByTestId("pending").getByText(/ due /)).toHaveCount(8);
  const spend = await page.getByTestId("spend").textContent();
  const reported = page.waitForRequest(
    (r) => r.url().endsWith("/api/missing") && r.method() === "POST",
  );
  await page.getByTestId("search").fill("unicorn serum assay");
  await expect(page.getByTestId("no-match")).toBeVisible();
  expect((await reported).postDataJSON()).toEqual({
    encounterId,
    kind: "test",
    query: "unicorn serum assay",
  });
  await expect(page.getByTestId("spend")).toHaveText(spend ?? "");
  await expect(page.getByTestId("clock")).toHaveText("Day 0, 00:45");
  await page.getByTestId("search").fill("");

  await mode(page, "wait");
  await page.getByTestId("wait-next").click();
  await expect(page.getByTestId("clock")).toHaveText("Day 0, 04:45");

  // The screening film is provisional, with its status line (N-014).
  await page.setViewportSize({ width: 1440, height: 900 });
  await expect(page.getByTestId("badge-provisional")).toBeVisible();
  await expect(page.getByTestId("status-line")).toContainText(
    "Provisional report",
  );
  await expect(page.locator("body")).not.toContainText(/lead poisoning/i);

  // The targeted remedy question, the film review, the blood lead and toxicology.
  await mode(page, "ask");
  for (const id of ["HX.MEDS.SUPPLEMENTS", "HX.EXPOSURE.OTHERS_EXPOSED"])
    await pick(page, names, id);
  await mode(page, "order");
  for (const id of ["LAB.HAEM.FILM_REVIEW", "LAB.TOX.BLOOD_LEAD"]) {
    await pick(page, names, id);
    await page.getByTestId("confirm").click();
  }
  await mode(page, "refer");
  await pick(page, names, "REF.TOXICOLOGY");
  await page.getByTestId("confirm").click();
  await waitForAll(page);
  await expect(page.getByTestId("badge-final")).toBeVisible();
  await expect(page.getByTestId("value-CMP.PB_BLOOD")).toContainText("77.8");
  await expect(page.locator("body")).not.toContainText(/lead poisoning/i);

  await page.screenshot({
    path: `${SHOTS}/desktop-workspace.png`,
    fullPage: true,
  });
  for (const [name, size] of [
    ["phone", { width: 390, height: 844 }],
    ["tablet", { width: 820, height: 1180 }],
  ] as const) {
    await page.setViewportSize(size);
    await page
      .getByTestId("view-chart")
      .click()
      .catch(() => undefined);
    await page.screenshot({
      path: `${SHOTS}/${name}-workspace.png`,
      fullPage: true,
    });
    await page
      .getByTestId("view-actions")
      .click()
      .catch(() => undefined);
  }
  await page.setViewportSize({ width: 1440, height: 900 });

  // Commit: lead poisoning, citing the supplement and the blood lead, with the plan in order.
  const view = await apiGet<PlayerView>(
    token,
    `/api/encounters/${encounterId}/view`,
  );
  const refOf = (match: (e: ChartEntry) => boolean) =>
    view.chart.find(match)?.ref ?? "";
  const supplement = refOf((e) => e.item === "HX.MEDS.SUPPLEMENTS");
  const lead = refOf((e) => e.component?.id === "CMP.PB_BLOOD");
  await mode(page, "commit");
  await page.getByTestId("go-commit").click();
  await page.getByTestId("dx-search").fill("lead poisoning");
  await page.getByTestId("pick-DX.LEAD_POISONING").click();
  for (const id of [
    "ACT.STOP_SUSPECTED_SOURCE",
    "RX.CHELATION.SUCCIMER_ORAL",
    "ACT.NOTIFY_PUBLIC_HEALTH",
    "ACT.REPEAT_BLOOD_LEAD",
  ]) {
    await page.getByTestId("plan-search").fill(names.get(id) ?? id);
    await page.getByTestId(`pick-${id}`).click();
  }
  await page.getByTestId(`cite-${supplement}`).click();
  await page.getByTestId(`cite-${lead}`).click();
  await page.screenshot({
    path: `${SHOTS}/desktop-commit.png`,
    fullPage: true,
  });
  await page.getByTestId("submit-commit").click();

  // The debrief: anchor 5, every must-do met, origins revealed, both film reports.
  await expect(page.getByTestId("score")).toContainText("anchor 5 of 5");
  await expect(page.getByTestId("must-do")).not.toContainText("✗");
  await expect(page.getByTestId("synthetic")).toContainText("were generated");
  await expect(page.getByTestId("report-pair")).toContainText(
    "After expert review",
  );
  await expect(page.getByTestId("source")).toContainText("CC BY 4.0");
  await page.screenshot({
    path: `${SHOTS}/desktop-debrief.png`,
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: `${SHOTS}/phone-debrief.png`, fullPage: true });

  // The finished encounter is listed for this player, with its score (N1.6).
  await page.goto("/");
  await expect(page.getByTestId("my-encounters")).toContainText("Score 95");
  await page.getByTestId("nav-credits").click();
  await expect(page.getByTestId("credits-statement")).toBeVisible();
  await expect(page.getByTestId("sources")).toHaveCount(0);
  await page.getByTestId("show-sources").click();
  await expect(page.getByTestId("sources")).toContainText("CC BY 4.0");
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.screenshot({
    path: `${SHOTS}/desktop-credits.png`,
    fullPage: true,
  });
});

test("a first visit shows the consent screen and sends nothing before the player agrees", async ({
  page,
}) => {
  const requests: string[] = [];
  page.on("request", (r) => {
    const url = r.url();
    if (!url.startsWith("http://localhost:8199")) requests.push(url);
  });
  await page.goto("/");
  await expect(page.getByTestId("consent-terms")).toBeVisible();
  await expect(
    page.getByRole("checkbox", { name: /research/ }),
  ).not.toBeChecked();
  await page.screenshot({ path: `${SHOTS}/phone-welcome.png`, fullPage: true });
  expect(requests).toEqual([]);
});
