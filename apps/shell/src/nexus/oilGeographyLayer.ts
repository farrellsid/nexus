// The guided oil geography as two data layers: sourced label anchors and illustrative corridor lines.
//
// They draw only what geography.json sources: six anchor points and two lines built from anchor
// coordinates. The anchors are not boundaries and the lines are not vessel tracks or pipeline
// routes; each record's caveat says exactly what it approximates, and the layer carries that text
// on the entity so a selection card can show it.
import * as Cesium from 'cesium';
import {
  OIL_GEOGRAPHY,
  type OilGeography,
  type OilRoute,
  type OilStop,
} from './oilStops.ts';

export const OIL_STOPS_LAYER_ID = 'nexus-oil-stops';
export const OIL_CORRIDORS_LAYER_ID = 'nexus-oil-corridors';

/** What the layer manager calls on a layer. Kept to the members this layer implements. */
export interface DataLayerModule {
  readonly id: string;
  readonly name: string;
  readonly icon: string;
  readonly source: string;
  init(viewer: Cesium.Viewer): Promise<boolean>;
  enable(viewer: Cesium.Viewer): Promise<boolean>;
  disable(viewer: Cesium.Viewer): Promise<boolean>;
  update(viewer: Cesium.Viewer): Promise<boolean>;
  destroy(viewer?: Cesium.Viewer): Promise<boolean>;
  getStats(): {
    count: number;
    lastUpdate: number | null;
    error: string | null;
    source: string;
  };
}

const STOP_COLOR = '#f2c14e';
const ROUTE_COLOR = '#4ec9e0';

/** The text a selection card shows for a record: what it says, how precise it is, and its limit. */
export function describeRecord(record: OilStop | OilRoute): string {
  return [
    `${record.role} · ${record.precision.replaceAll('_', ' ')}`,
    record.whyItMatters,
    `Caveat: ${record.caveat}`,
    `Source: ${record.sourceTitle} (${record.sourceUrl}), checked ${record.checkedOn}`,
  ].join('\n\n');
}

function stopEntity(stop: OilStop): Cesium.Entity.ConstructorOptions {
  return {
    id: `${OIL_STOPS_LAYER_ID}:${stop.id}`,
    name: stop.label,
    description: describeRecord(stop),
    position: Cesium.Cartesian3.fromDegrees(stop.longitude, stop.latitude),
    point: {
      pixelSize: 9,
      color: Cesium.Color.fromCssColorString(STOP_COLOR),
      outlineColor: Cesium.Color.BLACK.withAlpha(0.85),
      outlineWidth: 1.5,
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    },
    label: {
      text: stop.label,
      font: '600 13px "JetBrains Mono", monospace',
      fillColor: Cesium.Color.WHITE,
      outlineColor: Cesium.Color.BLACK,
      outlineWidth: 3,
      style: Cesium.LabelStyle.FILL_AND_OUTLINE,
      horizontalOrigin: Cesium.HorizontalOrigin.LEFT,
      verticalOrigin: Cesium.VerticalOrigin.CENTER,
      pixelOffset: new Cesium.Cartesian2(12, -2),
      disableDepthTestDistance: Number.POSITIVE_INFINITY,
    },
  };
}

function routeEntity(route: OilRoute): Cesium.Entity.ConstructorOptions {
  return {
    id: `${OIL_CORRIDORS_LAYER_ID}:${route.id}`,
    name: route.label,
    description: describeRecord(route),
    polyline: {
      positions: route.points.map((point) =>
        Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude),
      ),
      width: 2.5,
      material: new Cesium.PolylineDashMaterialProperty({
        color: Cesium.Color.fromCssColorString(ROUTE_COLOR),
        dashLength: 14,
      }),
      arcType: Cesium.ArcType.GEODESIC,
    },
  };
}

interface LayerSpec {
  readonly id: string;
  readonly name: string;
  readonly icon: string;
  readonly entities: () => Cesium.Entity.ConstructorOptions[];
}

/** Build a layer that draws nothing until enabled and removes everything when disabled. */
function createEntityLayer(spec: LayerSpec): DataLayerModule {
  let source: Cesium.CustomDataSource | null = null;
  let lastUpdate: number | null = null;
  let count = 0;

  const remove = (viewer: Cesium.Viewer | undefined): void => {
    if (source && viewer && !viewer.isDestroyed())
      viewer.dataSources.remove(source, true);
    source = null;
  };

  return {
    id: spec.id,
    name: spec.name,
    icon: spec.icon,
    source: 'Nexus evidence pack',
    async init() {
      return true;
    },
    async enable(viewer) {
      if (source) return true;
      const dataSource = new Cesium.CustomDataSource(spec.id);
      const entities = spec.entities();
      for (const entity of entities) dataSource.entities.add(entity);
      await viewer.dataSources.add(dataSource);
      source = dataSource;
      count = entities.length;
      lastUpdate = Date.now();
      viewer.scene.requestRender();
      return true;
    },
    async disable(viewer) {
      remove(viewer);
      count = 0;
      viewer.scene.requestRender();
      return true;
    },
    async update() {
      return true;
    },
    async destroy(viewer) {
      remove(viewer);
      count = 0;
      return true;
    },
    getStats() {
      return { count, lastUpdate, error: null, source: 'sourced anchors' };
    },
  };
}

/** The six sourced anchor points, drawn only while the layer is enabled. */
export function createOilStopsLayer(
  geography: OilGeography = OIL_GEOGRAPHY,
): DataLayerModule {
  return createEntityLayer({
    id: OIL_STOPS_LAYER_ID,
    name: 'Oil chokepoints',
    icon: '◈',
    entities: () => geography.stops.map(stopEntity),
  });
}

/** The sourced illustrative corridor lines, drawn only while the layer is enabled. */
export function createOilCorridorsLayer(
  geography: OilGeography = OIL_GEOGRAPHY,
): DataLayerModule {
  return createEntityLayer({
    id: OIL_CORRIDORS_LAYER_ID,
    name: 'Oil corridors',
    icon: '═',
    entities: () => geography.routes.map(routeEntity),
  });
}
