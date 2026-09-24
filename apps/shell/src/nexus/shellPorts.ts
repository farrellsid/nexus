// Connects the action layer's ports to the real viewer, layer manager and scene director.
//
// The shell's modules are JavaScript, so the pieces this file needs from them (the two camera
// flights and the scene id) are handed in rather than imported; that keeps this file type-checked
// end to end and free of any reach into the rest of the shell.
import * as Cesium from 'cesium';
import { OIL_OVERVIEW } from './oilPlaces.ts';
import type { CameraPose, ShellPorts } from './shellControls.ts';

export interface DataManagerPort {
  isEnabled(layerId: string): boolean;
  setEnabled(
    layerId: string,
    enabled: boolean,
    options: { origin: string },
  ): Promise<unknown>;
}

export interface SceneDirectorPort {
  readonly running: boolean;
  /** Settles when the whole run ends, or at once with a refusal; so it is not awaited to learn whether it began. */
  startScene(sceneId: string, options: { single: boolean }): Promise<unknown>;
  stopScene(reason?: string): void;
}

export interface ShellPortInputs {
  readonly viewer: Cesium.Viewer;
  readonly dataManager: DataManagerPort;
  readonly sceneDirector: SceneDirectorPort;
  readonly tourSceneId: string;
  /** flyToPOI(viewer, destinationId, placeIndex) from locations.js; null when there is no such place. */
  readonly flyToPlace: (
    viewer: Cesium.Viewer,
    destinationId: string,
    placeIndex: number,
  ) => unknown;
  /** flyToGlobeView(viewer) from locations.js. */
  readonly flyToGlobe: (viewer: Cesium.Viewer) => unknown;
}

/** The origin the layer manager records for changes the action layer makes on someone's behalf. */
const ACTION_ORIGIN = 'tool';

export function createCesiumShellPorts(inputs: ShellPortInputs): ShellPorts {
  const { viewer, dataManager, sceneDirector } = inputs;

  const flyToPose = (pose: CameraPose): void => {
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(
        pose.longitude,
        pose.latitude,
        pose.heightM,
      ),
      orientation: {
        heading: pose.heading,
        pitch: pose.pitch,
        roll: pose.roll,
      },
      duration: 2.5,
    });
  };

  return {
    readCameraPose() {
      const position = viewer.camera.positionCartographic;
      return {
        longitude: Cesium.Math.toDegrees(position.longitude),
        latitude: Cesium.Math.toDegrees(position.latitude),
        heightM: position.height,
        heading: viewer.camera.heading,
        pitch: viewer.camera.pitch,
        roll: viewer.camera.roll,
      };
    },
    flyToPose,
    flyToGlobe: () => void inputs.flyToGlobe(viewer),
    flyToOpeningView: () =>
      flyToPose({ ...OIL_OVERVIEW, heading: 0, pitch: -Math.PI / 2, roll: 0 }),
    flyToPlace: (destinationId, placeIndex) =>
      Boolean(inputs.flyToPlace(viewer, destinationId, placeIndex)),
    isLayerVisible: (layerId) => dataManager.isEnabled(layerId),
    setLayerVisible: async (layerId, visible) => {
      await dataManager.setEnabled(layerId, visible, { origin: ACTION_ORIGIN });
    },
    async playTour() {
      if (sceneDirector.running) return false;
      // The run claims the director synchronously, so `running` says whether it began.
      void sceneDirector.startScene(inputs.tourSceneId, { single: true });
      return sceneDirector.running;
    },
    stopTour: () => sceneDirector.stopScene('Stopped'),
  };
}
