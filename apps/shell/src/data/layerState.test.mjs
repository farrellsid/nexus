import { readShellSource } from '../testSupport/readShellSource.mjs';
import { expandApplicationHtml } from '../../build/application-html.js';
import test from 'node:test';
import assert from 'node:assert/strict';

import { DataLayerManager } from './manager.js';
import {
  LAYER_STATE_REGISTRY,
  LAYER_STATE_STORAGE_KEY,
  LayerStateCoordinator,
  REGISTERED_LAYER_IDS,
  createDefaultLayerState,
  decodeLayerStateParams,
  encodeLayerStateParams,
  normalizeLayerState,
  parseStoredLayerState,
  serializeStoredLayerState,
  validateLayerStateRegistry,
} from './layerState.js';
import { stampInitialShareGesture } from '../navigationPolicy.js';

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

function paramsForLayer(id) {
  if (id === 'flights' || id === 'military') {
    return { models3d: false, models3dMode: 'proximity', irBoost: true };
  }
  if (id === 'satellites') return { catalog: 'core', showPoints: false, showOrbits: false };
  if (id === 'cctv') {
    return {
      coverageMode: 'on',
      showProjection: true,
      autoHop: false,
      autoHopSec: 22,
      selectedCameraId: 'secret-camera',
      calibrationMode: true,
      calibration: { cameraId: 'secret-camera', values: { heading: 12 } },
    };
  }
  if (id === 'nexus-oil-corridors') {
    return {
      filter: 'all',
      volume: 0.8,
      selectedStationId: 'private-station',
      audioState: 'playing',
      voiceDucked: true,
    };
  }
  return null;
}

function fakeLayer(id, hooks = {}) {
  let params = paramsForLayer(id);
  return {
    id,
    name: id,
    icon: '',
    source: 'test',
    async init() { return hooks.init ? hooks.init() : true; },
    async enable() { return hooks.enable ? hooks.enable() : true; },
    async update() { return hooks.update ? hooks.update() : true; },
    async disable() { return hooks.disable ? hooks.disable() : true; },
    ...(hooks.resolveTrackingRestoreTarget ? {
      async resolveTrackingRestoreTarget(targetId, options) {
        return hooks.resolveTrackingRestoreTarget(targetId, options);
      },
    } : {}),
    ...(params ? {
      setParams(next = {}, options = {}) {
        if (hooks.setParams) {
          const result = hooks.setParams(next, options);
          if (result === false) return false;
          // 'defer' models the production tracking latch: the layer ACCEPTS the
          // request and holds it pending, but getParams() keeps reporting the
          // previous (still-untracked) value until the subject really arrives.
          if (result === 'defer') return true;
        }
        params = { ...params, ...next };
        return true;
      },
      /** Test seam: a deferred subject finally arrives on a later poll. */
      _arrive(next) { params = { ...params, ...next }; },
      getParams() { return { ...params }; },
      ...(hooks.cancelPendingTrackingRestore ? {
        cancelPendingTrackingRestore(options) { hooks.cancelPendingTrackingRestore(options); },
      } : {}),
    } : {}),
  };
}

function productionManager(hooksById = {}) {
  const manager = new DataLayerManager({});
  for (const id of REGISTERED_LAYER_IDS) manager.register(fakeLayer(id, hooksById[id] || {}));
  manager.finalizeRegistrations(LAYER_STATE_REGISTRY);
  return manager;
}

/**
 * Deterministic clock + timer queue for the pending-tracking window, so the
 * 90 s / 45 s / 300 s expiries are provable without sleeping.
 */
function manualTimers(startMs = 0) {
  let nowMs = startMs;
  let queued = null;
  return {
    now: () => nowMs,
    setTimer: (fn, ms) => { queued = { fn, ms }; return queued; },
    clearTimer: (handle) => { if (queued === handle) queued = null; },
    /** Fire queued polls, advancing the clock, until nothing re-arms. */
    runUntilIdle(maxTicks = 2_000) {
      for (let tick = 0; tick < maxTicks; tick += 1) {
        const pending = queued;
        if (!pending) return;
        queued = null;
        nowMs += pending.ms;
        pending.fn();
      }
      throw new Error('pending-tracking watch never settled');
    },
  };
}

function memoryStorage(initial = null) {
  const values = new Map();
  if (initial !== null) values.set(LAYER_STATE_STORAGE_KEY, initial);
  return {
    writes: [],
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) {
      values.set(key, value);
      this.writes.push([key, value]);
    },
  };
}

function shareSink() {
  return {
    provider: null,
    updates: 0,
    setLayerStateProvider(provider) { this.provider = provider; },
    onLayerStateChange() { this.updates += 1; },
  };
}

function encode(state) {
  const params = new URLSearchParams([['v', '2']]);
  encodeLayerStateParams(params, state);
  return params.toString();
}

test('production registry is exact, canonical, and rejects incomplete contracts', async () => {
  assert.equal(validateLayerStateRegistry(), true);
  assert.equal(REGISTERED_LAYER_IDS.length, 2);
  assert.equal(new Set(REGISTERED_LAYER_IDS).size, 2);
  assert.ok(REGISTERED_LAYER_IDS.includes('nexus-oil-corridors'));
  assert.deepEqual(REGISTERED_LAYER_IDS, [...REGISTERED_LAYER_IDS].sort());
  assert.throws(
    () => validateLayerStateRegistry([...LAYER_STATE_REGISTRY, LAYER_STATE_REGISTRY[0]]),
    /Duplicate layer-state id/,
  );

  const manager = new DataLayerManager({});
  manager.register(fakeLayer('nexus-oil-stops'));
  assert.throws(() => manager.register(fakeLayer('nexus-oil-stops')), /Duplicate data-layer id/);
  await assert.rejects(manager.restoreLayerState('nexus-oil-stops', { enabled: true }), /finalized/);
  assert.throws(() => manager.finalizeRegistrations([]), /registry mismatch/);
  assert.throws(
    () => manager.finalizeRegistrations([{ id: 'nexus-oil-stops', disposition: 'default' }]),
    /Invalid layer serialization disposition/,
  );
  assert.equal(manager.finalizeRegistrations([
    { id: 'nexus-oil-stops', disposition: 'enabled-only' },
  ]), true);
  assert.throws(() => manager.register(fakeLayer('nexus-oil-corridors')), /finalized/);
  assert.throws(() => manager.registerForQa(fakeLayer('nexus-oil-corridors')), /not authorized/);
  const qaManager = new DataLayerManager({}, { allowQaRegistration: true });
  qaManager.register(fakeLayer('nexus-oil-stops'));
  qaManager.finalizeRegistrations([{ id: 'nexus-oil-stops', disposition: 'enabled-only' }]);
  qaManager.registerForQa(fakeLayer('nexus-oil-corridors'));
  assert.equal(qaManager.layers.has('nexus-oil-corridors'), true);
  assert.equal(await qaManager.unregisterForQa('nexus-oil-corridors'), true);
  assert.equal(qaManager.layers.has('nexus-oil-corridors'), false);
});

test('unknown enabled-layer tokens reject the payload instead of becoming an empty set', () => {
  assert.equal(decodeLayerStateParams(new URLSearchParams('v=2&l=unknown')), null);
  assert.equal(decodeLayerStateParams(new URLSearchParams('v=2&l=c.unknown')), null);
});

test('stored state is deterministic, rejects other versions, and stays within a tested URL bound', () => {
  const state = createDefaultLayerState();
  state.enabledLayerIds = [...REGISTERED_LAYER_IDS].reverse();
  state.options.flights = { models3d: true, models3dMode: 'all' };
  state.options.satellites = { catalog: 'dense' };
  state.options.cctv = { coverageMode: 'viewshed', showProjection: false, autoHop: true };
  state.options.radio = { filter: 'genre:experimental-ambient', volume: 1 };
  const stored = serializeStoredLayerState(state);
  assert.deepEqual(parseStoredLayerState(stored), normalizeLayerState(state));
  assert.equal(parseStoredLayerState('{"v":1,"l":[]}'), null);
  assert.ok(encode(state).length < 420, encode(state));
});

test('historical share payload suppresses unrelated local layer preferences', async () => {
  const local = createDefaultLayerState();
  local.enabledLayerIds = ['nexus-oil-corridors', 'nexus-oil-corridors'];
  const storage = memoryStorage(serializeStoredLayerState(local));
  const manager = productionManager();
  const coordinator = new LayerStateCoordinator(manager, shareSink(), { storage });
  await coordinator.start({ allowLocalState: false });
  assert.equal(coordinator.source, 'legacy-share');
  assert.deepEqual(coordinator.getDurableState().enabledLayerIds, []);
  assert.equal(manager.getEnabledLayerIds().size, 0);
  assert.deepEqual(storage.writes, []);
  coordinator.destroy();
});

test('one layer failure is isolated from sibling restoration', async () => {
  const manager = productionManager({
    'nexus-oil-corridors': { init: () => { throw new Error('missing key'); } },
  });
  const state = createDefaultLayerState();
  state.enabledLayerIds = ['nexus-oil-corridors', 'nexus-oil-stops'];
  const coordinator = new LayerStateCoordinator(manager, shareSink(), { storage: memoryStorage() });
  const results = await coordinator.start({ shareLayerState: state });
  assert.equal(manager.isEnabled('nexus-oil-corridors'), false);
  assert.equal(manager.isEnabled('nexus-oil-stops'), true);
  const failed = results.find((result) => result.layerId === 'nexus-oil-corridors');
  assert.equal(failed.succeeded, false);
  assert.equal(failed.phase, 'init');
  assert.equal(failed.errorClass, 'Error');
  assert.equal(failed.error, 'missing key');
  assert.equal(results.find((result) => result.layerId === 'nexus-oil-stops').succeeded, true);
  coordinator.destroy();
});

test('later explicit visibility during delayed restore wins for that layer only', async () => {
  const gate = deferred();
  const manager = productionManager();
  const storage = memoryStorage();
  const state = createDefaultLayerState();
  state.enabledLayerIds = ['nexus-oil-corridors', 'nexus-oil-stops'];
  const coordinator = new LayerStateCoordinator(manager, shareSink(), {
    storage,
    restoreGate: gate.promise,
  });
  const restore = coordinator.start({ shareLayerState: state });
  await manager.setEnabled('nexus-oil-corridors', false, { origin: 'user' });
  gate.resolve();
  const results = await restore;
  assert.equal(manager.isEnabled('nexus-oil-corridors'), false);
  assert.equal(manager.isEnabled('nexus-oil-stops'), true);
  assert.equal(results.find((result) => result.layerId === 'nexus-oil-corridors').cancellationReason, 'superseded');
  assert.equal(storage.writes.length, 1);
  coordinator.destroy();
});

test('share restore waits for a superseding same-target visibility successor', async () => {
  const firstUpdateStarted = deferred();
  const releaseFirstUpdate = deferred();
  const secondUpdateStarted = deferred();
  const releaseSecondUpdate = deferred();
  let updateCount = 0;
  const manager = productionManager({
    'nexus-oil-corridors': {
      update: async () => {
        updateCount += 1;
        if (updateCount === 1) {
          firstUpdateStarted.resolve();
          await releaseFirstUpdate.promise;
        } else if (updateCount === 2) {
          secondUpdateStarted.resolve();
          await releaseSecondUpdate.promise;
        }
        return true;
      },
    },
  });
  const state = createDefaultLayerState();
  state.enabledLayerIds = ['nexus-oil-corridors'];
  const coordinator = new LayerStateCoordinator(manager, shareSink(), { storage: memoryStorage() });

  let restoreSettled = false;
  const restore = coordinator.start({ shareLayerState: state })
    .then((result) => { restoreSettled = true; return result; });
  await firstUpdateStarted.promise;
  let successorSettled = false;
  const explicitOn = manager.setEnabled('nexus-oil-corridors', true, { origin: 'user' })
    .then((result) => { successorSettled = true; return result; });
  releaseFirstUpdate.resolve();
  await secondUpdateStarted.promise;
  await Promise.resolve();
  assert.equal(restoreSettled, false, 'aggregate must wait for the authoritative successor');
  assert.equal(successorSettled, false);

  releaseSecondUpdate.resolve();
  assert.equal(await explicitOn, true);
  const results = await restore;
  const radio = results.find((result) => result.layerId === 'nexus-oil-corridors');
  assert.equal(radio.cancellationReason, 'superseded');
  assert.equal(radio.successorEnabled, true);
  assert.equal(radio.authoritativeIntentEpoch, radio.successorIntentEpoch);
  assert.equal(radio.authoritativeEnabled, true);
  assert.equal(radio.succeeded, true);
  assert.equal(manager.getLayerLifecycleState('nexus-oil-corridors').lifecycleState, 'enabled');
  coordinator.destroy();
});

test('share restore waits for a superseding opposite-target visibility successor', async () => {
  const updateStarted = deferred();
  const releaseUpdate = deferred();
  const disableStarted = deferred();
  const releaseDisable = deferred();
  const manager = productionManager({
    'nexus-oil-corridors': {
      update: async () => {
        updateStarted.resolve();
        await releaseUpdate.promise;
        return true;
      },
      disable: async () => {
        disableStarted.resolve();
        await releaseDisable.promise;
        return true;
      },
    },
  });
  const state = createDefaultLayerState();
  state.enabledLayerIds = ['nexus-oil-corridors'];
  const coordinator = new LayerStateCoordinator(manager, shareSink(), { storage: memoryStorage() });

  let restoreSettled = false;
  const restore = coordinator.start({ shareLayerState: state })
    .then((result) => { restoreSettled = true; return result; });
  await updateStarted.promise;
  const explicitOff = manager.setEnabled('nexus-oil-corridors', false, { origin: 'user' });
  releaseUpdate.resolve();
  await disableStarted.promise;
  await Promise.resolve();
  assert.equal(restoreSettled, false, 'aggregate must wait for the OFF successor to settle');

  releaseDisable.resolve();
  assert.equal(await explicitOff, true);
  const results = await restore;
  const radio = results.find((result) => result.layerId === 'nexus-oil-corridors');
  assert.equal(radio.cancellationReason, 'superseded');
  assert.equal(radio.successorEnabled, false);
  assert.equal(radio.authoritativeIntentEpoch, radio.successorIntentEpoch);
  assert.equal(radio.authoritativeEnabled, false);
  assert.equal(radio.succeeded, false, 'the newer OFF must not count as successful shared ON');
  assert.equal(manager.getLayerLifecycleState('nexus-oil-corridors').lifecycleState, 'disabled');
  coordinator.destroy();
});

// ---------------------------------------------------------------------------
// Share restore must be as resilient as reload-from-local.
//
// Reload-from-local arms the layer's own deferred-restore latch, which
// re-attempts on every later poll, so a contact that misses the first refresh
// is still picked up. The shared path used to decide on that single refresh:
// it cleared the subject from durable state AND the URL and posted a failure
// notice seconds into startup, so the SAME link healed on reload but never on
// the share. These pin both directions.
// ---------------------------------------------------------------------------

function pendingTrackingFixture({ resolveStatus = 'missing', copiedAtMs = null } = {}) {
  const storage = memoryStorage();
  const statuses = [];
  const paramsCalls = [];
  const cancellations = [];
  const manager = productionManager({
    flights: {
      resolveTrackingRestoreTarget: () => ({ status: resolveStatus }),
      setParams: (next, options) => {
        paramsCalls.push({ params: { ...next }, origin: options?.origin });
        // Production holds the id pending; getParams keeps reporting untracked
        // until the subject actually arrives on a later poll.
        return Object.hasOwn(next, 'selectedFlightsTrackingId') && next.selectedFlightsTrackingId
          ? 'defer'
          : true;
      },
      cancelPendingTrackingRestore: (options) => cancellations.push(options),
    },
  });
  const state = createDefaultLayerState();
  state.enabledLayerIds = ['flights'];
  state.options.flights = {
    ...state.options.flights,
    selectedFlightsTrackingId: 'late007',
  };
  const timers = manualTimers();
  const coordinator = new LayerStateCoordinator(manager, shareSink(), {
    storage,
    now: timers.now,
    setTimer: timers.setTimer,
    clearTimer: timers.clearTimer,
    onTrackingRestoreStatus: (status) => statuses.push(status),
  });
  return {
    manager,
    coordinator,
    statuses,
    storage,
    timers,
    state,
    copiedAtMs,
    paramsCalls,
    cancellations,
  };
}

// ---------------------------------------------------------------------------
// Share IDs and payloads are untrusted input and must be BOUNDED.
//
// A tracking ID is a transponder address, not free text. Identity is never
// truncated to fit: half an address is a different aircraft, not a shorter name
// for the same one, so an out-of-grammar ID is rejected outright and an
// oversized payload fails closed exactly like an unknown layer token.
// ---------------------------------------------------------------------------

test('an oversized enabled-layer field fails closed instead of decoding a prefix', () => {
  assert.equal(
    decodeLayerStateParams(new URLSearchParams([['v', '2'], ['l', 'f.'.repeat(5_000)]])),
    null,
  );
});

// ---------------------------------------------------------------------------
// The pending watch and the LAYER's deferred-restore latch are two halves of
// one mechanism and must die together.
//
// Aborting only the restore controller was a no-op by the time the watch
// existed (the controller has already settled), so the orphaned timer went on
// to announce "Shared … unavailable" at its deadline — a verdict about work
// nothing was attempting any more. Both paths below cancel the module latch in
// production: an explicit parameter replacement, and the owner layer going
// away (at any origin, including a programmatic disable).
// ---------------------------------------------------------------------------

