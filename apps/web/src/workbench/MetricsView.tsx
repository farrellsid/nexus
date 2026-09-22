import type { Investigation, Source } from "../api";

type Briefing = NonNullable<Investigation["pack"]["briefing"]>;

export function MetricsView({
  briefing,
  sources,
}: {
  briefing: Briefing;
  sources: Source[];
}) {
  return (
    <div className="view-content metrics-view">
      <div className="eyebrow">Observed measures and labelled outlooks</div>
      <h2>What changed across the system?</h2>
      <p className="muted">
        Values retain the source&apos;s reported, estimated, or forecast status.
        Compare direction carefully: several cards use different definitions and
        periods.
      </p>
      <div className="metric-grid">
        {briefing.metrics.map((metric) => {
          const maximum = Math.max(
            ...metric.points.map((point) => point.value),
          );
          return (
            <article className="metric-card" key={metric.id}>
              <div className="metric-heading">
                <span className="claim-id">{metric.id}</span>
                <h3>{metric.title}</h3>
                <p>{metric.description}</p>
              </div>
              <div
                className="metric-bars"
                role="img"
                aria-label={`${metric.title}, ${metric.unit}`}
              >
                {metric.points.map((point) => (
                  <div className="metric-point" key={point.period}>
                    <span className="metric-value">{point.value}</span>
                    <div className="bar-track" aria-hidden="true">
                      <span
                        className={`bar-fill ${point.status}`}
                        style={{ width: `${(point.value / maximum) * 100}%` }}
                      />
                    </div>
                    <span className="metric-period">{point.period}</span>
                    <span className={`metric-status ${point.status}`}>
                      {point.status}
                    </span>
                  </div>
                ))}
              </div>
              <div className="metric-unit">{metric.unit}</div>
              <p className="caveat">{metric.caveat}</p>
              <div className="citations">
                {metric.source_ids.map((id) => {
                  const source = sources.find((item) => item.id === id)!;
                  return (
                    <a
                      key={id}
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {id} · {source.publisher} ↗
                    </a>
                  );
                })}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
