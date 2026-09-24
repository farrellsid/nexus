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

## Consequences to keep in view

- **Nothing is publishable yet.** Published tours need accepted evidence, and the local database holds zero accepted versions and zero decisions (44 assertions, 44 candidate proposals, checked 2026-09-23). Claims must be reviewed and accepted first, and known defects (O-C26 is unsupported by its retained excerpt; the oil pack's cutoff label is wrong) must be repaired before acceptance.
- **The cap is in Canadian dollars** while the fetched prices are in US dollars. The exchange rate was not checked. A static public build costs nothing and is the plan, so the cap only constrains a later paid VPS. The 2 GiB droplet with weekly backup was quoted at US$14.40 and may sit close to the limit after conversion and tax.
- **Licence files now exist** (2026-09-24). Release still needs a bundle inventory once the visual shell is built, and the legal advice discussed in the roadmap is not yet decided.
- **Still open** are the items each recommendation lists under "Decisions needed", other than those settled above.
