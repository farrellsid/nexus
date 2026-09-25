import { StyleManager } from '../ui/composition.js';
import { flyToStartView } from '../camera.js';

/** Construct the existing controls and camera presentation. */
export function createApplicationControls({
  scene: { viewer, mapStackController, operations },
  loaderStatus,
  Controls = StyleManager,
  services,
  catalog,
  placeSearch,
  defer,
}) {
  // Initialize the style manager (post-processing, HUD, locations, share links)
  const styleManager = new Controls(viewer, {
    services: {
      ...services,
      searchAndFlyTo: operations.searchAndFlyTo,
    },
    mapStackController,
    placeSearch,
  });
  defer(() => styleManager.orbitController.stop());
  defer(() => styleManager.hud.destroy());
  defer(() => styleManager.dispose());
  // If no share link state, open on the oil overview
  if (!styleManager.hasShareState) {
    loaderStatus.textContent = 'Opening the oil overview...';
    defer(flyToStartView(viewer));
  } else {
    loaderStatus.textContent = 'Restoring shared view...';
  }

  return { styleManager };
}
