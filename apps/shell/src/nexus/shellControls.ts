// The controls the action layer drives, and global-context mode.
//
// `createShellControls` is the only place that decides what each verb does to the shell. It works
// through `ShellPorts`, a narrow description of the camera, layers and tour, so the logic (above all,
// how global context is entered and left) is tested without a globe. `createCesiumShellPorts` in
// shellPorts.ts connects the ports to the real viewer.
import type { ShellControls } from './actions.ts';

export interface CameraPose {
  readonly longitude: number;
  readonly latitude: number;
  readonly heightM: number;
  readonly heading: number;
  readonly pitch: number;
  readonly roll: number;
}

export interface ShellPorts {
  readCameraPose(): CameraPose;
  flyToPose(pose: CameraPose): void;
  /** Pull out to the whole globe, keeping the point under the camera centred. */
  flyToGlobe(): void;
  flyToOpeningView(): void;
  flyToPlace(destinationId: string, placeIndex: number): boolean;
  isLayerVisible(layerId: string): boolean;
  setLayerVisible(layerId: string, visible: boolean): Promise<void>;
  playTour(): Promise<boolean>;
  stopTour(): void;
}

interface GlobalContextSnapshot {
  readonly camera: CameraPose;
  readonly layers: ReadonlyMap<string, boolean>;
}

/**
 * @param globalContextLayerIds the layers global context turns on; their previous state is restored on exit.
 */
export function createShellControls(
  ports: ShellPorts,
  globalContextLayerIds: readonly string[],
): ShellControls {
  let snapshot: GlobalContextSnapshot | null = null;

  return {
    flyToPlace: (destinationId, placeIndex) =>
      ports.flyToPlace(destinationId, placeIndex),
    setLayerVisible: (layerId, visible) =>
      ports.setLayerVisible(layerId, visible),
    playTour: () => ports.playTour(),
    stopTour: () => ports.stopTour(),
    resetView: () => ports.flyToOpeningView(),

    async enterGlobalContext() {
      // Entering twice must not overwrite the view to return to with the globe view itself.
      if (snapshot) return;
      snapshot = {
        camera: ports.readCameraPose(),
        layers: new Map(
          globalContextLayerIds.map((id) => [id, ports.isLayerVisible(id)]),
        ),
      };
      ports.flyToGlobe();
      for (const id of globalContextLayerIds)
        await ports.setLayerVisible(id, true);
    },

    async exitGlobalContext() {
      if (!snapshot) return;
      const { camera, layers } = snapshot;
      snapshot = null;
      for (const [id, wasVisible] of layers)
        await ports.setLayerVisible(id, wasVisible);
      ports.flyToPose(camera);
    },
  };
}
