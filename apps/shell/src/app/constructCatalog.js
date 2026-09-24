import { createLayerCatalog } from './catalog.js';
import { LAYER_STATE_REGISTRY } from '../data/layerState.js';
import {
  createOilCorridorsLayer,
  createOilStopsLayer,
} from '../nexus/oilGeographyLayer.ts';

/** Construct the current catalog. Layers have this app's lifetime; the manager owns their destruction. */
export function createApplicationCatalog({
  signal,
  metadata = LAYER_STATE_REGISTRY,
}) {
  if (!signal?.addEventListener)
    throw new TypeError('An application lifetime signal is required');
  signal.throwIfAborted();
  return Object.freeze(
    createLayerCatalog(
      [createOilStopsLayer(), createOilCorridorsLayer()],
      metadata,
    ),
  );
}
