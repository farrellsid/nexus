import assert from 'node:assert/strict';
import test from 'node:test';
import { OIL_GEOGRAPHY, OIL_PACK } from './oilStops.ts';
import { packReadoutLines, selectionReadout } from './readouts.ts';

test('the pack readout gives the as-of date, the pack, and how many entities are not on the map', () => {
  const [asOf, pack, coverage] = packReadoutLines();
  assert.equal(asOf, `AS OF ${OIL_PACK.checkedOn}`);
  assert.match(pack ?? '', new RegExp(`PACK ${OIL_PACK.caseId}`));
  assert.match(pack ?? '', new RegExp(`SCHEMA ${OIL_PACK.schemaVersion.split('-')[0]}`));
  assert.match(coverage ?? '', /^\d+ OF \d+ ENTITIES ON MAP · \d+ NOT ON MAP$/);
});

test('the not-on-map count is the pack entities that no stop or corridor anchors', () => {
  const anchored = new Set([...OIL_GEOGRAPHY.stops, ...OIL_GEOGRAPHY.routes].map((record) => record.entityId));
  const onMap = OIL_PACK.entities.filter((entity) => anchored.has(entity.id)).length;
  const notOnMap = OIL_PACK.entities.length - onMap;
  assert.ok(notOnMap > 0, 'the pack has entities that the fixture does not place');
  assert.equal(
    packReadoutLines()[2],
    `${onMap} OF ${OIL_PACK.entities.length} ENTITIES ON MAP · ${notOnMap} NOT ON MAP`,
  );
});

test('a selected anchor reports its precision, a selected corridor says it is illustrative, nothing says nothing', () => {
  const stop = OIL_GEOGRAPHY.stops[0];
  const route = OIL_GEOGRAPHY.routes[0];
  assert.ok(stop && route);
  assert.equal(
    selectionReadout(`nexus-oil-stops:${stop.id}`),
    `SELECTED: ${stop.label} · ${stop.precision.replaceAll('_', ' ').toUpperCase()}`,
  );
  assert.equal(
    selectionReadout(`nexus-oil-corridors:${route.id}`),
    `SELECTED: ${route.label} · ${route.precision.replaceAll('_', ' ').toUpperCase()}`,
  );
  assert.equal(selectionReadout(undefined), 'SELECTED: NONE');
});

test('a selection that is not a Nexus record is reported as having no stated precision, never guessed', () => {
  assert.equal(selectionReadout('some-other-entity'), 'SELECTED: NO STATED PRECISION');
  assert.equal(selectionReadout('nexus-oil-stops:missing'), 'SELECTED: NO STATED PRECISION');
});
