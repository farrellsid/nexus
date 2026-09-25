// The 2D fallback: when there is no usable WebGL, or the globe fails to start, the sourced oil
// geography is shown on a flat Natural Earth map. It carries the same records, the same caveats and
// the same readouts as the globe; only the picture differs.
import {
  OIL_GEOGRAPHY,
  type OilGeography,
  type OilRoute,
  type OilStop,
} from './oilStops.ts';
import { projectGeography } from './fallbackProjection.ts';
import { packReadoutLines, selectionReadout } from './readouts.ts';

const SVG_NS = 'http://www.w3.org/2000/svg';

/** True when a WebGL context can be created. A missing or blocked context is the common failure. */
export function hasUsableWebGl(
  doc: Pick<Document, 'createElement'> = document,
): boolean {
  try {
    const canvas = doc.createElement('canvas');
    const context = canvas.getContext('webgl2') ?? canvas.getContext('webgl');
    return Boolean(
      context && context.getParameter(context.MAX_TEXTURE_SIZE) > 0,
    );
  } catch {
    return false;
  }
}

/** `?view=2d` asks for the fallback, so it can be checked without disabling WebGL. */
export function wantsFallback(search: string): boolean {
  return new URLSearchParams(search).get('view') === '2d';
}

export interface FallbackMapHandle {
  select(recordId: string | null): void;
  destroy(): void;
}

function element<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function svgElement<K extends keyof SVGElementTagNameMap>(
  tag: K,
  attributes: Record<string, string | number> = {},
): SVGElementTagNameMap[K] {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [name, value] of Object.entries(attributes))
    node.setAttribute(name, String(value));
  return node;
}

/** The entity id the globe uses for a record, so both views feed the same precision readout. */
const stopEntityId = (stop: OilStop): string => `nexus-oil-stops:${stop.id}`;
const routeEntityId = (route: OilRoute): string =>
  `nexus-oil-corridors:${route.id}`;

function fillCard(card: HTMLElement, record: OilStop | OilRoute | null): void {
  card.replaceChildren();
  if (!record) {
    card.append(
      element(
        'p',
        'nexus-fallback-hint',
        'Select a numbered place or a corridor to read its source and caveat.',
      ),
    );
    return;
  }
  const source = element('a', undefined, record.sourceTitle);
  source.href = record.sourceUrl;
  source.rel = 'noopener noreferrer';
  source.target = '_blank';
  card.append(
    element('h2', undefined, record.label),
    element(
      'p',
      'nexus-fallback-role',
      `${record.role} · ${record.precision.replaceAll('_', ' ')}`,
    ),
    element('p', undefined, record.whyItMatters),
    element('p', 'nexus-fallback-caveat', `Caveat: ${record.caveat}`),
    element('p', 'nexus-fallback-source'),
  );
  card.lastElementChild?.append(
    'Source: ',
    source,
    ` · checked ${record.checkedOn}`,
  );
}

/**
 * Mount the fallback into `container`. Every string shown comes from the generated records and is
 * set as text, never as markup.
 */
export function mountFallbackMap(
  container: HTMLElement,
  options: { reason: string; geography?: OilGeography },
): FallbackMapHandle {
  const geography = options.geography ?? OIL_GEOGRAPHY;
  const projected = projectGeography(geography);
  const records = new Map<
    string,
    { record: OilStop | OilRoute; entityId: string }
  >([
    ...geography.stops.map(
      (stop): [string, { record: OilStop | OilRoute; entityId: string }] => [
        stop.id,
        { record: stop, entityId: stopEntityId(stop) },
      ],
    ),
    ...geography.routes.map(
      (route): [string, { record: OilStop | OilRoute; entityId: string }] => [
        route.id,
        { record: route, entityId: routeEntityId(route) },
      ],
    ),
  ]);

  const root = element('main', 'nexus-fallback');
  root.id = 'nexus-fallback';
  const notice = element(
    'p',
    'nexus-fallback-notice',
    `The 3D globe is not available here (${options.reason}). Showing the sourced places on a flat map.`,
  );
  notice.setAttribute('role', 'status');

  const svg = svgElement('svg', {
    viewBox: `0 0 ${projected.width} ${projected.height}`,
    role: 'group',
    'aria-label': `World map with ${projected.stops.length} sourced oil geography anchors and ${projected.routes.length} sourced illustrative corridors`,
  });
  svg.classList.add('nexus-fallback-map');
  svg.append(
    svgElement('rect', {
      class: 'nexus-fallback-ocean',
      width: '100%',
      height: '100%',
      rx: 8,
    }),
    svgElement('path', {
      class: 'nexus-fallback-graticule',
      d: projected.graticulePath,
    }),
    svgElement('path', { class: 'nexus-fallback-land', d: projected.landPath }),
  );

  const card = element('section', 'nexus-fallback-card');
  card.setAttribute('aria-live', 'polite');
  const selection = element('p', 'nexus-fallback-selection');
  const readouts = element('div', 'nexus-fallback-readouts');
  readouts.append(
    ...packReadoutLines().map((line) => element('div', undefined, line)),
    selection,
  );

  const marks = new Map<string, SVGElement>();
  let selectedId: string | null = null;

  const select = (recordId: string | null): void => {
    selectedId = recordId !== null && records.has(recordId) ? recordId : null;
    for (const [id, mark] of marks) {
      const active = id === selectedId;
      mark.classList.toggle('active', active);
      mark.setAttribute('aria-pressed', String(active));
    }
    const entry = selectedId === null ? undefined : records.get(selectedId);
    fillCard(card, entry?.record ?? null);
    selection.textContent = selectionReadout(entry?.entityId);
  };

  const makeSelectable = (
    mark: SVGElement,
    id: string,
    label: string,
  ): void => {
    mark.setAttribute('role', 'button');
    mark.setAttribute('tabindex', '0');
    mark.setAttribute('aria-pressed', 'false');
    mark.setAttribute('aria-label', label);
    mark.addEventListener('click', () => select(id === selectedId ? null : id));
    mark.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        select(id === selectedId ? null : id);
      }
    });
    marks.set(id, mark);
  };

  for (const route of projected.routes) {
    const line = svgElement('path', {
      class: 'nexus-fallback-route',
      d: route.path,
    });
    const title = svgElement('title');
    title.textContent = `${route.label} (illustrative sourced corridor)`;
    line.append(title);
    makeSelectable(line, route.id, `${route.label}, illustrative corridor`);
    svg.append(line);
  }
  for (const stop of projected.stops) {
    const group = svgElement('g', { class: 'nexus-fallback-stop' });
    const number = svgElement('text', {
      class: 'nexus-fallback-number',
      x: stop.x,
      y: stop.y + 3,
    });
    number.textContent = String(stop.number);
    group.append(
      svgElement('circle', { cx: stop.x, cy: stop.y, r: 8 }),
      number,
    );
    makeSelectable(group, stop.id, `${stop.number}. ${stop.label}`);
    svg.append(group);
  }

  const credit = element(
    'p',
    'nexus-fallback-credit',
    'Natural Earth · public domain',
  );
  root.append(
    element('h1', undefined, 'NEXUS'),
    notice,
    svg,
    readouts,
    card,
    credit,
  );
  container.append(root);
  select(null);

  return {
    select,
    destroy: () => root.remove(),
  };
}
