import { useEffect, useRef, useState } from "react";
import { geoGraticule10, geoNaturalEarth1, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import landTopology from "world-atlas/land-110m.json";
import type { FeatureCollection, Geometry } from "geojson";
import type { GeometryCollection, Topology } from "topojson-specification";
import {
  ArcGisMapServerImageryProvider,
  Cartesian2,
  Cartesian3,
  Color,
  ConstantProperty,
  EasingFunction,
  Entity,
  HorizontalOrigin,
  ImageryLayer,
  LabelStyle,
  Math as CesiumMath,
  OpenStreetMapImageryProvider,
  PolylineDashMaterialProperty,
  ScreenSpaceEventType,
  VerticalOrigin,
  Viewer,
} from "cesium";
import type { Investigation } from "../api";

type Geography = NonNullable<Investigation["geography"]>;
type GeoStop = Geography["stops"][number];
type GeoRoute = Geography["routes"][number];

const ESRI_WORLD_IMAGERY =
  "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer";
const OSM_TILES = "https://tile.openstreetmap.org/";
const MARKER_PREFIX = "nexus-geography:";
const ROUTE_PREFIX = "nexus-geography-route:";
const ROUTE_COLOR = "#5c7fa6";

type MapStatus = "loading" | "satellite" | "streets" | "globe-only" | "local";
type MapRenderer = "cesium" | "svg";

const LOCAL_MAP_WIDTH = 720;
const LOCAL_MAP_HEIGHT = 360;
const topology = landTopology as unknown as Topology<{
  land: GeometryCollection;
}>;
const land = feature(
  topology,
  topology.objects.land,
) as unknown as FeatureCollection<Geometry>;

function hasUsableWebGl() {
  try {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("webgl2") ?? canvas.getContext("webgl");
    return Boolean(
      context && context.getParameter(context.MAX_TEXTURE_SIZE) > 0,
    );
  } catch {
    return false;
  }
}

function stopEntityId(stop: GeoStop) {
  return `${MARKER_PREFIX}${stop.id}`;
}

function routeEntityId(route: GeoRoute) {
  return `${ROUTE_PREFIX}${route.id}`;
}

function markerColor(selected: boolean) {
  return Color.fromCssColorString(selected ? "#c17b3d" : "#557a58");
}

function NaturalEarthMap({
  stops,
  routes,
  selectedId,
  onSelect,
}: {
  stops: GeoStop[];
  routes: GeoRoute[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const projection = geoNaturalEarth1().fitExtent(
    [
      [8, 8],
      [LOCAL_MAP_WIDTH - 8, LOCAL_MAP_HEIGHT - 8],
    ],
    land,
  );
  const path = geoPath(projection);
  return (
    <svg
      className="geo-map geo-map-fallback"
      viewBox={`0 0 ${LOCAL_MAP_WIDTH} ${LOCAL_MAP_HEIGHT}`}
      role="img"
      aria-label={`Interactive Natural Earth world map with ${stops.length} sourced oil geography anchors and ${routes.length} sourced illustrative corridors`}
    >
      <rect className="geo-local-ocean" width="100%" height="100%" rx="8" />
      <path className="geo-local-graticule" d={path(geoGraticule10()) ?? ""} />
      <path className="geo-local-land" d={path(land) ?? ""} />
      {routes.map((route) => {
        const line = path({
          type: "LineString",
          coordinates: route.points.map((point) => [
            point.longitude,
            point.latitude,
          ]),
        });
        if (!line) return null;
        return (
          <path
            className="geo-local-route"
            key={route.id}
            d={line}
            aria-label={`${route.label} (illustrative sourced corridor)`}
          >
            <title>{route.label}</title>
          </path>
        );
      })}
      {stops.map((stop, index) => {
        const point = projection([stop.longitude, stop.latitude]);
        if (!point) return null;
        const selected = stop.id === selectedId;
        return (
          <g
            className={selected ? "geo-local-stop active" : "geo-local-stop"}
            key={stop.id}
            role="button"
            tabIndex={0}
            aria-label={`${index + 1}. ${stop.label}`}
            onClick={() => onSelect(stop.id)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") onSelect(stop.id);
            }}
          >
            <title>{stop.label}</title>
            <circle cx={point[0]} cy={point[1]} r={selected ? 9 : 7} />
            <text className="geo-local-number" x={point[0]} y={point[1] + 3}>
              {index + 1}
            </text>
            {selected && (
              <text
                className="geo-local-label"
                x={point[0] + 12}
                y={point[1] + 4}
              >
                {stop.label}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

/**
 * A deliberately narrow Cesium adapter. Its viewer configuration, keyless
 * Esri/OSM source ladder and explicit credit container are adapted from the
 * MIT-licensed God's Eye View map seam; Nexus owns the records and selection.
 */
export function CesiumGeographyMap({
  stops,
  routes,
  selectedId,
  onSelect,
}: {
  stops: GeoStop[];
  routes: GeoRoute[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const creditRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const selectRef = useRef(onSelect);
  const previousSelection = useRef(selectedId);
  const [renderer, setRenderer] = useState<MapRenderer>(() =>
    hasUsableWebGl() ? "cesium" : "svg",
  );
  const [status, setStatus] = useState<MapStatus>(() =>
    hasUsableWebGl() ? "loading" : "local",
  );

  selectRef.current = onSelect;

  useEffect(() => {
    if (renderer !== "cesium") return;
    const container = containerRef.current;
    const creditContainer = creditRef.current;
    if (!container || !creditContainer) return;

    const viewer = new Viewer(container, {
      timeline: false,
      animation: false,
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      navigationHelpButton: false,
      fullscreenButton: false,
      vrButton: false,
      selectionIndicator: false,
      infoBox: false,
      baseLayer: false,
      creditContainer,
      contextOptions: { webgl: { preserveDrawingBuffer: true } },
    });
    viewerRef.current = viewer;
    viewer.scene.renderError.addEventListener(() => {
      setStatus("local");
      setRenderer("svg");
    });
    viewer.scene.globe.show = false;
    viewer.scene.globe.baseColor = Color.fromCssColorString("#d7dfd1");
    viewer.scene.backgroundColor = Color.fromCssColorString("#dce8e5");
    if (viewer.scene.skyBox) viewer.scene.skyBox.show = false;
    if (viewer.scene.sun) viewer.scene.sun.show = false;
    if (viewer.scene.moon) viewer.scene.moon.show = false;
    viewer.camera.setView({
      destination: Cartesian3.fromDegrees(70, 17, 13_500_000),
      orientation: {
        heading: 0,
        pitch: CesiumMath.toRadians(-90),
        roll: 0,
      },
    });

    for (const stop of stops) {
      const selected = stop.id === selectedId;
      viewer.entities.add({
        id: stopEntityId(stop),
        position: Cartesian3.fromDegrees(stop.longitude, stop.latitude, 1500),
        point: {
          pixelSize: selected ? 15 : 11,
          color: markerColor(selected),
          outlineColor: Color.fromCssColorString("#f7f5ed"),
          outlineWidth: selected ? 4 : 3,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        label: {
          text: stop.label,
          show: selected,
          font: "600 13px system-ui",
          fillColor: Color.fromCssColorString("#26362c"),
          outlineColor: Color.fromCssColorString("#f7f5ed"),
          outlineWidth: 4,
          style: LabelStyle.FILL_AND_OUTLINE,
          horizontalOrigin: HorizontalOrigin.LEFT,
          verticalOrigin: VerticalOrigin.CENTER,
          pixelOffset: new Cartesian2(13, 0),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
      });
    }

    // Routes are dashed, unpicked polylines: visually distinct from the solid
    // point-stop markers above and architecturally separate from the
    // schematic relationship graph (RelationshipGraph.tsx), which never
    // renders on this map.
    for (const route of routes) {
      viewer.entities.add({
        id: routeEntityId(route),
        polyline: {
          positions: Cartesian3.fromDegreesArray(
            route.points.flatMap((point) => [point.longitude, point.latitude]),
          ),
          width: 2.5,
          material: new PolylineDashMaterialProperty({
            color: Color.fromCssColorString(ROUTE_COLOR),
            dashLength: 14,
          }),
          clampToGround: false,
        },
      });
    }

    viewer.screenSpaceEventHandler.setInputAction(
      (movement: { position: Cartesian2 }) => {
        const picked = viewer.scene.pick(movement.position) as
          { id?: Entity } | undefined;
        const entityId = picked?.id?.id;
        if (
          typeof entityId === "string" &&
          entityId.startsWith(MARKER_PREFIX)
        ) {
          selectRef.current(entityId.slice(MARKER_PREFIX.length));
        }
      },
      ScreenSpaceEventType.LEFT_CLICK,
    );

    let disposed = false;
    void ArcGisMapServerImageryProvider.fromUrl(ESRI_WORLD_IMAGERY, {
      credit:
        "Powered by Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community",
      enablePickFeatures: false,
    })
      .then((provider) => {
        if (disposed) return;
        viewer.imageryLayers.add(new ImageryLayer(provider), 0);
        viewer.scene.globe.show = true;
        setStatus("satellite");
        viewer.scene.requestRender();
      })
      .catch(() => {
        if (disposed) return;
        try {
          const provider = new OpenStreetMapImageryProvider({
            url: OSM_TILES,
            credit: "© OpenStreetMap contributors",
          });
          viewer.imageryLayers.add(new ImageryLayer(provider), 0);
          viewer.scene.globe.show = true;
          setStatus("streets");
        } catch {
          viewer.scene.globe.show = true;
          setStatus("globe-only");
        }
        viewer.scene.requestRender();
      });

    return () => {
      disposed = true;
      viewerRef.current = null;
      if (!viewer.isDestroyed()) {
        try {
          viewer.destroy();
        } catch {
          // A lost WebGL context can partly tear down Cesium before React cleanup.
        }
      }
    };
  }, [renderer, stops, routes]);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || viewer.isDestroyed()) return;
    for (const stop of stops) {
      const entity = viewer.entities.getById(stopEntityId(stop));
      const selected = stop.id === selectedId;
      if (entity?.point) {
        entity.point.color = new ConstantProperty(markerColor(selected));
        entity.point.pixelSize = new ConstantProperty(selected ? 15 : 11);
        entity.point.outlineWidth = new ConstantProperty(selected ? 4 : 3);
      }
      if (entity?.label) {
        entity.label.show = new ConstantProperty(selected);
      }
    }
    const stop = stops.find((candidate) => candidate.id === selectedId);
    if (stop && previousSelection.current !== selectedId) {
      viewer.camera.flyTo({
        destination: Cartesian3.fromDegrees(
          stop.longitude,
          stop.latitude,
          3_700_000,
        ),
        orientation: {
          heading: 0,
          pitch: CesiumMath.toRadians(-90),
          roll: 0,
        },
        duration: 1.1,
        easingFunction: EasingFunction.CUBIC_IN_OUT,
      });
    }
    previousSelection.current = selectedId;
    viewer.scene.requestRender();
  }, [selectedId, stops]);

  const statusText = {
    loading: "Loading satellite basemap…",
    satellite: "Esri satellite globe",
    streets: "OpenStreetMap globe fallback",
    "globe-only": "Offline globe fallback",
    local: "Natural Earth local map",
  }[status];

  return (
    <div className="geo-map-wrap">
      <div
        className={renderer === "cesium" ? "geo-map" : "geo-map geo-map-hidden"}
        ref={containerRef}
        role="img"
        aria-hidden={renderer !== "cesium"}
        aria-label={`Interactive world globe with ${stops.length} sourced oil geography anchors and ${routes.length} sourced illustrative corridors`}
      />
      {renderer === "svg" && (
        <NaturalEarthMap
          stops={stops}
          routes={routes}
          selectedId={selectedId}
          onSelect={onSelect}
        />
      )}
      <div className="geo-map-meta">
        <p className="graph-caption">
          Interactive world globe · {stops.length} sourced anchors ·{" "}
          {routes.length} sourced illustrative corridors
        </p>
        <span className={`geo-map-status ${status}`}>{statusText}</span>
      </div>
      {routes.length > 0 && (
        <div className="geo-map-legend" aria-hidden="true">
          <span className="geo-map-legend-item">
            <i className="geo-map-legend-swatch geo-map-legend-point" />
            Sourced anchor point
          </span>
          <span className="geo-map-legend-item">
            <i className="geo-map-legend-swatch geo-map-legend-route" />
            Sourced illustrative corridor — not a vessel track or as-built route
          </span>
        </div>
      )}
      <div
        className="geo-map-credits"
        ref={creditRef}
        hidden={renderer !== "cesium"}
      />
      {renderer === "svg" && (
        <div className="geo-map-credits">Natural Earth · public domain</div>
      )}
    </div>
  );
}
