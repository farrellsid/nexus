# Decision log

Decisions made by the user, in order. Design records and recommendations elsewhere in `docs/` carry the reasoning; this file is the place to see what is actually decided. Approved directions are not implemented unless stated.

## 2026-09-22, frontend and data model

- Rebuild the frontend on a God's Eye View foundation. The reason is visual and interaction quality, not only the rendering bug. (`docs/frontend-rebuild.md`)
- Backend stays Python, FastAPI and PostgreSQL. Frontend becomes TypeScript, adopting God's Eye's visual and interaction design but not its plain-JavaScript code.
- An industry is a persistent domain; investigations sit inside it.
- Entities live in one shared registry across industries.
- Display prominence uses a sourced significance criterion where one exists, with a curated tier as fallback.
- Entity types use two levels: category and subtype, mapped to external vocabularies where they fit.
- Live tracking, voice control, Google integrations and Pinokio plumbing are stripped. Chat is later and out of scope for now.

## 2026-09-23, interface

- Dark visual style. The globe is the centrepiece and stays behind other screens. Tours advance on "next". Desktop first. Tours are curated, one per major industry, with some generation for updates. (`docs/ui-flows.md`)
- An organisation is shown only where it has sourced connections.
- Connections are offered both as a highlight filter over the globe and as a separate graph view.
- Curate is a separate route that a public read-only build omits.
- Corner readouts are on by default and can be toggled off.

## 2026-09-23, after the technical design review (`docs/recommendations/`)

Approved as direction, with the details still to be designed:

- **Cost cap:** hosting must cost no more than about CAD 10 to 20 a month.
- **Normalisation:** versioned projections for vocabularies, time and measurements. Historical IDs and payloads are preserved, and legacy IDs resolve as aliases into the shared registry. Accepted history is not rewritten or re-ID'd. (`01-vocabularies.md`)
- **Disagreement and units:** distinct measure, period and unit definitions. Sources are shown side by side by default. A range appears only after an explicit comparability review, and there is no implicit mass-to-volume conversion. (`03-conflicting-sources.md`, `04-units-and-conversions.md`)
- **Shipping:** explicitly modelled alternatives over a small sourced network, with no fabricated port connectors and no inferred cargo routes. (`05-real-geometry.md`)
- **Public release:** a static public snapshot with local authoring. MIT for original code and CC BY 4.0 for original authored material. Unverified and non-commercial assets are excluded from the default release. (`07-hosting-cost-and-identity.md`, `10-assets-and-licences.md`)
- **Published tours use accepted versions only.** Releases are pinned, and a change to a dependency requires review. (`06-guided-tours.md`)

## 2026-09-24, rights and scope

- **Copyright holder** for the notices is `farrellsid`. `LICENSE` (MIT) and `LICENSE-CONTENT.md` (CC BY 4.0, legal text unmodified from creativecommons.org) now exist.
- **`Zlib` is on the npm licence allow-list**, on the strength of pako's file headers.
- **Copper publishers' terms are audited when the data is expanded**, not now. Until then their excerpts are withheld from any public build.

## 2026-09-24, oil pack repair (assistant proposals, awaiting user approval)

- **Repairs supersede; they never rewrite.** Seven replacement source versions (O-S21 to O-S27) are added; the old records stay and are declared superseded in `investigations/excerpt-exceptions.json`. Claims move to them only through 13 evidence-only correction proposals that a person accepts.
- **Replacement versions are not extra independent sources.** Each `independence` note says so, and each keeps its original `origin_group`.
- **The coverage label moves from 2026-09-10 to 2026-09-16** because the pack contains evidence dated 2026-09-16. This is an assistant proposal; the user decides the wording.
- **Excerpts should match the page's exact characters.** The verifier folds case, quotes and dashes so it does not fail on typography; a strict character-exact pass is a possible later option.

## 2026-09-24, normalisation release (proposed by the assistant; approved by the user the same day)

- **One release covers both investigations** and is approved as a whole by a stored decision; every row stays append-only. A later release may add but never drop or repoint an accepted entity or alias.
- **Canonical entity ID is `<category>/<slug>`** (for example `place/china`), using the two-level taxonomy. Legacy IDs resolve as case-scoped aliases.
- **Measurement IDs are `<case_id>:<metric_id>:<n>`**, permanent once accepted; `n` is a provenance pointer only.
- **The overloaded metric `period` is repaired in the projection.** O-M06 and O-M11 rows get an entity and take their period from the group's context; the pack is unchanged.
- **Nothing is `observed`** in vocabulary 1. A forecast must name its issuer in a note.
- **Data adapters read accepted releases only.**

## 2026-09-24, evaluation and comparability (proposed by the assistant; classes and comparability rules approved by the user)

- **Deterministic evaluation before any model.** Counts stay raw; failures are listed. Expected answers are drafts until the user confirms each.
- **The retriever is a baseline** (BM25 plus an entity boost); vectors stay deferred until a measured miss justifies them.
- **An answerer sees only the question and the hits**, never the oracle, so a model adapter can replace it.
- **A range needs a reviewer's `comparable` mark, at least two independent origins, one lane and unit, and recorded scope metadata.** It is labelled "range of N reports; not a confidence interval". A revision or a shared origin never counts as a second report.
- **Comparability judgements are append-only and reviewer-attributed.** The user is the only reviewer for now. No write endpoint exists yet.

## 2026-09-24, acquisition (assistant proposals, awaiting user approval)

- **Three storage policies per source:** `store`, `hash_only`, `none`. Every source defaults to `hash_only`; the user decides which publishers become `store`.
- **Verification compares to a named baseline and is not a truth score.** A missing baseline is `unreachable` (`baseline_missing`, not ready), never a match. A first snapshot of a legacy source is a new baseline, not a reconstruction of what the maintainer saw.
- **A byte match and a text match are reported separately, and either gives `matches`,** because a real page varied between fetches while its text did not (see `docs/acquisition-providers.md`).
- **HTML first.** PDFs and scans are logged and hashed but not extracted until an extractor is chosen.
- **The only network path is `scripts/acquire.py`,** dry run by default, one fetch per `--confirm`. No scheduled, startup or automatic fetching.
- **Proposal gates are mechanical.** Passing lets a proposal enter human review and never means the claim is entailed.

## 2026-09-24, provider and storage decisions (the user's)

- **Providers:** EIA API v2 and JODI CSV downloads. GDELT is under discussion as a discovery layer, not evidence (`docs/acquisition-providers.md`).
- **Local storage:** every source is `store`, for private local research use under fair use. The intent is to collect broadly now and filter what may be published later. Working assumption: the data may not be published publicly. Publication is filtered by the release gate, which is unchanged.
- **Secrets:** the EIA key lives in `.local/` only. Logged URLs must redact `api_key` before any adapter exists.

## 2026-09-24, adapters and the source survey

- **Adapters are pure parsers.** Only `scripts/acquire.py` and `scripts/crosscheck.py` touch the network, dry run by default, one request per `--confirm`.
- **Credential values are redacted everywhere they could be logged,** including redirect chains and error text, and a body containing a known secret is never stored.
- **Comparisons use exact scale changes only** and round the provider's value to the pack's own precision; a `differs` result goes to a person.
- **A cross-check is not a verdict.** Agreement with a provider does not show the pack cited it.
- **Provider series are not yet `evidence_sources`,** so cross-checks write a manifest of hashes and redacted URLs instead of database attempts. Registering them is an open decision.

## 2026-09-24, EIA registered; other adapters (the user's direction)

- **Three EIA API series are registered sources (O-S28 to O-S30)** with baselines, in normalisation release r2. EIA is treated as reliable for these series; agreement is still not independence, and the origin group is recorded as one EIA API view of the surveys the pack already cites.
- **An API response's canonical text is its data rows only,** so metadata changes are not data changes.
- **A blocked request is recorded, not worked around.** A 403, 412, a certificate failure or a 429 ends that request; no user-agent spoofing, no certificate bypass, no automatic retry. Refused sources go to a manual-download path.
- **GDELT is discovery-only,** cited as the GDELT Project with a link, one query at a time.

## 2026-09-24, working with what we have (the user's direction)

- **Data-source work stops here for now.** The remaining gaps (China's monthly crude figures, OPEC and Energy Institute files, GEM, ANP, GDELT volume, O-M11's August values) are targeted later, if they appear or the information turns out to be incomplete.
- **Measurement-level source bindings to O-S28 to O-S30 were first deferred, then built at the user's request** (release r3, migration 012). A binding is additive and states its basis; it never replaces a metric group's sources. An EIA-to-EIA binding is recorded as the same publisher and survey, so it does not count as an independent report.

## 2026-09-24, M5 approach (the user's answers)

- **Strip steps are committed by the assistant on branch `m5-shell`, never on `master`,** each commit naming its paths. This is a scoped exception to "the user makes the commits", for that branch only.
- **Retained upstream modules stay JavaScript; new Nexus code is strict TypeScript;** React comes in M6 as mounted panels.
- **Local development keeps Esri and OSM imagery; the public build uses Natural Earth** through one flag.

## 2026-09-25, M5 shell: assistant proposals awaiting the user

These were made while building `apps/shell`, are recorded in `apps/shell/UPSTREAM.md`, and stand unless the user objects.

- **The shell shows no invented instrument data.** Classification banners, mission, sensor and orbit ids, GSD and NIIRS, collection time and the REC light were removed from the HUD; what remains is measured from the camera or the clock.
- **The mark and icons are drawn for Nexus** (`nexus-mark.svg` and three small icons), because the upstream logo is another project's identity and its icons have no provenance. They can be replaced by a designed mark at any time.
- **Upstream's documentation (650 KB) was deleted** from `apps/shell`; it described removed features and would mislead later work. The import commit in git history keeps it.
- **The action layer's verbs are camera, layer and tour operations only** and cannot make a request or write evidence; the mouse and panels do not use it yet.
- **The shell opens on the Indian Ocean** and its location presets are the six oil stops in two groups (Gulf and Red Sea; Southeast Asian straits).
- **Share-link input is range-checked and clamped;** unknown names fall back to defaults.
- **The 2D fallback replaces the whole page** when WebGL is missing, startup fails, or `?view=2d` is given.
- **Still open for the user (D3):** which visual effects stay, frame rate on their hardware, and reduced motion.

## 2026-09-25, live tracking requested back (undecided)

After the M5 check the user said planes and boats add a lot and should be added to the milestones. The earlier decision stripped live tracking, so this is recorded as an open request, not a reversal: feeds, terms, keys, cost and the local-only versus public question must be settled first (see the M5 feedback in `docs/roadmap.md`).

## Consequences to keep in view

- **Nothing is publishable yet.** Published tours need accepted evidence, and the local database holds zero accepted versions and zero decisions (44 assertions, 44 candidate proposals, checked 2026-09-23). Claims must be reviewed and accepted first, and known defects (O-C26 is unsupported by its retained excerpt; the oil pack's cutoff label is wrong) must be repaired before acceptance.
- **The cap is in Canadian dollars** while the fetched prices are in US dollars. The exchange rate was not checked. A static public build costs nothing and is the plan, so the cap only constrains a later paid VPS. The 2 GiB droplet with weekly backup was quoted at US$14.40 and may sit close to the limit after conversion and tax.
- **Licence files now exist** (2026-09-24). Release still needs a bundle inventory once the visual shell is built, and the legal advice discussed in the roadmap is not yet decided.
- **Still open** are the items each recommendation lists under "Decisions needed", other than those settled above.
