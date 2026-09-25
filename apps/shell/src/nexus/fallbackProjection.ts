// The flat world map behind the 2D fallback: Natural Earth land (public domain, via world-atlas)
// drawn with the Natural Earth projection, with the sourced stops and corridors placed on it.
//
// This file only computes shapes and positions, so it runs and is tested without a browser.
// fallbackMap.ts turns the result into DOM.
import { geoGraticule10, geoNaturalEarth1, geoPath } from 'd3-geo';
import type { FeatureCollection, Geometry } from 'geojson';
import { feature } from 'topojson-client';
import type { GeometryCollection, Topology } from 'topojson-specification';
import landTopology from 'world-atlas/land-110m.json' with { type: 'json' };
import { OIL_GEOGRAPHY, type OilGeography } from './oilStops.ts';

export const MAP_WIDTH = 720;
export const MAP_HEIGHT = 360;
const MAP_MARGIN = 8;

const topology = landTopology as unknown as Topology<{
  land: GeometryCollection;
}>;
const land = feature(
  topology,
  topology.objects.land,
) as unknown as FeatureCollection<Geometry>;

export interface ProjectedStop {
  readonly id: string;
  readonly label: string;
  /** One-based position in the brief's order, shown on the marker. */
  readonly number: number;
  readonly x: number;
  readonly y: number;
}

export interface ProjectedRoute {
  readonly id: string;
  readonly label: string;
  readonly path: string;
}

export interface ProjectedMap {
  readonly width: number;
  readonly height: number;
  readonly landPath: string;
  readonly graticulePath: string;
  readonly stops: readonly ProjectedStop[];
  readonly routes: readonly ProjectedRoute[];
}

export function projectGeography(
  geography: OilGeography = OIL_GEOGRAPHY,
): ProjectedMap {
  const projection = geoNaturalEarth1().fitExtent(
    [
      [MAP_MARGIN, MAP_MARGIN],
      [MAP_WIDTH - MAP_MARGIN, MAP_HEIGHT - MAP_MARGIN],
    ],
    land,
  );
  const path = geoPath(projection);

  const stops: ProjectedStop[] = [];
  geography.stops.forEach((stop, index) => {
    const point = projection([stop.longitude, stop.latitude]);
    if (point)
      stops.push({
        id: stop.id,
        label: stop.label,
        number: index + 1,
        x: point[0],
        y: point[1],
      });
  });

  const routes: ProjectedRoute[] = [];
  for (const route of geography.routes) {
    const line = path({
      type: 'LineString',
      coordinates: route.points.map((point) => [
        point.longitude,
        point.latitude,
      ]),
    });
    if (line) routes.push({ id: route.id, label: route.label, path: line });
  }

  return {
    width: MAP_WIDTH,
    height: MAP_HEIGHT,
    landPath: path(land) ?? '',
    graticulePath: path(geoGraticule10()) ?? '',
    stops,
    routes,
  };
}
