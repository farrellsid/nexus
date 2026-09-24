import { createLayerCatalog } from './catalog.js';
import { LAYER_STATE_REGISTRY } from '../data/layerState.js';
import { createInfrastructureLayers } from '../data/infrastructure.js';
import { localGeoJsonServices } from './localGeojsonServices.js';
import { createBhoteKoshiEventLayer } from '../data/bhoteKoshiEvent.js';
import { createBhoteKoshiLocatorLayer } from '../data/bhoteKoshiLocator.js';

/** Construct the current catalog without choosing any source provider.
 * Layers have this app's lifetime; the manager owns their destruction.
 */
export function createApplicationCatalog({
  signal,
  metadata = LAYER_STATE_REGISTRY,
  nepalBoundaryResolver,
}) {
  if (!signal?.addEventListener)
    throw new TypeError('An application lifetime signal is required');
  signal.throwIfAborted();

  const catalog = createLayerCatalog(
    [
      createBhoteKoshiEventLayer(),
      createBhoteKoshiLocatorLayer({
        boundaryResolver: nepalBoundaryResolver,
      }),
      ...createInfrastructureLayers(localGeoJsonServices),
    ],
    metadata,
  );
  return Object.freeze(catalog);
}
