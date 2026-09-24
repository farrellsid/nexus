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
  const first = createApplicationCatalog({ signal: a.signal });
  const second = createApplicationCatalog({ signal: b.signal });
  assert.deepEqual(
    first.layers.map(({ id }) => id),
    ['nexus-oil-stops', 'nexus-oil-corridors'],
  );
  assert.deepEqual(
    first.layers.map(({ id }) => id),
    second.layers.map(({ id }) => id),
  );
  for (const layer of first.layers)
    assert.notEqual(layer, second.get(layer.id));
  const lifecycle = new LayerLifecycle({});
  for (const layer of first.layers) lifecycle.register(layer);
  for (const row of lifecycle.getAll())
    assert.equal(
      row.showInTogglePanel,
      true,
      `${row.id} appears in the Data Layers panel`,
    );
});

test('an already cancelled construction fails before any layer is built', () => {
  const lifetime = new AbortController();
  lifetime.abort();
  assert.throws(() => createApplicationCatalog({ signal: lifetime.signal }), {
    name: 'AbortError',
  });
});
