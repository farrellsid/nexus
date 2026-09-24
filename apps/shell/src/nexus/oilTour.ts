// The guided oil tour as a scene recipe: one shot per sourced stop, in the brief's order.
//
// The scene director plays a recipe as a camera path. Each shot places the camera south of a stop
// and looks north at it, so the stop sits in the middle of the frame; the distance follows from the
// altitude and pitch so the same rule frames every stop.
import { OIL_GEOGRAPHY, type OilGeography } from './oilStops.ts';
import {
  OIL_CORRIDORS_LAYER_ID,
  OIL_STOPS_LAYER_ID,
} from './oilGeographyLayer.ts';

export const OIL_TOUR_ID = 'nexus-oil-tour';

const METRES_PER_DEGREE_LATITUDE = 111_320;
const TOUR_ALTITUDE_M = 1_500_000;
const TOUR_PITCH_DEG = -50;

export interface OilTourShot {
  readonly title: string;
  readonly lat: number;
  readonly lon: number;
  readonly alt: number;
  readonly heading: number;
  readonly pitch: number;
  readonly roll: number;
  readonly duration: number;
  readonly hold: number;
}

export interface OilTourRecipe {
  readonly id: string;
  readonly title: string;
  readonly durationSec: number;
  readonly style: string;
  readonly ui: {
    readonly hidePanels: boolean;
    readonly hudMode: string;
    readonly safeFrame: string;
  };
  readonly layers: Readonly<Record<string, boolean>>;
  readonly post: { readonly bloom: number; readonly sharpen: boolean };
  readonly cameraPath: readonly OilTourShot[];
}

/** Degrees of latitude between the camera and the point it looks at, for a given altitude and pitch. */
export function lookAheadDegrees(altitudeM: number, pitchDeg: number): number {
  return (
    altitudeM /
    Math.tan((Math.abs(pitchDeg) * Math.PI) / 180) /
    METRES_PER_DEGREE_LATITUDE
  );
}

export function oilTourRecipe(
  geography: OilGeography = OIL_GEOGRAPHY,
): OilTourRecipe {
  const offset = lookAheadDegrees(TOUR_ALTITUDE_M, TOUR_PITCH_DEG);
  const cameraPath = geography.stops.map((stop): OilTourShot => ({
    title: stop.label,
    lat: stop.latitude - offset,
    lon: stop.longitude,
    alt: TOUR_ALTITUDE_M,
    heading: 0,
    pitch: TOUR_PITCH_DEG,
    roll: 0,
    duration: 5,
    hold: 2,
  }));
  return {
    id: OIL_TOUR_ID,
    title: 'Oil chokepoints',
    durationSec: cameraPath.reduce(
      (total, shot) => total + shot.duration + shot.hold,
      0,
    ),
    style: 'normal',
    ui: { hidePanels: false, hudMode: 'full', safeFrame: '16:9' },
    layers: { [OIL_STOPS_LAYER_ID]: true, [OIL_CORRIDORS_LAYER_ID]: true },
    post: { bloom: 0, sharpen: true },
    cameraPath,
  };
}
