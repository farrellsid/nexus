import { MAP_STACKS } from './catalog.js';
import {
  createOsmImagery,
  createEsriImagery,
  ESRI_ATTRIBUTION_HTML,
} from './imagery.js';
import { createKeylessTerrain } from './terrain.js';

/** Select the keyless imagery and terrain sources without putting provider branches in the controller. */
export function createDefaultMapSources() {
  const terrain = { id: 'keyless', create: createKeylessTerrain };
  return {
    defaultId: 'esri-imagery',
    unknownId: 'esri-imagery',
    recoveryId: null,
    state: {},
    sources: MAP_STACKS.map((descriptor) => ({
      descriptor,
      available: true,
      unavailableReason: null,
      imagery: descriptor.id === 'osm' ? createOsmImagery : createEsriImagery,
      terrain,
      ...(descriptor.id === 'esri-imagery'
        ? {
            credit: ESRI_ATTRIBUTION_HTML,
            constructionFallback: {
              id: 'osm',
              message: 'Esri Satellite is unavailable; using OSM',
            },
            tileFailureFallback: {
              id: 'osm',
              threshold: 2,
              message: 'Esri Satellite tile requests failed; using OSM',
            },
          }
        : {}),
    })),
  };
}
