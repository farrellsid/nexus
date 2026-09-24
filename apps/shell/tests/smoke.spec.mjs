// Smoke test for the strip: after every step the shell must render and must not be noisier than
// before. `known-errors.json` lists console errors that are still expected; a step that removes
// their source deletes the entry, and a listed error that no longer appears fails the test so the
// list can only shrink. Set NEXUS_RECORD_BASELINE=1 to record the current errors as the list.
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';

const KNOWN_PATH = new URL('./known-errors.json', import.meta.url);
const known = JSON.parse(readFileSync(KNOWN_PATH, 'utf8')).errors;
const recording = process.env.NEXUS_RECORD_BASELINE === '1';

test('the shell renders and is no noisier than its recorded baseline', async ({ page }) => {
  const errors = [];
  const hosts = new Set();
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text().split('\n')[0].slice(0, 220));
  });
  page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`.slice(0, 220)));
  page.on('request', (request) => hosts.add(new URL(request.url()).host));

  await page.goto('/');
  await page.waitForSelector('canvas', { timeout: 60_000 });
  await page.waitForTimeout(10_000);

  // Imagery arrives over the network, so wait for a rendered frame rather than a fixed delay.
  let screenshot = await page.screenshot();
  for (let attempt = 0; attempt < 12 && screenshot.length <= 60_000; attempt++) {
    await page.waitForTimeout(5_000);
    screenshot = await page.screenshot();
  }
  mkdirSync('test-results', { recursive: true });
  writeFileSync('test-results/smoke.png', screenshot);
  writeFileSync(
    'test-results/smoke-observed.json',
    JSON.stringify({ hosts: [...hosts].sort(), errors: [...new Set(errors)].sort(), screenshotBytes: screenshot.length }, null, 2),
  );

  if (recording) {
    writeFileSync(KNOWN_PATH, JSON.stringify({ errors: [...new Set(errors)].sort() }, null, 2) + '\n');
    return;
  }
  const allowedHosts = new Set(JSON.parse(readFileSync(new URL('./allowed-hosts.json', import.meta.url), 'utf8')).hosts);
  expect([...hosts].filter((host) => !allowedHosts.has(host)), 'hosts the page must not contact').toEqual([]);
  // A blank page compresses to a few KB; a rendered globe with chrome is far larger.
  expect(screenshot.length, 'the page looks blank').toBeGreaterThan(60_000);
  const unexpected = errors.filter((text) => !known.some((entry) => text.includes(entry)));
  expect(unexpected, 'errors that are not in known-errors.json').toEqual([]);
  const stale = known.filter((entry) => !errors.some((text) => text.includes(entry)));
  expect(stale, 'known errors that no longer occur: delete them from known-errors.json').toEqual([]);
});

test('the oil layers draw their sourced records when enabled and remove them when disabled', async ({ page }) => {
  await page.goto('/');
  await page.waitForFunction(() => window.__godsEyeView?.dataManager, null, { timeout: 60_000 });
  const read = () =>
    page.evaluate(() => {
      const { viewer } = window.__godsEyeView;
      return Array.from({ length: viewer.dataSources.length }, (_, index) => {
        const source = viewer.dataSources.get(index);
        return `${source.name}:${source.entities.values.length}`;
      }).sort();
    });
  const setLayers = (enabled) =>
    page.evaluate(async (on) => {
      const { dataManager } = window.__godsEyeView;
      for (const id of ['nexus-oil-stops', 'nexus-oil-corridors'])
        await dataManager.setEnabled(id, on, { origin: 'user' });
    }, enabled);
  expect(await read()).toEqual([]);
  await setLayers(true);
  expect(await read()).toEqual(['nexus-oil-corridors:2', 'nexus-oil-stops:6']);
  await setLayers(false);
  expect(await read()).toEqual([]);
});

test('the corner readouts state the pack, its date and what the map leaves out, and follow the selection', async ({ page }) => {
  await page.goto('/');
  await page.waitForFunction(() => window.__godsEyeView?.viewer, null, { timeout: 60_000 });
  const lines = page.locator('#hud-data-lines');
  await expect(lines).toContainText('AS OF 2026-09-22');
  await expect(lines).toContainText('8 OF 23 ENTITIES ON MAP · 15 NOT ON MAP');
  await expect(page.locator('#hud-selection')).toHaveText('SELECTED: NONE');

  await page.evaluate(async () => {
    const { viewer, dataManager } = window.__godsEyeView;
    await dataManager.setEnabled('nexus-oil-stops', true, { origin: 'user' });
    const source = Array.from({ length: viewer.dataSources.length }, (_, i) => viewer.dataSources.get(i)).find(
      (candidate) => candidate.name === 'nexus-oil-stops',
    );
    viewer.selectedEntity = source.entities.values[0];
  });
  await expect(page.locator('#hud-selection')).toHaveText('SELECTED: Strait of Hormuz · REPRESENTATIVE LABEL POINT');
});

test('the action layer plays the tour, refuses a bad request, and global context puts the view back', async ({ page }) => {
  await page.goto('/');
  await page.waitForFunction(() => window.__godsEyeView?.actions, null, { timeout: 60_000 });
  // Let the opening flight finish, or it would take the camera back from the first request.
  await page.waitForFunction(
    () => Math.abs(window.__godsEyeView.viewer.camera.positionCartographic.height - 12_000_000) < 50_000,
    null,
    { timeout: 30_000 },
  );
  const run = (name, args) => page.evaluate(([n, a]) => window.__godsEyeView.actions.run(n, a), [name, args]);
  const camera = () =>
    page.evaluate(() => {
      const { camera } = window.__godsEyeView.viewer;
      const position = camera.positionCartographic;
      return { lon: (position.longitude * 180) / Math.PI, lat: (position.latitude * 180) / Math.PI, height: position.height };
    });
  const enabledLayers = () =>
    page.evaluate(() =>
      ['nexus-oil-stops', 'nexus-oil-corridors'].filter((id) => window.__godsEyeView.dataManager.isEnabled(id)),
    );

  expect((await run('delete_evidence', {})).ok).toBe(false);
  expect((await run('set_layer', { layer: 'no-such-layer', visible: true })).ok).toBe(false);

  // Global context: pull out with the layers on, then return to exactly where the camera was.
  expect((await run('fly_to_place', { destination: 'gulf-and-red-sea', place: 0 })).ok).toBe(true);
  await page.waitForFunction(() => window.__godsEyeView.viewer.camera.positionCartographic.height < 800_000, null, { timeout: 30_000 });
  const before = await camera();
  expect(await enabledLayers()).toEqual([]);
  expect((await run('global_context', { on: true })).ok).toBe(true);
  await page.waitForFunction(() => window.__godsEyeView.viewer.camera.positionCartographic.height > 15_000_000, null, { timeout: 30_000 });
  expect(await enabledLayers()).toEqual(['nexus-oil-stops', 'nexus-oil-corridors']);
  expect((await run('global_context', { on: false })).ok).toBe(true);
  await page.waitForFunction(() => window.__godsEyeView.viewer.camera.positionCartographic.height < 800_000, null, { timeout: 30_000 });
  const after = await camera();
  expect(Math.abs(after.lon - before.lon)).toBeLessThan(0.5);
  expect(Math.abs(after.lat - before.lat)).toBeLessThan(0.5);
  expect(await enabledLayers()).toEqual([]);

  // The tour flies to the first stop (Hormuz) and turns the oil layers on.
  expect((await run('play_tour', {})).ok).toBe(true);
  await page.waitForFunction(
    () => {
      const position = window.__godsEyeView.viewer.camera.positionCartographic;
      return Math.abs((position.longitude * 180) / Math.PI - 56.5) < 3 && position.height < 3_000_000;
    },
    null,
    { timeout: 45_000 },
  );
  expect(await enabledLayers()).toEqual(['nexus-oil-stops', 'nexus-oil-corridors']);
  expect((await run('stop_tour', {})).ok).toBe(true);
});

test('a hostile share hash is ignored: no errors, and the shell opens on its own view', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/#lat=999&lon=NaN&alt=1e300&style=__proto__&map=%3Cscript%3E&hud=constructor&v=2&l=evil');
  await page.waitForFunction(() => window.__godsEyeView?.viewer, null, { timeout: 60_000 });
  await page.waitForFunction(
    () => Math.abs(window.__godsEyeView.viewer.camera.positionCartographic.height - 12_000_000) < 50_000,
    null,
    { timeout: 30_000 },
  );
  expect(errors).toEqual([]);
});

test('a well-formed share hash restores its view', async ({ page }) => {
  await page.goto('/#v=2&lat=12.5&lon=43.3&alt=600000&heading=0&pitch=-60&roll=0&style=normal&map=esri-imagery');
  await page.waitForFunction(() => window.__godsEyeView?.viewer, null, { timeout: 60_000 });
  await page.waitForFunction(
    () => {
      const position = window.__godsEyeView.viewer.camera.positionCartographic;
      return Math.abs((position.latitude * 180) / Math.PI - 12.5) < 0.5 && Math.abs(position.height - 600_000) < 20_000;
    },
    null,
    { timeout: 30_000 },
  );
});
