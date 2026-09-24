import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createActionRegistry, type ActionCatalogue, type ShellControls } from './actions.ts';

const catalogue: ActionCatalogue = {
  places: { 'gulf-and-red-sea': 3 },
  layerIds: ['nexus-oil-stops', 'nexus-oil-corridors'],
};

/** Controls that record every call, so a test can say what a verb did and did not touch. */
function recordingControls(overrides: Partial<ShellControls> = {}) {
  const calls: string[] = [];
  const controls: ShellControls = {
    flyToPlace: (destination, place) => (calls.push(`fly:${destination}:${place}`), true),
    setLayerVisible: async (layer, visible) => void calls.push(`layer:${layer}:${visible}`),
    playTour: async () => (calls.push('play'), true),
    stopTour: () => void calls.push('stop'),
    enterGlobalContext: async () => void calls.push('global:on'),
    exitGlobalContext: async () => void calls.push('global:off'),
    resetView: () => void calls.push('reset'),
    ...overrides,
  };
  return { calls, registry: createActionRegistry(controls, catalogue) };
}

test('every listed verb runs with valid arguments and reaches exactly one control', async () => {
  const { calls, registry } = recordingControls();
  const valid: [string, unknown][] = [
    ['fly_to_place', { destination: 'gulf-and-red-sea', place: 2 }],
    ['fly_to_place', { destination: 'gulf-and-red-sea' }],
    ['set_layer', { layer: 'nexus-oil-stops', visible: false }],
    ['play_tour', {}],
    ['stop_tour', {}],
    ['global_context', { on: true }],
    ['global_context', { on: false }],
    ['reset_view', {}],
  ];
  for (const [name, args] of valid) assert.deepEqual(await registry.run(name, args), { ok: true }, name);
  assert.deepEqual(calls, [
    'fly:gulf-and-red-sea:2',
    'fly:gulf-and-red-sea:0',
    'layer:nexus-oil-stops:false',
    'play',
    'stop',
    'global:on',
    'global:off',
    'reset',
  ]);
  const listed = registry.describe().map((verb) => verb.name);
  for (const [name] of valid) assert.ok(listed.includes(name), `${name} is not described`);
});

test('unknown verbs are refused, including names that exist on every object', async () => {
  const { calls, registry } = recordingControls();
  for (const name of ['delete_evidence', 'constructor', 'toString', '__proto__', '', 42, null, undefined]) {
    const result = await registry.run(name, {});
    assert.equal(result.ok, false, String(name));
  }
  assert.deepEqual(calls, []);
});

test('each verb rejects arguments it does not declare, of the wrong type, or naming things that do not exist', async () => {
  const { calls, registry } = recordingControls();
  const bad: [string, unknown][] = [
    ['fly_to_place', { destination: 'nowhere' }],
    ['fly_to_place', { destination: 'constructor' }],
    ['fly_to_place', { destination: 'gulf-and-red-sea', place: 3 }],
    ['fly_to_place', { destination: 'gulf-and-red-sea', place: -1 }],
    ['fly_to_place', { destination: 'gulf-and-red-sea', place: 1.5 }],
    ['fly_to_place', { destination: 'gulf-and-red-sea', place: '1' }],
    ['fly_to_place', { destination: 7 }],
    ['fly_to_place', {}],
    ['fly_to_place', { destination: 'gulf-and-red-sea', url: 'https://example.com' }],
    ['set_layer', { layer: 'made-up', visible: true }],
    ['set_layer', { layer: 'nexus-oil-stops' }],
    ['set_layer', { layer: 'nexus-oil-stops', visible: 'yes' }],
    ['set_layer', { layer: 'nexus-oil-stops', visible: true, origin: 'system' }],
    ['play_tour', { speed: 2 }],
    ['stop_tour', { force: true }],
    ['global_context', {}],
    ['global_context', { on: 1 }],
    ['reset_view', { hard: true }],
  ];
  for (const [name, args] of bad) {
    const result = await registry.run(name, args);
    assert.equal(result.ok, false, `${name} ${JSON.stringify(args)} should be refused`);
  }
  assert.deepEqual(calls, [], 'a refused verb must not touch the shell');
});

test('arguments that are not a plain object are refused', async () => {
  const { calls, registry } = recordingControls();
  for (const args of ['x', 5, null, [], [{ on: true }]]) {
    assert.equal((await registry.run('global_context', args)).ok, false, JSON.stringify(args));
  }
  assert.deepEqual(calls, []);
});

test('an inherited property is not read as an argument', async () => {
  const { registry } = recordingControls();
  const inherited = Object.create({ destination: 'gulf-and-red-sea' }) as Record<string, unknown>;
  assert.equal((await registry.run('fly_to_place', inherited)).ok, false);
});

test('a control that throws or declines becomes a failed result, not an exception', async () => {
  const { registry } = recordingControls({
    flyToPlace: () => false,
    playTour: async () => {
      throw new Error('director is gone');
    },
  });
  assert.equal((await registry.run('fly_to_place', { destination: 'gulf-and-red-sea' })).ok, false);
  const failed = await registry.run('play_tour', {});
  assert.deepEqual(failed, { ok: false, error: 'play_tour failed: director is gone' });
});

test('the action layer has no way to make a request or write evidence', () => {
  const source = readFileSync(new URL('./actions.ts', import.meta.url), 'utf8');
  const code = source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, '');
  assert.doesNotMatch(code, /\bimport\b/, 'the registry imports nothing, so it reaches nothing but its controls');
  assert.doesNotMatch(code, /\b(fetch|XMLHttpRequest|WebSocket|EventSource|sendBeacon|localStorage|indexedDB|eval|Function)\b/);
});
