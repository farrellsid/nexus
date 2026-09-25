import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

import {
  sceneLayerPlan,
} from './scenePolicy.js';
import { SCENE_RECIPES } from './recipes.js';
import { LAYER_STATE_REGISTRY } from '../data/layerState.js';


/** The layer registry as main.js builds it (src/main.js dataManager.register calls). */
const REGISTERED = new Set([
  'bhote-koshi-2026', 'bhote-koshi-locator',
  'directions', 'flights', 'military', 'satellites', 'rocket-launches',
  'ais-live-vessels', 'military-installations',
  'military-awareness', 'nexus-oil-corridors', 'nexus-oil-stops',
  'local-firms', 'test-layer',
]);

test('a shot only reconciles the layers it declares', () => {
  const plan = sceneLayerPlan({ flights: { enabled: true } }, REGISTERED);
  assert.deepEqual(plan, [{ id: 'flights', enabled: true, params: undefined }]);
});

test('undeclared layers are never torn down by a four-layer recipe', () => {
  // Regression: the reconcile used to walk the live registry and force every
  // absent layer off, so a recipe authored against four layers destroyed the
  // twelve added since — with no restore pass to put them back.
  const plan = sceneLayerPlan(
    { flights: { enabled: true }, satellites: { enabled: false } },
    REGISTERED,
  );
  const touched = plan.map((entry) => entry.id);
  assert.deepEqual(touched, ['flights', 'satellites']);
  for (const untouched of ['directions', 'military', 'nexus-oil-stops', 'nexus-oil-corridors', 'local-firms']) {
    assert.ok(!touched.includes(untouched), `${untouched} must be left alone`);
  }
});

test('an explicit false in a recipe still disables that layer', () => {
  const plan = sceneLayerPlan(
    { earthquakes: { enabled: true }, flights: { enabled: false }, 'test-layer': { enabled: false } },
    REGISTERED,
  );
  assert.deepEqual(
    plan.filter((entry) => !entry.enabled).map((entry) => entry.id),
    ['flights', 'test-layer'],
  );
});

test('an operator-captured shot declaring every layer still reconciles in full', () => {
  // captureShot() snapshots the whole registry, so full reconcile is preserved.
  const captured = Object.fromEntries(
    [...REGISTERED].map((id) => [id, { enabled: id === 'nexus-oil-stops' }]),
  );
  const plan = sceneLayerPlan(captured, REGISTERED);
  assert.equal(plan.length, REGISTERED.size);
  assert.deepEqual(plan.filter((entry) => entry.enabled).map((entry) => entry.id), ['nexus-oil-stops']);
});

test('layers no longer registered are skipped, not pushed at the data manager', () => {
  const plan = sceneLayerPlan(
    { flights: { enabled: true }, 'retired-layer': { enabled: true } },
    REGISTERED,
  );
  assert.deepEqual(plan.map((entry) => entry.id), ['flights']);
});

test('per-layer params ride along only when the shot carries them', () => {
  const plan = sceneLayerPlan(
    { satellites: { enabled: true, params: { catalog: 'dense' } }, flights: { enabled: true } },
    REGISTERED,
  );
  assert.deepEqual(plan[0], { id: 'satellites', enabled: true, params: { catalog: 'dense' } });
  assert.equal(plan[1].params, undefined);
});

test('missing or malformed target maps produce an empty plan', () => {
  assert.deepEqual(sceneLayerPlan(undefined, REGISTERED), []);
  assert.deepEqual(sceneLayerPlan({}, REGISTERED), []);
  assert.deepEqual(sceneLayerPlan({ flights: null }, REGISTERED), [
    { id: 'flights', enabled: false, params: undefined },
  ]);
});

test('every shipped recipe declares only registered layer ids', () => {
  for (const recipe of SCENE_RECIPES) {
    for (const layerId of Object.keys(recipe.layers || {})) {
      assert.ok(REGISTERED.has(layerId), `${recipe.id} declares unknown layer ${layerId}`);
    }
  }
});

test('shipped recipes touch only their declared layers', () => {
  for (const recipe of SCENE_RECIPES) {
    const declared = Object.entries(recipe.layers || {})
      .map(([id, enabled]) => [id, { enabled }]);
    const plan = sceneLayerPlan(Object.fromEntries(declared), REGISTERED);
    assert.equal(plan.length, Object.keys(recipe.layers || {}).length, recipe.id);
    assert.ok(plan.length <= 8, `${recipe.id} should not reach beyond its declared layers`);
  }
});
