import { useState } from "react";
import type { Investigation } from "../api";
import { CesiumGeographyMap } from "./CesiumGeographyMap";

type Geography = NonNullable<Investigation["geography"]>;

export function GuidedGeographyView({
  geography,
  onExplore,
}: {
  geography: Geography;
  onExplore: (entityId: string) => void;
}) {
  const [selectedId, setSelectedId] = useState(geography.stops[0].id);
  const selected =
    geography.stops.find((stop) => stop.id === selectedId) ??
    geography.stops[0];

  return (
    <div className="view-content geography-view">
      <div className="eyebrow">Sourced geographic anchors</div>
      <h2>{geography.title}</h2>
      <p className="muted">{geography.framing}</p>
      <CesiumGeographyMap
        stops={geography.stops}
        routes={geography.routes}
        selectedId={selected.id}
        onSelect={setSelectedId}
      />
      <div className="geo-stops" aria-label="Guided geography stops">
        {geography.stops.map((stop, index) => (
          <button
            key={stop.id}
            aria-pressed={stop.id === selected.id}
            onClick={() => setSelectedId(stop.id)}
          >
            <span>{index + 1}</span>
            {stop.label}
          </button>
        ))}
      </div>
      <article className="geo-explanation">
        <div>
          <span className="eyebrow">
            {selected.role} · {selected.precision.replaceAll("_", " ")}
          </span>
          <h3>{selected.label}</h3>
          <p>{selected.why_it_matters}</p>
          <p className="caveat">{selected.caveat}</p>
        </div>
        <div className="geo-actions">
          <button onClick={() => onExplore(selected.entity_id)}>
            Explore relationships →
          </button>
          <a href={selected.source_url} target="_blank" rel="noreferrer">
            Coordinate source ↗
          </a>
          <small>{selected.source_title}</small>
        </div>
      </article>
      {geography.routes.length > 0 && (
        <section
          className="geo-routes"
          aria-label="Sourced illustrative corridors"
        >
          <div className="eyebrow">Sourced illustrative corridors</div>
          <p className="muted">
            Lines built from sourced anchor points, not vessel tracks, pipeline
            as-built routes or precise canal centerlines. Each corridor's caveat
            states what it approximates.
          </p>
          {geography.routes.map((route) => (
            <article className="geo-route-card" key={route.id}>
              <div>
                <span className="eyebrow">
                  {route.role} · {route.precision.replaceAll("_", " ")}
                </span>
                <h4>{route.label}</h4>
                <p>{route.why_it_matters}</p>
                <p className="caveat">{route.caveat}</p>
              </div>
              <div className="geo-actions">
                <button onClick={() => onExplore(route.entity_id)}>
                  Explore relationships →
                </button>
                <a href={route.source_url} target="_blank" rel="noreferrer">
                  Coordinate source ↗
                </a>
                <small>{route.source_title}</small>
              </div>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
