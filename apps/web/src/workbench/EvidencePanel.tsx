import type { Claim, Source } from "../api";
import { ReviewPanel } from "./ReviewPanel";

export function EvidencePanel({
  claim,
  sources,
  onChanged,
}: {
  claim: Claim | undefined;
  sources: Source[];
  onChanged: () => Promise<void>;
}) {
  if (!claim)
    return (
      <aside className="evidence">
        <p>Select a relationship to inspect its evidence.</p>
      </aside>
    );
  const supporting = sources.filter((source) =>
    claim.evidence_ids.includes(source.id),
  );
  return (
    <aside className="evidence" aria-label="Evidence inspector">
      <div className="eyebrow">
        Evidence inspector <span>{claim.id}</span>
      </div>
      <h2>{claim.statement}</h2>
      <span className="badge">
        {claim.review_status === "accepted"
          ? "Accepted in local review"
          : claim.review_status === "rejected"
            ? "Rejected in local review"
            : "Source-checked candidate"}
      </span>
      <p className="caveat">{claim.caveat}</p>
      <dl className="dates">
        <div>
          <dt>Source as of</dt>
          <dd>{claim.source_as_of ?? "Undated context"}</dd>
        </div>
        <div>
          <dt>Recorded in fixture</dt>
          <dd>{claim.recorded_on}</dd>
        </div>
        <div>
          <dt>Valid-time bounds</dt>
          <dd>
            {claim.valid_from ?? "Unknown"} → {claim.valid_to ?? "Unknown"}
          </dd>
        </div>
      </dl>
      <ReviewPanel
        key={claim.id}
        claim={claim}
        sources={sources}
        onChanged={onChanged}
      />
      <h3>
        Retained sources <span className="count">{supporting.length}</span>
      </h3>
      {supporting.map((source) => (
        <article className="source" key={source.id}>
          <div className="source-meta">
            {source.id} · {source.language.toUpperCase()} · {source.format}
          </div>
          <a href={source.url} target="_blank" rel="noreferrer">
            {source.title} ↗
          </a>
          <p>
            {source.publisher} ·{" "}
            {source.published_on ?? "Publication date unknown"}
          </p>
          <blockquote>“{source.excerpt}”</blockquote>
          <p className="locator">{source.locator}</p>
          <details>
            <summary>Provenance & limitations</summary>
            <p>Origin group: {source.origin_group}</p>
            <p>{source.independence}</p>
            <p>{source.rights}</p>
          </details>
        </article>
      ))}
      <p className="footnote">
        Short anchors help locate the source. Read the full passage to assess
        support. Shared-origin releases are not independent corroboration.
      </p>
    </aside>
  );
}
