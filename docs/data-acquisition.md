# Data acquisition and evidence verification

Design record, 2026-09-23. Nothing here is implemented, and nothing here authorizes scheduled fetching, new providers or cost. Sections marked **proposal** are assistant proposals awaiting the user's decision.

## The problem (raised by the user)

Evidence is currently gathered by agents using web search and fetch tools, then organised into the evidence packs by the same agents. That is non-deterministic: results depend on which tool is available, how a page is rendered, and the chat context. The user also wants to expand and refresh the corpus from within Nexus, or at startup, later on.

## Current state (checked 2026-09-23)

- **No acquisition code exists.** A search of `backend/` and `scripts/` finds no HTTP fetching, scraping or ingestion outside tests. Everything in the packs was written by agents and imported as fixtures.
- **Nothing records how a source was retrieved.** The `Source` model (`backend/app/evidence.py`) holds title, url, locator, excerpt, `checked_on`, `review_status`, rights and independence. `review_status` values such as `primary_document_read_via_web` are free text typed by the agent, not verified facts. The database `content_hash` on `evidence_sources` fingerprints the source's metadata record, not the fetched document. No snapshot of any fetched page or PDF is kept.
- **Excerpts are not machine-verified.** No test checks that an excerpt appears in its cited source.

### Spot check of the oil pack's excerpts

One run against the live pages: 17 sources were HTML and fetchable, and **7 of 17** excerpts were found verbatim. The rest fall into distinct groups:

- Trailing-character mismatches (O-S15, S16, S17, about 100% matches): checker strictness, not a data problem.
- Non-verbatim quotes (O-S05, S07, S08, S10). **Correction, 2026-09-23:** my first description of these was wrong for two of the four, as the technical design review found and I confirmed against my own fetch output. For O-S05 and O-S07 the page contains "million barrels per day (b/d)" and the stored anchor omits the parenthetical. For O-S08 and O-S10 the page abbreviates to "million b/d" and the stored anchor spells it out. The cause is not established and should not be assumed to be one explanation. All four are shown in quotation marks and are not verbatim.
- Not reproducible by plain HTTP: EIA's STEO page (O-S02) returns almost no text to a plain fetch because it is script-rendered; O-S09 returns mostly navigation; O-S06 failed to fetch. JODI's landing page (O-S03) now reports a newer update month than the stored excerpt, and no snapshot exists of what it said when checked. PDFs (O-S14, O-S19) were not checked; O-S19 was image-based and read via page vision, which a substring check cannot verify.

"Not found" is not evidence of fabrication and no incorrect figure was identified. Two further gaps came from the technical design review and were confirmed: claim O-C26 (Iraq, 3.86 million b/d) cites O-S20, whose retained excerpt is about global production and contains neither "Iraq" nor "3.86", so the retained evidence does not support that claim; and the pack states developments "through 2026-09-10" while including evidence published 2026-09-11 (O-S20, O-E08) and 2026-09-16 (O-S14, O-E07). The overall finding is that verification is currently impossible for most of the pack. The check script was not kept in the repository.

## Proposal: a pipeline split by how much determinism each stage can promise

1. **Acquire (deterministic, no LLM).** Per-source adapters store an immutable raw snapshot with sha256, UTC timestamp, HTTP status and tool version. Prefer structured feeds where they exist, since numbers can then come straight from data without anyone reading prose. `docs/design.md` names the EIA Open Data API and JODI downloads as leads; their endpoints have not been sampled.
2. **Extract (LLM proposes only).** An agent may propose entities, claims and metric rows, but each excerpt must be a verbatim substring of the stored snapshot and each figure must appear in its excerpt. A proposal that fails either check is rejected mechanically.
3. **Review (human).** Passing proposals enter the existing proposal / decision / append-only version machinery. That back half already exists.
4. **Refresh.** Re-fetch, compare hashes, and open a review item on change. Never overwrite. Any startup or in-app check should be opt-in and use conditional requests, and it only ever creates pending proposals.

The LLM stays non-deterministic where it proposes and is never trusted where things are recorded.

## Open questions

- **Rights.** `Source.rights` limits some sources to short anchors. Government works (EIA) can be stored in full; for publisher pages the repository would keep the hash and a local-only copy.
- **Script-rendered pages.** A headless browser makes acquisition work but adds a renderer whose version must be recorded with the snapshot.
- **PDFs and scans.** Text-layer PDFs can be substring-checked; image-only PDFs need OCR with recorded confidence or human confirmation.
- **Mutable "latest" URLs.** O-S14's own note says its URL is overwritten every week, so it cannot be verified later without a snapshot.
- **Excerpt policy.** Either `excerpt` must be verbatim and verifiable, with a separate `note` for authored paraphrase, or the four reworded excerpts get corrected. The UI must not show unverified text in quotation marks.
