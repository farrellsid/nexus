import { createSurfaceServices } from './surfaceServices.js';
import test from 'node:test';
import assert from 'node:assert/strict';
import { createApplicationCatalog } from './constructCatalog.js';
import { LayerLifecycle } from '../data/lifecycle.js';

test('catalogs construct distinct layer instances', (t) => {
  const a = new AbortController();
  const b = new AbortController();
  t.after(() => {
    a.abort();
    b.abort();
  });
  const first = createApplicationCatalog({
    signal: a.signal,
    surface: fixtureSurface(a.signal),
  });
  const second = createApplicationCatalog({
    signal: b.signal,
    surface: fixtureSurface(b.signal),
  });
  assert.equal(first.layers.length, 5);
  assert.ok(first.get('bhote-koshi-2026'));
  assert.ok(first.get('bhote-koshi-locator'));
  const lifecycle = registerAll(first.layers);
  const rows = lifecycle.getAll();
  for (const id of ['bhote-koshi-2026', 'bhote-koshi-locator']) {
    assert.equal(
      rows.find((row) => row.id === id)?.showInTogglePanel,
      false,
      `${id} remains registered for Scenes but is absent from Data Layers`,
    );
    assert.equal(typeof first.get(id).enable, 'function');
    assert.equal(typeof first.get(id).setParams, 'function');
  }
  assert.equal(
    rows.find((row) => row.id === 'directions')?.showInTogglePanel,
    true,
    'ordinary data layer entries remain visible',
  );
  assert.deepEqual(
    first.layers.map(({ id }) => id),
    second.layers.map(({ id }) => id),
  );
  for (const layer of first.layers)
    assert.notEqual(layer, second.get(layer.id));
});

test('an already cancelled construction fails before any layer is built', () => {
  const lifetime = new AbortController();
  lifetime.abort();
  assert.throws(
    () =>
      createApplicationCatalog({
        signal: lifetime.signal,
        surface: fixtureSurface(lifetime.signal),
      }),
    { name: 'AbortError' },
  );
});

function registerAll(layers) {
  const lifecycle = new LayerLifecycle({});
  for (const layer of layers) lifecycle.register(layer);
  return lifecycle;
}

function fixtureSurface(signal) {
  return createSurfaceServices({
    terrainSource: { getHeights: async () => [] },
    signal,
    eventTarget: null,
  });
}
