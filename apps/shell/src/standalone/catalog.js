import { createApplicationCatalog } from '../app/constructCatalog.js';

/** Create fresh layer instances for the standalone application. */
export function createStandaloneCatalog({
  nepalBoundaryResolver,
  signal = new AbortController().signal,
} = {}) {
  return createApplicationCatalog({ nepalBoundaryResolver, signal });
}

// Direct compatibility callers share one catalog; application startup supplies its own.
let compatibilityCatalog;
export function getStandaloneCatalog() {
  return (compatibilityCatalog ||= createStandaloneCatalog());
}
