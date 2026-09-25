import { readShellSource } from './testSupport/readShellSource.mjs';
import { expandApplicationHtml } from '../build/application-html.js';
import { readStylesheet } from './testSupport/readStylesheet.mjs';
// MAP STACK chip row — the dropdown's replacement control surface.
//
// The owner's complaint was two clicks (open panel → open dropdown) to change
// basemap. These tests pin the three things that make the row a faithful swap:
// it projects the owner-approved four-source allowlist from the controller's
// stack data, a click dispatches the same selection the `change` handler used
// to, and the lit chip tracks controller state rather than the click. Run with:
// npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  PRESENTED_MAP_STACK_IDS,
  renderMapStackChips,
  syncMapStackChips,
} from './mapStackChips.js';

/** Minimal element stand-in — the row only needs create/append/attr/class. */
function makeElement(tagName = 'div') {
  const element = {
    tagName,
    type: '',
    className: '',
    title: '',
    disabled: false,
    textContent: '',
    dataset: {},
    attributes: {},
    listeners: {},
    children: [],
    classList: {
      toggle(name, force) {
        const classes = new Set(
          String(element.className).split(/\s+/).filter(Boolean),
        );
        const next = force === undefined ? !classes.has(name) : !!force;
        if (next) classes.add(name);
        else classes.delete(name);
        element.className = [...classes].join(' ');
      },
      contains(name) {
        return String(element.className).split(/\s+/).includes(name);
      },
    },
    appendChild(child) {
      element.children.push(child);
      return child;
    },
    setAttribute(name, value) {
      element.attributes[name] = String(value);
    },
    getAttribute(name) {
      return element.attributes[name] ?? null;
    },
    addEventListener(type, handler) {
      (element.listeners[type] ||= []).push(handler);
    },
    click() {
      for (const handler of element.listeners.click || []) handler();
    },
  };
  Object.defineProperty(element, 'innerHTML', {
    get() {
      return '';
    },
    set() {
      element.children.length = 0;
    },
  });
  return element;
}

const doc = { createElement: (tagName) => makeElement(tagName) };

// Shaped exactly like MapStackController.getStacks() output.
const CONTROLLER_STACKS = [
  {
    id: 'esri-imagery',
    label: 'Esri Satellite',
    available: true,
    unavailableReason: null,
  },
  { id: 'osm', label: 'OSM', available: true, unavailableReason: null },
];

test('re-rendering replaces the previous chips instead of stacking a second row', () => {
  const container = makeElement();
  renderMapStackChips(container, CONTROLLER_STACKS, {
    activeId: 'photoreal',
    doc,
  });
  renderMapStackChips(container, CONTROLLER_STACKS, { activeId: 'osm', doc });

  assert.equal(container.children.length, PRESENTED_MAP_STACK_IDS.length);
});

test('a missing row or document is inert rather than throwing during boot', () => {
  assert.deepEqual(renderMapStackChips(null, CONTROLLER_STACKS, { doc }), []);
  assert.deepEqual(
    renderMapStackChips(makeElement(), CONTROLLER_STACKS, { doc: {} }),
    [],
  );
  assert.doesNotThrow(() => syncMapStackChips(null, 'osm'));
});

test('the active cyan survives hover', () => {
  const css = readStylesheet(new URL('../style.css', import.meta.url));
  const hover = css.indexOf('.map-stack-chip:hover');
  const active = css.indexOf('.map-stack-chip.active {');
  const unavailable = css.indexOf('.map-stack-chip.unavailable');

  assert.ok(
    hover > 0 && active > hover,
    'active must follow hover so it wins at equal specificity',
  );
  assert.ok(
    unavailable > active,
    'unavailable must follow both so a keyless chip never lights up',
  );
  assert.doesNotMatch(
    css.slice(hover, active),
    /:not\(/,
    'a :not() in the hover selector outranks .active and washes the cyan out on hover',
  );
});

test('the keyboard focus ring survives on the ACTIVE chip', () => {
  // The bug this pins: `.active` legitimately wins the color/border/background/
  // box-shadow it shares with the focus rule, and the base rule sets
  // `outline: none` — so a focus state built only from those properties is
  // INVISIBLE on the active chip. The ring must live on a property no other
  // chip-state rule sets.
  const css = readStylesheet(new URL('../style.css', import.meta.url));
  const stripComments = (text) => text.replace(/\/\*[\s\S]*?\*\//g, '');
  const chipRules = [
    ...css.matchAll(/([^{}]*\.map-stack-chip[^{}]*)\{([^{}]*)\}/g),
  ].map(([, selector, body], order) => ({
    selector: stripComments(selector).trim(),
    body: stripComments(body),
    order,
  }));
  assert.ok(chipRules.length >= 5, 'expected the chip state rules to be found');

  const ringIndex = chipRules.findIndex(
    ({ selector, body }) =>
      selector.includes(':focus-visible') &&
      /outline:\s*(?!none)\S/.test(body) &&
      /outline-offset:/.test(body),
  );
  assert.ok(
    ringIndex >= 0,
    'a :focus-visible rule must draw a real outline ring',
  );

  // Nothing after it may touch outline again, so the ring cannot be erased by
  // .active, :disabled, or anything added later.
  for (const rule of chipRules.slice(ringIndex + 1)) {
    assert.doesNotMatch(
      rule.body,
      /outline/,
      `"${rule.selector}" must not touch outline — it would erase the focus ring`,
    );
  }
  for (const selector of [
    '.map-stack-chip.active',
    '.map-stack-chip.unavailable',
  ]) {
    assert.ok(
      chipRules.some((rule) => rule.selector.includes(selector)),
      `expected a ${selector} rule to exist for this check to mean anything`,
    );
  }

  // `transition: all` animates outline-width off the `outline: none` base, and
  // Chrome parks that transition at 0px for chips on a wrapped line — the ring
  // never appeared on rows 2 and 3. The base rule must list its properties.
  const base = chipRules.find((rule) =>
    rule.selector.endsWith('.map-stack-chip'),
  );
  assert.ok(base, 'expected the base .map-stack-chip rule');
  assert.doesNotMatch(
    base.body,
    /transition:\s*all\b/,
    'transition: all animates outline-width and kills the focus ring on wrapped rows',
  );
  assert.doesNotMatch(
    base.body,
    /transition:[^;]*outline/,
    'the focus ring must not be animated',
  );
  assert.match(
    base.body,
    /transition:\s*\n?\s*color/,
    'the hover/active treatment still animates',
  );
});

test('the Visual Presets tray owns Map Source and the retired left panel is absent', () => {
  const html = expandApplicationHtml(
    readFileSync(new URL('../index.html', import.meta.url), 'utf8'),
  );
  const ui = readShellSource();

  assert.doesNotMatch(
    html,
    /map-stack-select/,
    'the SOURCE dropdown is replaced by the chip row',
  );
  assert.match(
    html,
    /<section class="map-source-section"[\s\S]*?<div id="map-stack-chips" class="map-stack-chip-row" role="group" aria-label="Map source"><\/div>/,
  );
  assert.doesNotMatch(
    html,
    /id="stack-panel"/,
    'the duplicate left MAP STACK panel is retired',
  );
  assert.match(
    html,
    /id="map-source-label">MAP SOURCE<[\s\S]*?id="map-stack-status"/,
  );
  assert.match(
    html,
    /<button id="control-panel-toggle"[\s\S]*?data-dock-toggle-target="control-panel"[\s\S]*?aria-controls="control-panel-popover"/,
    'the compact wing must expose a semantic keyboard disclosure',
  );
  const panels = readFileSync(
    new URL('./ui/panelDisclosure.js', import.meta.url),
    'utf8',
  );
  assert.match(panels, /event\.key !== 'Escape'[\s\S]*?disclosure\?\.focus/);
  assert.match(
    ui,
    /querySelector\(\s*'\.map-stack-chip\.active',?\s*\)\s*\|\|\s*panel\.querySelector\('\.map-stack-chip'\)/,
  );

  const controls = readFileSync(
    new URL('./ui/mapSourceControls.js', import.meta.url),
    'utf8',
  );
  assert.match(
    ui,
    /return this\._mapSourceControls\.select\(stackId, \{ syncShare \}\)/,
    'the application action uses the component selection path',
  );
  assert.match(
    controls,
    /onSelect: [\s\S]*?select\(id\)/,
    'chip clicks use the same component selection path',
  );
  assert.match(
    controls,
    /await controller\.setStack\(stackId\)/,
    'selection still delegates source loading to the map controller',
  );
  assert.match(
    controls,
    /render\(controller\.getState\(\)\)/,
    'the active chip is re-synced from actual controller state',
  );
  assert.match(
    ui,
    /window\.addEventListener\('gev:map-stack-changed', onChange\)/,
    'provider-driven fallback reaches the component without a user click',
  );
  assert.match(
    ui,
    /window\.removeEventListener\('gev:map-stack-changed', onChange\)/,
    'the provider-driven subscription has an explicit remover',
  );
  assert.match(
    controls,
    /unsubscribe\?\.\(\)/,
    'component destruction releases its subscription',
  );
});

test('the row renders the two keyless sources, lit from the active id', () => {
  const container = makeElement();
  renderMapStackChips(container, CONTROLLER_STACKS, { activeId: 'osm', doc });
  assert.deepEqual(
    container.children.map((chip) => chip.dataset.stackId),
    ['esri-imagery', 'osm'],
  );
  assert.deepEqual(
    container.children.map((chip) => chip.attributes['aria-pressed']),
    ['false', 'true'],
  );
});

test('clicking a chip dispatches that stack id', () => {
  const container = makeElement();
  const picked = [];
  renderMapStackChips(container, CONTROLLER_STACKS, {
    activeId: 'esri-imagery',
    onSelect: (id) => picked.push(id),
    doc,
  });
  container.children[1].click();
  assert.deepEqual(picked, ['osm']);
});

test('an unavailable stack says why and does not dispatch', () => {
  const container = makeElement();
  const picked = [];
  renderMapStackChips(
    container,
    [
      {
        id: 'osm',
        label: 'OSM',
        available: false,
        unavailableReason: 'tile server refused',
      },
    ],
    { onSelect: (id) => picked.push(id), doc },
  );
  const [chip] = container.children;
  assert.equal(chip.attributes['aria-disabled'], 'true');
  assert.match(chip.attributes['aria-label'], /tile server refused/);
  chip.click();
  assert.deepEqual(picked, []);
});

test('the lit chip follows controller state, not the click', () => {
  const container = makeElement();
  renderMapStackChips(container, CONTROLLER_STACKS, {
    activeId: 'esri-imagery',
    doc,
  });
  syncMapStackChips(container, 'osm');
  assert.deepEqual(
    container.children.map((chip) => chip.attributes['aria-pressed']),
    ['false', 'true'],
  );
});
