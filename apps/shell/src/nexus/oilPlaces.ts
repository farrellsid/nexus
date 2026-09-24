import { OIL_GEOGRAPHY, type OilStop } from './oilStops.ts';

/** One place the camera can fly to, in the shape the location panel and the camera code read. */
export interface PlacePoi {
  readonly name: string;
  readonly lat: number;
  readonly lon: number;
  /** Range from the target in metres, not an absolute altitude. */
  readonly alt: number;
  readonly pitch: number;
  readonly heading: number;
  readonly buildingHeight: number;
}

/** A group of places shown together in the location panel. */
export interface PlaceDestination {
  readonly name: string;
  readonly groundElevation: number;
  readonly viewBounds: {
    readonly southwest: { readonly lat: number; readonly lng: number };
    readonly northeast: { readonly lat: number; readonly lng: number };
  };
  readonly pois: readonly PlacePoi[];
}

/** How the destinations group the oil stops. The grouping is a reading aid, not a claim about the stops. */
const DESTINATION_GROUPS: readonly {
  readonly id: string;
  readonly name: string;
  readonly entityIds: readonly string[];
}[] = [
  {
    id: 'gulf-and-red-sea',
    name: 'Gulf and Red Sea',
    entityIds: ['oil-hormuz', 'oil-yanbu', 'oil-bab'],
  },
  {
    id: 'southeast-asian-straits',
    name: 'Southeast Asian straits',
    entityIds: ['oil-malacca', 'oil-sunda', 'oil-lombok'],
  },
];

const STRAIT_RANGE_M = 450_000;
const FACILITY_RANGE_M = 60_000;
const VIEW_PADDING_DEGREES = 5;

const poiFor = (stop: OilStop): PlacePoi => ({
  name: stop.label,
  lat: stop.latitude,
  lon: stop.longitude,
  alt: stop.precision === 'facility_point' ? FACILITY_RANGE_M : STRAIT_RANGE_M,
  pitch: -55,
  heading: 0,
  buildingHeight: 0,
});

function destinationFor(
  group: (typeof DESTINATION_GROUPS)[number],
  stops: readonly OilStop[],
): PlaceDestination {
  const own = group.entityIds.map((entityId) => {
    const stop = stops.find((candidate) => candidate.entityId === entityId);
    if (!stop)
      throw new Error(
        `Oil place group ${group.id} names ${entityId}, which has no stop`,
      );
    return stop;
  });
  const latitudes = own.map((stop) => stop.latitude);
  const longitudes = own.map((stop) => stop.longitude);
  return {
    name: group.name,
    groundElevation: 0,
    viewBounds: {
      southwest: {
        lat: Math.min(...latitudes) - VIEW_PADDING_DEGREES,
        lng: Math.min(...longitudes) - VIEW_PADDING_DEGREES,
      },
      northeast: {
        lat: Math.max(...latitudes) + VIEW_PADDING_DEGREES,
        lng: Math.max(...longitudes) + VIEW_PADDING_DEGREES,
      },
    },
    pois: own.map(poiFor),
  };
}

/** The camera destinations, one per group, built from the sourced stops so they cannot drift from the layer. */
export const OIL_PLACE_PRESETS: Readonly<Record<string, PlaceDestination>> =
  Object.fromEntries(
    DESTINATION_GROUPS.map((group) => [
      group.id,
      destinationFor(group, OIL_GEOGRAPHY.stops),
    ]),
  );

/**
 * Where the shell opens: the Indian Ocean, from far enough out that the Gulf and the three Asian
 * straits are in view together. The globe is the introduction; the tour supplies the detail.
 */
export const OIL_OVERVIEW = Object.freeze({
  longitude: 78,
  latitude: 12,
  heightM: 12_000_000,
});
