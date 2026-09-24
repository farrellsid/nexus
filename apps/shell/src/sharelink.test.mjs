// Share links carry the shell's state in the URL hash. What comes back out of a hash is untrusted
// text, so these tests pin two things: a state that goes in comes back unchanged, and a hash that is
// malformed or hostile is refused or reduced to safe values, never acted on.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ShareLinkManager } from './sharelink.js';
import { createDefaultLayerState } from './data/layerState.js';

const DEG = Math.PI / 180;

function makeManager(hash = '', camera = {}) {
  globalThis.window = { location: { hash, href: `http://localhost/${hash}` } };
  globalThis.history = {
    replaceState(_state, _title, next) {
      window.location.hash = next;
    },
  };
  const viewer = {
    camera: {
      changed: { addEventListener() {} },
      positionCartographic: { latitude: 0, longitude: 0, height: 1000, ...camera.position },
      heading: 0,
      pitch: -Math.PI / 2,
      roll: 0,
      ...camera.angles,
    },
  };
  return new ShareLinkManager(viewer);
}

test('a camera and layer state written to a hash reads back as the same state', () => {
  const writer = makeManager('', {
    position: { latitude: 26.6 * DEG, longitude: 56.5 * DEG, height: 450000 },
    angles: { heading: 30 * DEG, pitch: -55 * DEG, roll: 0 },
  });
  const layers = createDefaultLayerState();
  layers.enabledLayerIds = ['nexus-oil-stops', 'nexus-oil-corridors'];
  writer.setLayerStateProvider(() => layers);
  writer._mapStack = 'osm';
  const hash = writer._buildHashParams().toString();

  const state = makeManager(`#${hash}`).parseInitialHash();
  assert.ok(state, 'the written hash must parse');
  assert.equal(state.lat, 26.6);
  assert.equal(state.lon, 56.5);
  assert.equal(state.alt, 450000);
  assert.equal(state.heading, 30);
  assert.equal(state.pitch, -55);
  assert.equal(state.mapStack, 'osm');
  assert.deepEqual([...state.layerState.enabledLayerIds].sort(), ['nexus-oil-corridors', 'nexus-oil-stops']);
});

test('a hash with no usable position is ignored', () => {
  for (const hash of [
    '',
    '#',
    '#nonsense',
    '#lat=abc&lon=def',
    '#lat=NaN&lon=1',
    '#lat=Infinity&lon=1',
    '#lat=1&lon=-Infinity',
    '#lat=1',
    '#lon=1',
    '#lat=91&lon=0',
    '#lat=-90.5&lon=0',
    '#lat=0&lon=181',
    '#lat=0&lon=-360',
    '#lat=1e400&lon=1',
  ]) {
    assert.equal(makeManager(hash).parseInitialHash(), null, `hash ${JSON.stringify(hash)} must be ignored`);
  }
});

test('camera values from a hash are held to what a camera can be', () => {
  const state = makeManager('#lat=10&lon=20&alt=1e300&heading=99999&pitch=-500&roll=Infinity').parseInitialHash();
  assert.ok(state);
  assert.ok(state.alt > 0 && state.alt <= 60_000_000, `alt ${state.alt}`);
  assert.ok(state.heading >= -360 && state.heading <= 360, `heading ${state.heading}`);
  assert.ok(state.pitch >= -90 && state.pitch <= 90, `pitch ${state.pitch}`);
  assert.ok(state.roll >= -360 && state.roll <= 360, `roll ${state.roll}`);
  const negative = makeManager('#lat=10&lon=20&alt=-5000').parseInitialHash();
  assert.ok(negative && negative.alt > 0, 'a negative altitude is not below the ground');
});

test('names that are not shell values fall back to the defaults, whatever they resemble', () => {
  const state = makeManager(
    '#lat=10&lon=20&style=constructor&map=__proto__&hud=<script>alert(1)</script>&v=2&l=zz',
  ).parseInitialHash();
  assert.ok(state);
  assert.equal(state.style, 'normal');
  assert.equal(typeof state.style, 'string');
  assert.equal(state.layerState, null, 'an undecodable layer list restores nothing');
  for (const name of ['__proto__', 'constructor', 'toString', 'hasOwnProperty']) {
    assert.equal(makeManager(`#lat=1&lon=1&style=${name}`).parseInitialHash().style, 'normal', name);
  }
});

test('a hash cannot enable a layer the shell does not have', () => {
  const state = makeManager('#lat=10&lon=20&v=2&l=evil-layer,nexus-oil-stops').parseInitialHash();
  assert.ok(state);
  const enabled = state.layerState?.enabledLayerIds ?? [];
  assert.ok(!enabled.includes('evil-layer'));
});

test('an enormous or repeated hash is read without harm', () => {
  const long = `#lat=10&lon=20&${'x=1&'.repeat(50_000)}style=${'a'.repeat(100_000)}`;
  const state = makeManager(long).parseInitialHash();
  assert.ok(state);
  assert.equal(state.style, 'normal');
  const repeated = makeManager('#lat=10&lat=99&lon=20&lon=5').parseInitialHash();
  assert.ok(repeated && repeated.lat === 10 && repeated.lon === 20, 'the first value wins, as URLSearchParams reads it');
});

test('reading a hostile hash runs nothing and touches no global', () => {
  const before = Object.keys(globalThis).sort();
  makeManager('#lat=1&lon=1&style=__proto__&map=%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E&hud=constructor').parseInitialHash();
  assert.deepEqual(Object.keys(globalThis).filter((key) => !before.includes(key)), []);
  assert.equal({}.polluted, undefined);
});
