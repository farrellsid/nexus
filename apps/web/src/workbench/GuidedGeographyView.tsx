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
    </div>
  );
}
