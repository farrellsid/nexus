import type { Neighborhood } from "../api";

export function RelationshipGraph({
  graph,
  selectedEntity,
  selectedClaim,
  onEntity,
  onClaim,
}: {
  graph: Neighborhood;
  selectedEntity: string;
  selectedClaim: string;
  onEntity: (id: string) => void;
  onClaim: (id: string) => void;
}) {
  const center = graph.entities.find((entity) => entity.id === selectedEntity)!;
  const neighbors = graph.entities.filter(
    (entity) => entity.id !== selectedEntity,
  );
  const positions = new Map<string, { x: number; y: number }>();
  positions.set(center.id, { x: 360, y: 220 });
  neighbors.forEach((entity, index) => {
    const angle = (index / neighbors.length) * Math.PI * 2 - Math.PI / 2;
    positions.set(entity.id, {
      x: 360 + 260 * Math.cos(angle),
      y: 220 + 155 * Math.sin(angle),
    });
  });
  return (
    <div className="graph-wrap">
      <svg
        viewBox="0 0 720 440"
        role="img"
        aria-label={`Relationship overview for ${center.name}. Use the entity and relationship buttons below to explore.`}
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="29"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
          </marker>
        </defs>
        {graph.claims.map((claim) => {
          const from = positions.get(claim.subject)!;
          const to = positions.get(claim.object)!;
          return (
            <g
              key={claim.id}
              className={claim.id === selectedClaim ? "edge active" : "edge"}
            >
              <line
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                markerEnd="url(#arrow)"
              />
              <text x={(from.x + to.x) / 2} y={(from.y + to.y) / 2 - 8}>
                {claim.id}
              </text>
            </g>
          );
        })}
        {graph.entities.map((entity) => {
          const point = positions.get(entity.id)!;
          return (
            <g
              key={entity.id}
              className={
                entity.id === selectedEntity ? "node selected" : "node"
              }
            >
              <circle
                cx={point.x}
                cy={point.y}
                r={entity.id === selectedEntity ? 24 : 14}
              />
              <text x={point.x} y={point.y + 38} textAnchor="middle">
                {entity.name.length > 30
                  ? `${entity.name.slice(0, 27)}…`
                  : entity.name}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="graph-caption">
        Directional assertions · positions are schematic, not geographic
      </div>
      <div className="entity-chips" aria-label="Explore connected entities">
        {graph.entities.map((entity) => (
          <button
            key={entity.id}
            aria-pressed={entity.id === selectedEntity}
            onClick={() => onEntity(entity.id)}
          >
            {entity.name}
          </button>
        ))}
      </div>
      <div className="relationships" aria-label="Relationships">
        {graph.claims.map((claim) => (
          <button
            key={claim.id}
            className={
              selectedClaim === claim.id
                ? "relationship selected"
                : "relationship"
            }
            onClick={() => onClaim(claim.id)}
          >
            <span className="claim-id">{claim.id}</span>
            <span>
              <strong>{claim.statement}</strong>
              <small>
                {claim.review_status === "accepted"
                  ? "accepted · "
                  : claim.review_status === "rejected"
                    ? "rejected · "
                    : "candidate · "}
                {claim.kind.replaceAll("_", " ")} ·{" "}
                {claim.source_as_of ?? "undated"}
              </small>
            </span>
            <span>↗</span>
          </button>
        ))}
        {graph.claims.length === 0 && (
          <p>
            No relationships recorded for this entity. That does not establish
            that none exist.
          </p>
        )}
      </div>
    </div>
  );
}
