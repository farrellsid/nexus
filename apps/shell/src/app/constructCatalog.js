import { createLayerCatalog } from './catalog.js';
import { LAYER_STATE_REGISTRY } from '../data/layerState.js';
import { createApplicationDirections } from './layers/directions.js';
import { createInfrastructureLayers } from '../data/infrastructure.js';
import { localGeoJsonServices } from './localGeojsonServices.js';
import { createBhoteKoshiEventLayer } from '../data/bhoteKoshiEvent.js';
import { createBhoteKoshiLocatorLayer } from '../data/bhoteKoshiLocator.js';

/** Construct the current catalog without choosing any source provider.
 * Layers have this app's lifetime; the manager owns their destruction.
 */
export function createApplicationCatalog({
  surface,
  signal,
  metadata = LAYER_STATE_REGISTRY,
  nepalBoundaryResolver,
}) {
  if (!signal?.addEventListener)
    throw new TypeError('An application lifetime signal is required');
  signal.throwIfAborted();
  if (!surface?.groundFloor || !surface?.terrain)
    throw new TypeError('Application surface services are required');

  const catalog = createLayerCatalog(
    [
      createBhoteKoshiEventLayer(),
      createBhoteKoshiLocatorLayer({
        boundaryResolver: nepalBoundaryResolver,
      }),
      createApplicationDirections(),
      ...createInfrastructureLayers(localGeoJsonServices),
    ],
    metadata,
  );
  return Object.freeze({ ...catalog, surface });
}
