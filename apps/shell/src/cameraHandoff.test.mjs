import { LayerBindings } from './ui/layerBindings.js';
import { readShellSource, shellMethod } from './testSupport/readShellSource.mjs';
import { readLayerSource } from './testSupport/readLayerSource.mjs';
import { StyleManager } from './ui/applicationShell.js';
import { enter as cockpitEnter, navigateContext } from './ui/cockpitTrackingController.js';
import { CockpitViewController } from './ui/cockpitController.js';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ui = readShellSource();
const firms = readLayerSource(path.join(ROOT, 'src', 'data', 'firmsHeatmap.js'));
const vessels = readLayerSource(path.join(ROOT, 'src', 'data', 'aisLiveVessels.js'));
const cameraVerbs = fs.readFileSync(path.join(ROOT, 'src', 'cameraVerbs.js'), 'utf8');
const cockpitTracking = fs.readFileSync(path.join(ROOT, 'src', 'cockpitTracking.js'), 'utf8');

function body(source, pattern, label) {
  const name = pattern.source.match(/^(\w+)/)?.[1];
  if (source === ui && typeof shellMethod(name) === 'function') {
    const method = shellMethod(name).toString();
    return method.slice(method.indexOf(') {') + 3, -1);
  }
  const match = source.match(pattern);
  assert.ok(match, `${label} is missing`);
  return match[1];
}

function ordered(source, needles, label) {
  let previous = -1;
  for (const needle of needles) {
    const match = needle instanceof RegExp ? needle.exec(source.slice(previous + 1)) : null;
    const index = needle instanceof RegExp ? (match ? previous + 1 + match.index : -1) : source.indexOf(needle, previous + 1);
    assert.ok(index >= 0, `${label}: missing ${needle}`);
    assert.ok(index > previous, `${label}: ${needle} is out of order`);
    previous = index;
  }
}

test('Cockpit takeover invalidates deferred work before camera cancellation', () => {
  const enter = cockpitEnter.toString();
  ordered(enter, [
    'if (!info || !entity?.position) return false;',
    'this.onCameraTakeover?.();',
    'this.viewer.camera.cancelFlight();',
    'this.viewer.trackedEntity = undefined;',
  ], 'Cockpit takeover');
  assert.match(
    ui,
    /onCameraTakeover: \(\) =>\s*this\._stampNavigation\(\{\s*cancelPendingSelection: false,?\s*\}\),/,
    'Cockpit retires stale camera work without clearing the aircraft selection it adopts',
  );
});

test('one explicit tracking selection clears sibling IDs before publishing its durable replacement', () => {
  const persist = body(
    ui,
    /_persistAwarenessSelection\(event, cleared = false\) \{([\s\S]*?)\n  \}/,
    'tracking persistence',
  );
  assert.match(persist, /adoptLayerParams\?\.\(\s*layerId,/);
  assert.match(persist, /\['flights', 'selectedFlightsTrackingId'\]/);
  assert.match(persist, /\['military', 'selectedMilitaryTrackingId'\]/);
  assert.match(persist, /\['satellites', 'selectedSatTrackingId'\]/);
  assert.match(persist, /if \(otherLayerId === layerId\) continue;/);
  assert.match(
    persist,
    /for \(const \[otherLayerId, otherKey\][\s\S]*?setLayerParams\(\s*otherLayerId,[\s\S]*?adoptLayerParams\?\.\(\s*layerId,/,
    'the previous family clears before Flight/Military/Satellite publishes the new durable ID',
  );
});

test('navigation clears dormant tracker IDs without aborting unrelated layer restoration', () => {
  const stamp = body(
    ui,
    /_stampNavigation\(\{ cancelPendingSelection = true[^)]*\} = \{\}\) \{([\s\S]*?)\n  \}/,
    'navigation authority stamp',
  );
  assert.doesNotMatch(stamp, /cancelPendingRestores\(\)/);
  assert.match(stamp, /flightsLayer\.cancelPendingTrackingRestore\?\.\(\)/);
  assert.match(stamp, /militaryFlightsLayer\.cancelPendingTrackingRestore\?\.\(\)/);
  assert.match(stamp, /satellitesLayer\.cancelPendingTrackingRestore\?\.\(\)/);
  assert.match(stamp, /if \(\s*!passivelyClearedShareSelection\s*&&\s*!flightsLayer\.getTrackedInfo\?\.\(\)\s*\)[\s\S]*?selectedFlightsTrackingId: null/);
  assert.match(stamp, /if \(\s*!passivelyClearedShareSelection\s*&&\s*!militaryFlightsLayer\.getTrackedInfo\?\.\(\)\s*\)[\s\S]*?selectedMilitaryTrackingId: null/);
  assert.match(stamp, /if \(\s*!passivelyClearedShareSelection\s*&&\s*!satellitesLayer\.getTrackedInfo\?\.\(\)\s*\)[\s\S]*?selectedSatTrackingId: null/);
});

test('voice Cockpit entry reaches the camera only through stamping seams', () => {
  // Cockpit is the camera-authority VETO HOLDER, not a petitioner: routing
  // entry through _runExplicitNavigation would make it refuse itself, because
  // cockpitActive is the state entry is trying to reach. What entry owes the
  // policy is the STAMP that retires deferred navigation — and the voice path
  // must not acquire the camera by any route that skips it.
  //
  // The transaction has exactly two camera-owner mutations, and each one
  // stamps:
  //   1. selectedLayer.trackById(id) -> viewer.trackedEntity
  //        -> viewer.trackedEntityChanged -> _stampNavigation()
  //   2. cockpitView.enter() -> onCameraTakeover() -> _stampNavigation()
  const transaction = body(
    cockpitTracking,
    /export function enterCockpitWithTracking\(\{[\s\S]*?\n\}\) \{([\s\S]*?)\n\}\n/,
    'Cockpit entry transaction',
  );
  ordered(transaction, [
    /if \(\s*!selectedLayer\.trackById\?\.\(selectedTarget\.id, \{\s*origin: selectionOrigin,?\s*\}\)\s*\) \{/,
    'if (!entryError) entered = Boolean(cockpitView.enter());',
  ], 'Cockpit entry transaction');
  // No direct camera control: every mutation goes through a layer tracker or
  // the cockpit controller, both of which stamp.
  assert.doesNotMatch(transaction, /\b(?:viewer\.)?camera\s*(?:\.|\[|=)/);
  assert.doesNotMatch(cockpitTracking, /trackedEntity\s*=/);
  assert.doesNotMatch(cockpitTracking, /flyTo/);

  // Seam 1: any tracker handoff stamps, so the adoption step is covered.
  assert.match(
    ui,
    /viewer\.trackedEntityChanged\.addEventListener\(\s*\(entity\) => \{\s*if \(entity && !this\._disposed\)\s*this\._stampNavigation\(\{\s*cancelPendingSelection: false,?\s*\}\);/,
    'tracker handoff must stamp',
  );
  // Seam 2 is pinned by "Cockpit takeover invalidates deferred work" above.
  const control = body(
    ui,
    /if \(normalized === 'enter'\) \{([\s\S]*?)\n    \}/,
    'controlCockpit enter branch',
  );
  assert.match(control, /enterCockpitWithTracking\(\{/);
  // A refused entry is reported as a failure, never as silent success.
  assert.match(control, /ok: entry\.entered,/);
  assert.match(control, /error: entry\.error,/);
});

test('voice Cockpit next/previous shares the manual Context navigation path', () => {
  // The voice verb must not grow a private focus route: manual PREVIOUS/NEXT
  // and the voice verb both hand off through the owning layer's tracker, which
  // is what stamps. Divergence here is how a voice-only camera path escapes
  // the arbiter.
  assert.match(
    CockpitViewController.toString(),
    /this\._listen\(this\.contextPrevious, 'click', \(\) =>\s*this\.navigateContext\(-1, \{ origin: 'user' \}\),?\s*\);/,
  );
  assert.match(
    CockpitViewController.toString(),
    /this\._listen\(this\.contextNext, 'click', \(\) =>\s*this\.navigateContext\(1, \{ origin: 'user' \}\),?\s*\);/,
  );
  const funnel = navigateContext.toString();
  assert.match(funnel, /const navigationOptions = wasActive\s*\? \{ \.\.\.options, aircraftOnly: true \}\s*: options;/);
  ordered(funnel, [
    "const method = direction < 0 ? 'navigatePrevious' : 'navigateNext';",
    'const navigationOptions = wasActive',
    'militaryAwarenessLayer?.[method]?.(navigationOptions)',
    'this._adoptTrackedEntity(performance.now());',
  ], 'Cockpit Context navigation funnel');
  const navigate = body(
    ui,
    /if \(normalized === 'next' \|\| normalized === 'previous'\) \{([\s\S]*?)\n    \}/,
    'controlCockpit navigation branch',
  );
  ordered(navigate, [
    'this.cockpitView.navigateContext(',
    "normalized === 'next' ? 1 : -1,",
  ], 'controlCockpit navigation branch');
  // No private camera route around the awareness layer.
  assert.doesNotMatch(navigate, /flyTo|camera|trackById|_runExplicitNavigation/);
  // An exhausted cohort is an honest failure, not a silent success.
  assert.match(navigate, /ok: changed,/);
  assert.match(navigate, /error: changed \? null : 'No further context target was available',/);
});

test('accepted navigation releases through PR15-aware ownership before flight', () => {
  const run = body(
    ui,
    /_runExplicitNavigation\(noun, navigate, releaseOptions = undefined\) \{([\s\S]*?)\n  \}/,
    'explicit navigation',
  );
  ordered(run, [
    'cockpitActive: this.isCockpitActive()',
    'stamp: () => this._stampNavigation()',
    'release: () => this._releaseFollowCamera(releaseOptions)',
    'navigate,',
  ], 'explicit navigation');
  const release = body(
    ui,
    /_releaseFollowCamera\(\{[\s\S]*?\} = \{\}\) \{([\s\S]*?)\n  \}/,
    'follow release',
  );
  ordered(release, [
    'origin: trackingOrigin',
    'satellitesLayer.stopTracking?.({ origin: trackingOrigin })',
    'rocketLaunchesLayer.releaseCameraOwnership?.()',
    'this.viewer.trackedEntity = undefined;',
    "interruptCameraMotion('explicit-navigation')",
    'this.viewer.camera.cancelFlight();',
    'this.viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);',
  ], 'follow release');
  assert.match(release, /flightsLayer\.stopTracking\?\.\(\{ origin: trackingOrigin \}\)/);
  assert.match(release, /militaryFlightsLayer\.stopTracking\?\.\(\{ origin: trackingOrigin \}\)/);
});

