import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { OIL_GEOGRAPHY } from './oilStops.ts';

const source = JSON.parse(
  readFileSync(new URL('../../../../investigations/02-oil-system/geography.json', import.meta.url), 'utf8'),
) as {
  title: string;
  framing: string;
  stops: Record<string, unknown>[];
  routes: (Record<string, unknown> & { points: { latitude: number; longitude: number }[] })[];
};

test('the fixture has the six sourced stops and the two sourced corridors', () => {
  assert.equal(OIL_GEOGRAPHY.stops.length, 6);
  assert.equal(OIL_GEOGRAPHY.routes.length, 2);
  assert.deepEqual(
    OIL_GEOGRAPHY.stops.map((stop) => stop.id),
    ['O-G01', 'O-G02', 'O-G03', 'O-G04', 'O-G05', 'O-G06'],
  );
});

test('the generated file carries every value of the evidence-pack source, unchanged', () => {
  assert.equal(OIL_GEOGRAPHY.title, source.title);
  assert.equal(OIL_GEOGRAPHY.framing, source.framing);
  for (const [index, stop] of OIL_GEOGRAPHY.stops.entries()) {
    const from = source.stops[index];
    assert.ok(from);
    assert.equal(stop.entityId, from['entity_id']);
    assert.equal(stop.latitude, from['latitude']);
    assert.equal(stop.longitude, from['longitude']);
    assert.equal(stop.caveat, from['caveat']);
    assert.equal(stop.whyItMatters, from['why_it_matters']);
    assert.equal(stop.sourceUrl, from['source_url']);
    assert.equal(stop.checkedOn, from['checked_on']);
  }
  for (const [index, route] of OIL_GEOGRAPHY.routes.entries()) {
    const from = source.routes[index];
    assert.ok(from);
    assert.deepEqual(route.points, from.points);
    assert.equal(route.caveat, from['caveat']);
  }
});

test('every record states its precision, its caveat and where its coordinates come from', () => {
  for (const record of [...OIL_GEOGRAPHY.stops, ...OIL_GEOGRAPHY.routes]) {
    assert.ok(record.precision.length > 0, `${record.id} has no precision`);
    assert.ok(record.caveat.length > 0, `${record.id} has no caveat`);
    assert.match(record.sourceUrl, /^https:\/\//, `${record.id} has no https source`);
  }
});
