// The HUD's readouts about the data on show: fixed lines, and a line that follows the selection.
// hud.js imports `mgrs`, which Node's ESM loader cannot read by name, so it is stubbed (see
// hudAltitudeDatum.test.mjs for the reasoning behind the hook-then-import order).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';

const MGRS_STUB_URL = 'gev-test-stub:mgrs';
registerHooks({
  resolve(specifier, context, next) {
    if (specifier === 'mgrs') return { url: MGRS_STUB_URL, shortCircuit: true };
    return next(specifier, context);
  },
  load(url, context, next) {
    if (url === MGRS_STUB_URL) {
      return { format: 'module', shortCircuit: true, source: 'export function forward() { return ""; }\n' };
    }
    return next(url, context);
  },
});
const { IntelHUD } = await import('./hud.js');

function environment() {
  const elements = new Map();
  const previous = globalThis.document;
  globalThis.document = {
    getElementById: (id) => elements.get(id) ?? null,
    createElement: () => ({ textContent: '' }),
  };
  const listeners = new Set();
  const viewer = {
    camera: { moveEnd: { addEventListener() {}, removeEventListener() {} } },
    selectedEntityChanged: {
      addEventListener: (fn) => listeners.add(fn),
      removeEventListener: (fn) => listeners.delete(fn),
    },
  };
  return {
    elements,
    listeners,
    viewer,
    restore() {
      if (previous === undefined) delete globalThis.document;
      else globalThis.document = previous;
    },
  };
}

test('fixed lines are painted one row each, and the selection line follows the selected entity', () => {
  const env = environment();
  try {
    env.elements.set('hud-data-lines', {
      rows: [],
      replaceChildren(...rows) {
        this.rows = rows.map((row) => row.textContent);
      },
    });
    env.elements.set('hud-selection', { textContent: '' });
    const hud = new IntelHUD(env.viewer, {
      staticLines: () => ['AS OF 2026-09-22', 'PACK demo'],
      selectionLine: (id) => `SELECTED: ${id ?? 'NONE'}`,
    });
    hud._showDataLines();
    assert.deepEqual(env.elements.get('hud-data-lines').rows, ['AS OF 2026-09-22', 'PACK demo']);

    assert.equal(env.listeners.size, 1, 'the HUD listens for selection changes');
    for (const listener of env.listeners) listener({ id: 'stop-1' });
    assert.equal(env.elements.get('hud-selection').textContent, 'SELECTED: stop-1');
    for (const listener of env.listeners) listener(undefined);
    assert.equal(env.elements.get('hud-selection').textContent, 'SELECTED: NONE');

    hud.destroy();
    assert.equal(env.listeners.size, 0, 'destroying the HUD stops the selection subscription');
  } finally {
    env.restore();
  }
});

test('without readouts the HUD subscribes to nothing and paints no lines', () => {
  const env = environment();
  try {
    const hud = new IntelHUD(env.viewer);
    assert.equal(env.listeners.size, 0);
    hud._showDataLines();
    hud.destroy();
  } finally {
    env.restore();
  }
});
