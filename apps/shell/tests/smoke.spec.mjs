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
