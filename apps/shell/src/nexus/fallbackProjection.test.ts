import assert from 'node:assert/strict';
import test from 'node:test';
import { OIL_GEOGRAPHY } from './oilStops.ts';
import { MAP_HEIGHT, MAP_WIDTH, projectGeography } from './fallbackProjection.ts';

const map = projectGeography();

test('every sourced stop and corridor is on the flat map, in the brief\'s order', () => {
  assert.deepEqual(
    map.stops.map((stop) => stop.id),
    OIL_GEOGRAPHY.stops.map((stop) => stop.id),
  );
  assert.deepEqual(
    map.stops.map((stop) => stop.number),
    OIL_GEOGRAPHY.stops.map((_, index) => index + 1),
  );
  assert.deepEqual(
    map.routes.map((route) => route.id),
    OIL_GEOGRAPHY.routes.map((route) => route.id),
  );
});

test('every marker lies inside the map frame', () => {
  for (const stop of map.stops) {
    assert.ok(stop.x > 0 && stop.x < MAP_WIDTH, `${stop.id} x ${stop.x}`);
    assert.ok(stop.y > 0 && stop.y < MAP_HEIGHT, `${stop.id} y ${stop.y}`);
  }
});

test('the projection puts places where the world is: Hormuz is east of Bab el-Mandeb and north of Lombok', () => {
  const at = (entityId: string) => {
    const stop = OIL_GEOGRAPHY.stops.find((candidate) => candidate.entityId === entityId);
    assert.ok(stop);
    const placed = map.stops.find((candidate) => candidate.id === stop.id);
    assert.ok(placed);
    return placed;
  };
  assert.ok(at('oil-hormuz').x > at('oil-bab').x);
  assert.ok(at('oil-hormuz').y < at('oil-lombok').y, 'screen y grows southward');
  assert.ok(at('oil-malacca').x > at('oil-hormuz').x);
});

test('the land and graticule are drawn', () => {
  assert.ok(map.landPath.length > 1000, 'land path is empty');
  assert.ok(map.graticulePath.length > 100, 'graticule path is empty');
});
