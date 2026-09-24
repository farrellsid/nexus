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

## Consequences to keep in view

- **Nothing is publishable yet.** Published tours need accepted evidence, and the last observed state was zero accepted claims. Claims must be reviewed and accepted first, and known defects (O-C26 is unsupported by its retained excerpt; the oil pack's cutoff label is wrong) must be repaired before acceptance.
- **The cap is in Canadian dollars** while the fetched prices are in US dollars. The exchange rate was not checked. A static public build costs nothing and is the plan, so the cap only constrains a later paid VPS. The 2 GiB droplet with weekly backup was quoted at US$14.40 and may sit close to the limit after conversion and tax.
- **No LICENSE file exists yet.** The licence choice is decided, but writing the files needs the copyright holder's name for the notice, and release still needs the asset audit in `10-assets-and-licences.md`.
- **Still open** are the items each recommendation lists under "Decisions needed", other than those settled above.
