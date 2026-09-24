import { createSurfaceServices } from '../app/surfaceServices.js';
import { createApplicationRequestServices } from '../services/requests.js';
import { createApplicationCatalog } from '../app/constructCatalog.js';

/** Create fresh layer instances for the standalone application. */
export function createStandaloneCatalog({
  nepalBoundaryResolver,
  signal = new AbortController().signal,
  surface = createSurfaceServices({
    terrainSource: createApplicationRequestServices().terrain,
    signal,
  }),
} = {}) {
  return createApplicationCatalog({
    nepalBoundaryResolver,
    surface,
    signal,
  });
}

// Direct compatibility callers share one catalog; application startup supplies its own.
let compatibilityCatalog;
export function getStandaloneCatalog() {
  return (compatibilityCatalog ||= createStandaloneCatalog());
}
