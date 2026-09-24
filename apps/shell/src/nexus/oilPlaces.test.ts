import assert from 'node:assert/strict';
import test from 'node:test';
import { OIL_OVERVIEW, OIL_PLACE_PRESETS } from './oilPlaces.ts';
import { OIL_GEOGRAPHY } from './oilStops.ts';

const pois = Object.values(OIL_PLACE_PRESETS).flatMap((destination) => destination.pois);

test('every sourced stop is a place the camera can fly to, exactly once', () => {
  assert.deepEqual(
    pois.map((poi) => poi.name).sort(),
    OIL_GEOGRAPHY.stops.map((stop) => stop.label).sort(),
  );
});

test('a place flies to its stop, at the stop\'s own coordinates', () => {
  for (const stop of OIL_GEOGRAPHY.stops) {
    const poi = pois.find((candidate) => candidate.name === stop.label);
    assert.ok(poi, `${stop.label} has no place`);
    assert.equal(poi.lat, stop.latitude);
    assert.equal(poi.lon, stop.longitude);
  }
});

test('a facility is framed closer than a strait, because it is a point and a strait is an area', () => {
  const yanbu = pois.find((poi) => poi.name.includes('Yanbu'));
  const hormuz = pois.find((poi) => poi.name.includes('Hormuz'));
  assert.ok(yanbu && hormuz);
  assert.ok(yanbu.alt < hormuz.alt);
});

test('the opening view is a whole-region height over the Indian Ocean', () => {
  assert.ok(OIL_OVERVIEW.heightM > 5_000_000);
  assert.ok(OIL_OVERVIEW.longitude > 40 && OIL_OVERVIEW.longitude < 115);
});
