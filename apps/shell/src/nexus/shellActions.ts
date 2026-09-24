// Assembles the shell's action layer from the real viewer, layers, places and tour.
import { createActionRegistry, type ActionRegistry } from './actions.ts';
import {
  OIL_CORRIDORS_LAYER_ID,
  OIL_STOPS_LAYER_ID,
} from './oilGeographyLayer.ts';
import { OIL_TOUR_ID } from './oilTour.ts';
import { createShellControls } from './shellControls.ts';
import { createCesiumShellPorts, type ShellPortInputs } from './shellPorts.ts';

export interface ShellActionInputs extends Omit<
  ShellPortInputs,
  'tourSceneId'
> {
  /** Destination id to its places, as the location presets hold them. */
  readonly places: Readonly<
    Record<string, { readonly pois: readonly unknown[] }>
  >;
}

const NEXUS_LAYER_IDS = [OIL_STOPS_LAYER_ID, OIL_CORRIDORS_LAYER_ID];

export function createShellActions(inputs: ShellActionInputs): ActionRegistry {
  const controls = createShellControls(
    createCesiumShellPorts({ ...inputs, tourSceneId: OIL_TOUR_ID }),
    NEXUS_LAYER_IDS,
  );
  const placeCounts = Object.fromEntries(
    Object.entries(inputs.places).map(([id, destination]) => [
      id,
      destination.pois.length,
    ]),
  );
  return createActionRegistry(controls, {
    places: placeCounts,
    layerIds: NEXUS_LAYER_IDS,
  });
}
