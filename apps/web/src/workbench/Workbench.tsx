import { useEffect, useState } from "react";
import { getJson, type Investigation, type Neighborhood } from "../api";
import { EvidencePanel } from "./EvidencePanel";
import { GuidedGeographyView } from "./GuidedGeographyView";
import { MetricsView } from "./MetricsView";
import { RelationshipGraph } from "./RelationshipGraph";

type InvestigationSummary = { case_id: string; title: string; scope: string };

export function Workbench() {
  const [data, setData] = useState<Investigation | null>(null);
  const [investigations, setInvestigations] = useState<InvestigationSummary[]>(
    [],
  );
  const [caseId, setCaseId] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    getJson<InvestigationSummary[]>("/api/investigations", controller.signal)
      .then((available) => {
        setInvestigations(available);
        const preferred = available.some(
          (item) => item.case_id === "oil-system-2025q3-2026q2",
        )
          ? "oil-system-2025q3-2026q2"
          : available[0]?.case_id;
        if (!preferred) throw new Error("No investigations are available.");
        setCaseId(preferred);
      })
      .catch((error) => {
        if (!controller.signal.aborted) setError(String(error));
      });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    if (!caseId) return;
    const controller = new AbortController();
    setData(null);
    setError("");
    getJson<Investigation>(
      `/api/investigation?case_id=${encodeURIComponent(caseId)}`,
      controller.signal,
    )
      .then(setData)
      .catch((error) => {
        if (!controller.signal.aborted) setError(String(error));
      });
    return () => controller.abort();
  }, [caseId]);
  if (error)
    return (
      <main className="loading">
        <h1>Evidence service unavailable</h1>
        <p role="alert">{error}</p>
        <p>Start the Nexus backend, then reload this page.</p>
        <button onClick={() => location.reload()}>Try again</button>
      </main>
    );
  if (!data)
    return (
      <main className="loading" aria-live="polite">
        Loading the evidence workbench…
      </main>
    );
  async function refreshData() {
    const controller = new AbortController();
    const next = await getJson<Investigation>(
      `/api/investigation?case_id=${encodeURIComponent(caseId)}`,
      controller.signal,
    );
    setData(next);
  }
  return (
    <LoadedWorkbench
      key={caseId}
      data={data}
      investigations={investigations}
      caseId={caseId}
      onCase={setCaseId}
      onChanged={refreshData}
    />
  );
}

function LoadedWorkbench({
  data,
  investigations,
  caseId,
  onCase,
  onChanged,
}: {
  data: Investigation;
  investigations: InvestigationSummary[];
  caseId: string;
  onCase: (caseId: string) => void;
  onChanged: () => Promise<void>;
}) {
  const { pack, questions } = data;
  const [entityId, setEntityId] = useState(pack.entities[0].id);
  const [claimId, setClaimId] = useState(pack.claims[0]?.id ?? "");
  const [tab, setTab] = useState<
    "relationships" | "geography" | "metrics" | "timeline" | "questions"
  >(pack.briefing ? "metrics" : "relationships");
  const [search, setSearch] = useState("");
  const [depth, setDepth] = useState(1);
  const [graph, setGraph] = useState<Neighborhood | null>(null);
  const [graphError, setGraphError] = useState("");
  const [questionId, setQuestionId] = useState(questions[0].id);
  const [retry, setRetry] = useState(0);
  const selectedEntity = pack.entities.find(
    (entity) => entity.id === entityId,
  )!;
  const selectedClaim = pack.claims.find((claim) => claim.id === claimId);
  const question = questions.find((question) => question.id === questionId)!;
  const degrees = pack.claims.reduce<Record<string, number>>(
    (counts, claim) => {
      counts[claim.subject] = (counts[claim.subject] ?? 0) + 1;
      counts[claim.object] = (counts[claim.object] ?? 0) + 1;
      return counts;
    },
    {},
  );
  const isolatedCount = pack.entities.filter(
    (entity) => !degrees[entity.id],
  ).length;
  const leafCount = pack.entities.filter(
    (entity) => degrees[entity.id] === 1,
  ).length;

  useEffect(() => {
    const controller = new AbortController();
    setGraph(null);
    setGraphError("");
    getJson<Neighborhood>(
      `/api/entities/${encodeURIComponent(entityId)}/neighborhood?depth=${depth}&case_id=${encodeURIComponent(caseId)}`,
      controller.signal,
    )
      .then(setGraph)
      .catch((error) => {
        if (!controller.signal.aborted) setGraphError(String(error));
      });
    return () => controller.abort();
  }, [entityId, depth, retry, data, caseId]);

  function selectEntity(id: string) {
    if (id === entityId) return;
    // Clear the previous neighborhood before rendering a newly selected center.
    setGraph(null);
    setEntityId(id);
    setClaimId(
      pack.claims.find((claim) => claim.subject === id || claim.object === id)
        ?.id ?? "",
    );
  }

  return (
    <>
      <header className="topbar">
        <a className="brand" href="/">
          N<span>◇</span>XUS
        </a>
        <span className="product-label">
          INDUSTRIAL SYSTEMS / EVIDENCE WORKBENCH
        </span>
        <label className="investigation-picker">
          <span>Industry brief</span>
          <select
            value={caseId}
            onChange={(event) => onCase(event.target.value)}
          >
            {investigations.map((item) => (
              <option key={item.case_id} value={item.case_id}>
                {item.title}
              </option>
            ))}
          </select>
        </label>
        <span className="local-indicator">Local research workspace</span>
      </header>
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            {pack.briefing ? "Industry brief" : "Evidence pilot"}
            <span> / {pack.case_id}</span>
          </div>
          <h1>{pack.briefing?.title ?? "From copper to cables."}</h1>
          <p>
            {pack.briefing?.framing ??
              "A network of disclosed relationships, with the gaps left visible."}
          </p>
        </div>
        <div className="snapshot">
          <span>{pack.briefing ? "EVIDENCE CHECKED" : "FIXTURE REVIEWED"}</span>
          <strong>{pack.checked_on}</strong>
          <small>
            {pack.briefing
              ? `${pack.briefing.window_start} → ${pack.briefing.window_end}`
              : "Historical evidence · not a live feed"}
          </small>
        </div>
      </div>
      <div className="scope-banner">
        <span>READING THIS NETWORK</span>
        {pack.briefing
          ? " Aggregate flows and graph links do not trace individual cargoes or establish a single cause."
          : " Commercial links do not prove that the same lot of copper reached a cable manufacturer."}
      </div>
      <main className="workbench">
        <nav className="entity-nav" aria-label="Investigation entities">
          <div className="eyebrow">
            Entities <span>{pack.entities.length}</span>
          </div>
          <label className="search-label" htmlFor="entity-search">
            Find in this investigation
          </label>
          <input
            id="entity-search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search entities…"
          />
          <div className="entity-list">
            {pack.entities
              .filter((entity) =>
                entity.name.toLowerCase().includes(search.toLowerCase()),
              )
              .map((entity) => (
                <button
                  key={entity.id}
                  className={
                    entity.id === entityId
                      ? "entity-item selected"
                      : "entity-item"
                  }
                  onClick={() => {
                    selectEntity(entity.id);
                    setTab("relationships");
                  }}
                >
                  <span>{entity.type.replaceAll("_", " ")}</span>
                  <strong>{entity.name}</strong>
                </button>
              ))}
          </div>
          {!pack.entities.some((entity) =>
            entity.name.toLowerCase().includes(search.toLowerCase()),
          ) && <p className="footnote">No matching entities.</p>}
          <p className="footnote network-health">
            Network coverage: {isolatedCount} isolated · {leafCount} with one
            documented relationship
          </p>
          <p className="footnote">{pack.scope}</p>
        </nav>
        <section className="workspace" aria-label="Investigation workspace">
          <div className="tabs" role="tablist" aria-label="Workbench views">
            {(
              [
                "relationships",
                ...(pack.briefing ? (["metrics"] as const) : []),
                ...(data.geography ? (["geography"] as const) : []),
                "timeline",
                "questions",
              ] as const
            ).map((view) => (
              <button
                id={`tab-${view}`}
                role="tab"
                aria-selected={tab === view}
                aria-controls="workspace-panel"
                key={view}
                onClick={() => {
                  setTab(view);
                  if (view === "questions")
                    setClaimId(question.claim_ids[0] ?? "");
                  if (view === "relationships")
                    setClaimId(
                      pack.claims.find(
                        (claim) =>
                          claim.subject === entityId ||
                          claim.object === entityId,
                      )?.id ?? "",
                    );
                }}
              >
                {view === "questions"
                  ? "Reading guide"
                  : view[0].toUpperCase() + view.slice(1)}
              </button>
            ))}
          </div>
          <div
            id="workspace-panel"
            role="tabpanel"
            aria-labelledby={`tab-${tab}`}
          >
            {tab === "relationships" && (
              <>
                <div className="section-heading">
                  <div>
                    <div className="eyebrow">
                      {selectedEntity.type.replaceAll("_", " ")}
                    </div>
                    <h2>{selectedEntity.name}</h2>
                  </div>
                  <label className="depth">
                    Explore{" "}
                    <select
                      aria-label="Exploration depth"
                      value={depth}
                      onChange={(event) => setDepth(Number(event.target.value))}
                    >
                      <option value={1}>1 step</option>
                      <option value={2}>2 steps</option>
                    </select>
                  </label>
                </div>
                <p className="location-note">
                  Location:{" "}
                  {selectedEntity.coordinates
                    ? selectedEntity.coordinates.join(", ")
                    : "not validated"}{" "}
                  · {selectedEntity.location_note}
                </p>
                {graphError ? (
                  <div role="alert">
                    <p>{graphError}</p>
                    <button onClick={() => setRetry((value) => value + 1)}>
                      Retry relationships
                    </button>
                  </div>
                ) : graph ? (
                  <RelationshipGraph
                    graph={graph}
                    selectedEntity={entityId}
                    selectedClaim={claimId}
                    onEntity={selectEntity}
                    onClaim={setClaimId}
                  />
                ) : (
                  <p aria-live="polite">Loading relationships…</p>
                )}
              </>
            )}
            {tab === "timeline" && (
              <div className="view-content">
                <div className="eyebrow">Dated developments</div>
                <h2>What was reported, and when?</h2>
                <p className="muted">
                  Event dates and publication dates are separate. Month and
                  quarter precision remain intact. This is not a reconstruction
                  of what the app knew at the time.
                </p>
                <div className="timeline">
                  {pack.events.map((event) => (
                    <article key={event.id} className="event">
                      <div className="event-date">
                        <span>{event.event_time ?? "Date not reported"}</span>
                        <small>{event.precision.replaceAll("_", " ")}</small>
                      </div>
                      <div>
                        <span
                          className={
                            event.kind === "forecast"
                              ? "badge forecast"
                              : "badge"
                          }
                        >
                          {event.kind.replaceAll("_", " ")}
                        </span>
                        <h3>{event.description}</h3>
                        <p className="muted">
                          Published: {event.published_on ?? "See source"}
                        </p>
                        <div className="citations">
                          {event.source_ids.map((id) => {
                            const source = pack.sources.find(
                              (source) => source.id === id,
                            )!;
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
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            )}
            {tab === "metrics" && pack.briefing && (
              <MetricsView briefing={pack.briefing} sources={pack.sources} />
            )}
            {tab === "geography" && data.geography && (
              <GuidedGeographyView
                geography={data.geography}
                onExplore={(id) => {
                  selectEntity(id);
                  setTab("relationships");
                }}
              />
            )}
            {tab === "questions" && (
              <div className="view-content">
                <div className="eyebrow">
                  Curated reading guide · no AI generation
                </div>
                <h2>Follow the evidence. Know its limits.</h2>
                <p className="muted">
                  These authored answers come from the pilot research notes.
                  Local reviews do not rewrite this guide. They are not a model
                  evaluation or live research.
                </p>
                <label htmlFor="question">Explore a question</label>
                <select
                  id="question"
                  className="question-select"
                  value={questionId}
                  onChange={(event) => {
                    setQuestionId(event.target.value);
                    const next = questions.find(
                      (question) => question.id === event.target.value,
                    )!;
                    setClaimId(next.claim_ids[0] ?? "");
                  }}
                >
                  {questions.map((question) => (
                    <option key={question.id} value={question.id}>
                      {question.question}
                    </option>
                  ))}
                </select>
                <article className="answer">
                  <span className="eyebrow">Research note / {question.id}</span>
                  <h3>{question.question}</h3>
                  <p>{question.expected_answer}</p>
                  <div className="citations">
                    {question.claim_ids.map((id) => (
                      <button key={id} onClick={() => setClaimId(id)}>
                        Inspect {id} ↗
                      </button>
                    ))}
                  </div>
                  {question.claim_ids.length === 0 && (
                    <p className="footnote">
                      No supporting claim is provided for this question. Missing
                      evidence is not evidence of absence.
                    </p>
                  )}
                </article>
              </div>
            )}
          </div>
        </section>
        <EvidencePanel
          claim={selectedClaim}
          sources={pack.sources}
          onChanged={onChanged}
        />
      </main>
      <footer>
        NEXUS / {pack.case_id.toUpperCase()}{" "}
        <span>
          {pack.claims.length} assertions ·{" "}
          {
            pack.claims.filter((claim) => claim.review_status === "accepted")
              .length
          }{" "}
          accepted in local review · {pack.sources.length} sources · evidence
          window bounded
        </span>
      </footer>
    </>
  );
}
