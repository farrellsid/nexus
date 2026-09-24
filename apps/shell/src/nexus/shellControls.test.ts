import assert from 'node:assert/strict';
import test from 'node:test';
import { createShellControls, type CameraPose, type ShellPorts } from './shellControls.ts';

const HOME: CameraPose = { longitude: 78, latitude: 12, heightM: 12_000_000, heading: 0, pitch: -1.5, roll: 0 };
const CLOSE: CameraPose = { longitude: 56.5, latitude: 26.6, heightM: 300_000, heading: 0.3, pitch: -0.9, roll: 0 };
const LAYERS = ['stops', 'corridors'];

/** Ports over a small in-memory shell, logging every call in order. */
function fakeShell(initial: { camera: CameraPose; visible: string[] }) {
  const log: string[] = [];
  const state = { camera: initial.camera, visible: new Set(initial.visible) };
  const ports: ShellPorts = {
    readCameraPose: () => state.camera,
    flyToPose: (pose) => {
      log.push('pose');
      state.camera = pose;
    },
    flyToGlobe: () => {
      log.push('globe');
      state.camera = { ...state.camera, heightM: 18_000_000 };
    },
    flyToOpeningView: () => {
      log.push('opening');
      state.camera = HOME;
    },
    flyToPlace: () => true,
    isLayerVisible: (id) => state.visible.has(id),
    setLayerVisible: async (id, visible) => {
      log.push(`${id}:${visible}`);
      if (visible) state.visible.add(id);
      else state.visible.delete(id);
    },
    playTour: async () => true,
    stopTour: () => undefined,
  };
  return { state, log, controls: createShellControls(ports, LAYERS) };
}

test('global context pulls out to the globe with the layers on, and exit puts both back', async () => {
  const shell = fakeShell({ camera: CLOSE, visible: [] });
  await shell.controls.enterGlobalContext();
  assert.equal(shell.state.camera.heightM, 18_000_000);
  assert.deepEqual([...shell.state.visible].sort(), ['corridors', 'stops']);

  await shell.controls.exitGlobalContext();
  assert.deepEqual(shell.state.camera, CLOSE, 'the view before entering comes back');
  assert.deepEqual([...shell.state.visible], [], 'layers that were off go back off');
});

test('exit restores each layer to what it was, not to off', async () => {
  const shell = fakeShell({ camera: CLOSE, visible: ['stops'] });
  await shell.controls.enterGlobalContext();
  await shell.controls.exitGlobalContext();
  assert.deepEqual([...shell.state.visible], ['stops']);
});

test('entering twice keeps the first view to return to', async () => {
  const shell = fakeShell({ camera: CLOSE, visible: [] });
  await shell.controls.enterGlobalContext();
  await shell.controls.enterGlobalContext();
  await shell.controls.exitGlobalContext();
  assert.deepEqual(shell.state.camera, CLOSE);
});

test('exiting when global context is not on changes nothing', async () => {
  const shell = fakeShell({ camera: CLOSE, visible: ['stops'] });
  await shell.controls.exitGlobalContext();
  assert.deepEqual(shell.log, []);
  assert.deepEqual(shell.state.camera, CLOSE);
});

test('a second entry after an exit takes a fresh snapshot', async () => {
  const shell = fakeShell({ camera: CLOSE, visible: [] });
  await shell.controls.enterGlobalContext();
  await shell.controls.exitGlobalContext();
  shell.state.camera = HOME;
  await shell.controls.enterGlobalContext();
  await shell.controls.exitGlobalContext();
  assert.deepEqual(shell.state.camera, HOME);
});
