import { useEffect, useRef, useState } from "react";
import {
  getJson,
  postJson,
  type Claim,
  type Source,
  type ReviewHistory,
  type ReviewAvailability,
  type ProposalRequest,
  type DecisionRequest,
} from "../api";

export function ReviewPanel({
  claim,
  sources,
  onChanged,
}: {
  claim: Claim;
  sources: Source[];
  onChanged: () => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [history, setHistory] = useState<ReviewHistory | null>(null);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [reviewer, setReviewer] = useState("");
  const [reason, setReason] = useState("");
  const [editing, setEditing] = useState(false);
  const [statement, setStatement] = useState(claim.statement);
  const [caveat, setCaveat] = useState(claim.caveat);
  const [evidenceIds, setEvidenceIds] = useState(claim.evidence_ids);
  const [validFrom, setValidFrom] = useState(claim.valid_from ?? "");
  const [validTo, setValidTo] = useState(claim.valid_to ?? "");
  const lastRequest = useRef<{ fingerprint: string; id: string } | null>(null);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setError("");
    async function load() {
      const status = await getJson<ReviewAvailability>(
        "/api/review/status",
        controller.signal,
      );
      setAvailable(status.enabled);
      if (status.enabled) {
        const result = await getJson<ReviewHistory>(
          `/api/claims/${claim.id}/history`,
          controller.signal,
        );
        setHistory(result);
      }
    }
    load().catch((error) => {
      if (!controller.signal.aborted) setError(String(error));
    });
    return () => controller.abort();
  }, [claim.id, open, refresh]);

  async function save(
    path: string,
    body:
      Omit<ProposalRequest, "request_id"> | Omit<DecisionRequest, "request_id">,
  ) {
    setBusy(true);
    setError("");
    setNotice("");
    const fingerprint = JSON.stringify({ path, body });
    if (lastRequest.current?.fingerprint !== fingerprint)
      lastRequest.current = { fingerprint, id: crypto.randomUUID() };
    try {
      const result = await postJson<ReviewHistory>(path, {
        ...body,
        request_id: lastRequest.current.id,
      });
      setHistory(result);
      lastRequest.current = null;
      setNotice("Saved to PostgreSQL. Earlier versions are preserved.");
      setEditing(false);
      setReason("");
      try {
        await onChanged();
      } catch {
        setError(
          "The review was saved, but the graph could not refresh. Reload the page.",
        );
      }
    } catch (error) {
      setError(String(error));
    } finally {
      setBusy(false);
    }
  }

  function startCorrection() {
    setStatement(claim.statement);
    setCaveat(claim.caveat);
    setEvidenceIds(claim.evidence_ids);
    setValidFrom(claim.valid_from ?? "");
    setValidTo(claim.valid_to ?? "");
    setReason("");
    setEditing(true);
    setNotice("");
  }
  const canReview =
    !busy && reviewer.trim().length > 0 && reason.trim().length > 0;
  return (
    <section className="review-panel" aria-label="Review and history">
      <button
        className="review-toggle"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        Review & history {open ? "−" : "+"}
      </button>
      {open && (
        <>
          <p className="footnote">
            Acceptance is a local editorial decision. It does not independently
            verify a source's claim.
          </p>
          {available === false && (
            <p>
              Read-only mode. Configure PostgreSQL to review and save
              corrections.
            </p>
          )}
          {error && (
            <div role="alert" className="review-error">
              <p>{error}</p>
              <button
                disabled={busy}
                onClick={() => {
                  setRefresh((value) => value + 1);
                  void onChanged().catch(() =>
                    setError("Unable to refresh the evidence service."),
                  );
                }}
              >
                Reload history and baseline
              </button>
            </div>
          )}
          {notice && (
            <p role="status" className="review-notice">
              {notice}
            </p>
          )}
          {available !== false && !history && !error && (
            <p aria-live="polite">Loading review history…</p>
          )}
          {history && (
            <>
              <p className="revision-summary">
                Accepted revision:{" "}
                <strong>{history.current_revision || "None yet"}</strong>
              </p>
              <label>
                Reviewer / author
                <input
                  aria-label="Reviewer / author"
                  value={reviewer}
                  maxLength={120}
                  onChange={(event) => setReviewer(event.target.value)}
                />
              </label>
              <label>
                Reason for this action
                <textarea
                  aria-label="Reason for this action"
                  value={reason}
                  maxLength={4000}
                  onChange={(event) => setReason(event.target.value)}
                  rows={2}
                />
              </label>
              <p className="footnote">
                Names are self-reported local attribution, not authenticated
                identities.
              </p>
              <h3>Pending proposals</h3>
              {history.proposals
                .filter((proposal) => !proposal.decision)
                .map((proposal) => {
                  const stale =
                    proposal.base_revision !== history.current_revision;
                  return (
                    <article className="proposal" key={proposal.id}>
                      <span className="badge">
                        {stale ? "Stale proposal" : "Awaiting review"}
                      </span>
                      <p>{proposal.claim.statement}</p>
                      <p className="footnote">{proposal.claim.caveat}</p>
                      <details>
                        <summary>Proposed evidence & dates</summary>
                        <p>
                          Evidence: {proposal.claim.evidence_ids.join(", ")}
                        </p>
                        <p>
                          Valid: {proposal.claim.valid_from ?? "Unknown"} →{" "}
                          {proposal.claim.valid_to ?? "Unknown"}
                        </p>
                        <p>
                          By {proposal.author} · {proposal.proposed_at}
                        </p>
                        <p>{proposal.reason}</p>
                      </details>
                      {stale && (
                        <p className="footnote">
                          The baseline has changed. Create a new proposal to use
                          this wording.
                        </p>
                      )}
                      <div className="review-actions">
                        <button
                          disabled={!canReview || stale}
                          onClick={() =>
                            void save(
                              `/api/proposals/${proposal.id}/decision`,
                              {
                                expected_revision: history.current_revision,
                                decision: "accept",
                                reviewer,
                                reason,
                              },
                            )
                          }
                        >
                          Accept for baseline
                        </button>
                        <button
                          disabled={!canReview}
                          onClick={() =>
                            void save(
                              `/api/proposals/${proposal.id}/decision`,
                              {
                                expected_revision: history.current_revision,
                                decision: "reject",
                                reviewer,
                                reason,
                              },
                            )
                          }
                        >
                          Reject proposal
                        </button>
                      </div>
                    </article>
                  );
                })}
              {!history.proposals.some((proposal) => !proposal.decision) && (
                <p className="footnote">No pending proposals.</p>
              )}
              {!editing && (
                <button
                  className="correction-button"
                  disabled={busy}
                  onClick={startCorrection}
                >
                  Propose correction
                </button>
              )}
              {editing && (
                <form
                  className="correction-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void save(`/api/claims/${claim.id}/proposals`, {
                      base_revision: history.current_revision,
                      statement,
                      caveat,
                      evidence_ids: evidenceIds,
                      valid_from: validFrom || null,
                      valid_to: validTo || null,
                      author: reviewer,
                      reason,
                    });
                  }}
                >
                  <h3>Propose a correction</h3>
                  <p className="footnote">
                    This will remain pending until accepted. Identity and
                    relationship type are unchanged.
                  </p>
                  <label>
                    Proposed statement
                    <textarea
                      required
                      maxLength={4000}
                      rows={4}
                      value={statement}
                      onChange={(event) => setStatement(event.target.value)}
                    />
                  </label>
                  <label>
                    Limitations / caveat
                    <textarea
                      required
                      maxLength={4000}
                      rows={3}
                      value={caveat}
                      onChange={(event) => setCaveat(event.target.value)}
                    />
                  </label>
                  <fieldset>
                    <legend>Retained evidence</legend>
                    <div className="source-checklist">
                      {sources.map((source) => (
                        <label key={source.id}>
                          <input
                            type="checkbox"
                            checked={evidenceIds.includes(source.id)}
                            onChange={(event) =>
                              setEvidenceIds((ids) =>
                                event.target.checked
                                  ? [...ids, source.id]
                                  : ids.filter((id) => id !== source.id),
                              )
                            }
                          />
                          {source.id} · {source.title}
                        </label>
                      ))}
                    </div>
                  </fieldset>
                  <label>
                    Valid from (optional)
                    <input
                      type="date"
                      value={validFrom}
                      onChange={(event) => setValidFrom(event.target.value)}
                    />
                  </label>
                  <label>
                    Valid to (optional)
                    <input
                      type="date"
                      min={validFrom || undefined}
                      value={validTo}
                      onChange={(event) => setValidTo(event.target.value)}
                    />
                  </label>
                  <div className="review-actions">
                    <button
                      type="submit"
                      disabled={
                        !canReview ||
                        !statement.trim() ||
                        !caveat.trim() ||
                        evidenceIds.length === 0
                      }
                    >
                      Save proposal
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => setEditing(false)}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
              <h3>Accepted versions</h3>
              {history.versions.length === 0 && (
                <p className="footnote">Nothing has been accepted yet.</p>
              )}
              {[...history.versions].reverse().map((version) => (
                <details className="version" key={version.revision}>
                  <summary>
                    Revision {version.revision}{" "}
                    {version.revision === history.current_revision
                      ? "· current"
                      : "· retained"}
                  </summary>
                  <p>{version.claim.statement}</p>
                  <p>{version.claim.caveat}</p>
                  <p>
                    Valid: {version.claim.valid_from ?? "Unknown"} →{" "}
                    {version.claim.valid_to ?? "Unknown"}
                  </p>
                  <p>Accepted at: {version.recorded_at}</p>
                  <div className="citations">
                    {version.claim.evidence_ids.map((id) => (
                      <a
                        key={id}
                        href={sources.find((source) => source.id === id)?.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {id} ↗
                      </a>
                    ))}
                  </div>
                </details>
              ))}
              <details className="decision-history">
                <summary>
                  All proposals & decisions ({history.proposals.length})
                </summary>
                {history.proposals.map((proposal) => (
                  <article className="proposal" key={proposal.id}>
                    <strong>
                      {proposal.decision?.decision ?? "pending"} · based on
                      revision {proposal.base_revision}
                    </strong>
                    <p>{proposal.claim.statement}</p>
                    <p>
                      {proposal.author} · {proposal.proposed_at}
                    </p>
                    <p>Proposal reason: {proposal.reason}</p>
                    {proposal.decision && (
                      <>
                        <p>
                          {proposal.decision.reviewer} ·{" "}
                          {proposal.decision.recorded_at}
                        </p>
                        <p>Review reason: {proposal.decision.reason}</p>
                      </>
                    )}
                  </article>
                ))}
              </details>
            </>
          )}
        </>
      )}
    </section>
  );
}
