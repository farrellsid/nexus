import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { discoverUnitTestFiles } from '../scripts/run-unit-tests.mjs';

test('the runner discovers every test file under src in stable order', () => {
  const files = discoverUnitTestFiles();
  assert.ok(files.includes('src/unitTestRunner.test.mjs'));
  assert.ok(files.includes('src/nexus/oilStops.test.ts'), 'TypeScript tests are discovered too');
  assert.deepEqual(files, [...files].sort());
  assert.ok(files.every((file) => file.startsWith('src/') && /\.test\.(mjs|ts)$/.test(file)));
});

test('npm test invokes the runner', () => {
  const pkg = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
  assert.equal(pkg.scripts.test, 'node scripts/run-unit-tests.mjs');
});
