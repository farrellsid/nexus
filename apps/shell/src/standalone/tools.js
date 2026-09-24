import { createAssetDirectorySource } from '../director/packs/source.js';
import { createApplicationTools } from '../app/tools.js';
import { startApplicationChrome } from '../app/startupChrome.js';
export function createStandaloneTools(options) {
  return createApplicationTools({
    startChrome: startApplicationChrome,
    sceneDataPacks: {
      sources: {
        assets: createAssetDirectorySource({
          baseUrl: new URL('/scene-assets/', window.location.href).href,
        }),
      },
    },
    ...options,
  });
}
