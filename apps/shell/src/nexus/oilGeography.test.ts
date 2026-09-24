import assert from 'node:assert/strict';
import test from 'node:test';
import type * as Cesium from 'cesium';
import {
  createOilCorridorsLayer,
  createOilStopsLayer,
  describeRecord,
  OIL_CORRIDORS_LAYER_ID,
  OIL_STOPS_LAYER_ID,
} from './oilGeographyLayer.ts';
import { lookAheadDegrees, oilTourRecipe } from './oilTour.ts';
import { OIL_GEOGRAPHY } from './oilStops.ts';

interface FakeSource {
  entities: { values: unknown[]; add(entity: unknown): void };
}

/** The slice of a viewer the layer touches, recording what it does to it. */
function fakeViewer() {
  const sources: FakeSource[] = [];
  const removed: FakeSource[] = [];
  let renders = 0;
  const viewer = {
    isDestroyed: () => false,
    scene: { requestRender: () => void (renders += 1) },
    dataSources: {
      async add(source: FakeSource) {
        sources.push(source);
      },
      remove(source: FakeSource) {
        removed.push(source);
        return true;
      },
    },
  };
  return { viewer: viewer as unknown as Cesium.Viewer, sources, removed, renders: () => renders };
}

test('enabling draws every stop once, and disabling removes them', async () => {
  const layer = createOilStopsLayer();
  const { viewer, sources, removed } = fakeViewer();
  assert.equal(layer.getStats().count, 0, 'nothing is drawn before enable');
  assert.equal(await layer.enable(viewer), true);
  assert.equal(await layer.enable(viewer), true, 'a second enable does not draw twice');
  assert.equal(sources.length, 1);
  assert.equal(sources[0]?.entities.values.length, OIL_GEOGRAPHY.stops.length);
  assert.equal(layer.getStats().count, 6);
  await layer.disable(viewer);
  assert.equal(removed.length, 1);
  assert.equal(layer.getStats().count, 0);
});

test('the corridors layer draws the two sourced lines and nothing else', async () => {
  const layer = createOilCorridorsLayer();
  const { viewer, sources } = fakeViewer();
  await layer.enable(viewer);
  assert.equal(sources[0]?.entities.values.length, OIL_GEOGRAPHY.routes.length);
  assert.equal(layer.getStats().count, 2);
});

test('a record card carries its caveat and its source, so a point is never read as more than it is', () => {
  const hormuz = OIL_GEOGRAPHY.stops[0];
  assert.ok(hormuz);
  const text = describeRecord(hormuz);
  assert.match(text, /must not be read as a route or vessel position/);
  assert.match(text, /wikidata\.org\/wiki\/Q79883/);
  assert.match(text, /checked 2026-09-22/);
});

test('the layers use the ids the layer-state registry knows', () => {
  assert.equal(createOilStopsLayer().id, 'nexus-oil-stops');
  assert.equal(createOilCorridorsLayer().id, 'nexus-oil-corridors');
  assert.equal(OIL_STOPS_LAYER_ID, 'nexus-oil-stops');
  assert.equal(OIL_CORRIDORS_LAYER_ID, 'nexus-oil-corridors');
});

test('the tour has one shot per stop, in order, and asks only for the two oil layers', () => {
  const recipe = oilTourRecipe();
  assert.deepEqual(
    recipe.cameraPath.map((shot) => shot.title),
    OIL_GEOGRAPHY.stops.map((stop) => stop.label),
  );
  assert.deepEqual(recipe.layers, { [OIL_STOPS_LAYER_ID]: true, [OIL_CORRIDORS_LAYER_ID]: true });
  assert.equal(
    recipe.durationSec,
    recipe.cameraPath.reduce((total, shot) => total + shot.duration + shot.hold, 0),
  );
});

test('each shot looks north at its stop from the same distance', () => {
  const recipe = oilTourRecipe();
  const offset = lookAheadDegrees(1_500_000, -50);
  assert.ok(offset > 10 && offset < 12, `look-ahead ${offset}° is not the expected ~11°`);
  for (const [index, shot] of recipe.cameraPath.entries()) {
    const stop = OIL_GEOGRAPHY.stops[index];
    assert.ok(stop);
    assert.equal(shot.lon, stop.longitude);
    assert.ok(Math.abs(stop.latitude - shot.lat - offset) < 1e-9);
    assert.equal(shot.heading, 0);
  }
});
