# Installable industry data packs

Design record, 2026-09-23. Nothing is implemented. The idea is the user's; the mechanics below are assistant proposals awaiting decision. Nothing here is legal advice, and a licensing review is needed before any publication.

## The idea (user)

If Nexus becomes open source, distribute industry-level data packages (copper, semiconductors and so on) that users install as expansions, so nobody has to carry the whole corpus. Much of the underlying material is open data or copyrighted articles, which shapes what a pack may contain.

## Current state (checked 2026-09-23)

- A pack already exists in embryo: an `investigations/NN-name/` folder of three or four loose files (`evidence-pack.json`, `acceptance-cases.json`, optionally `geography.json`, plus a README). The evidence file has `schema_version`, `case_id` and `checked_on`, but there is no manifest, version or dependency declaration.
- **No licence file exists at the repository root**, only `THIRD_PARTY_NOTICES.md`. Neither the code licence nor a data licence has been chosen.
- `Source.rights` is free text. In the oil pack, 4 of 20 sources carry an explicit note that reuse terms are unaudited or content is paid (JODI, China NBS, PPAC, IEA). The copper pack flags none, which shows no note was written, not that the sources are clear.
- God's Eye View's own data documentation lists bundled datasets that are non-commercial or share-alike (TeleGeography, ODbL). Any adopted material inherits those constraints.

## Proposal: what a pack may contain

**Ship references and our own work, never their content.** A pack carries entity and claim structure, source metadata and locators, short attributed excerpts, our own authored text, and a hash of what the maintainer retrieved. It does not carry copies of articles, reports or PDFs. Users who want to verify run the acquisition step locally (see `docs/data-acquisition.md`); any snapshot stays on their machine.

General understanding, to be confirmed by a lawyer: bare facts are treated differently from prose and curated compilations, the EU has a separate database right, and a website's terms may forbid automated fetching regardless of copyright. Our authored notes should be original wording with attribution, not close paraphrase of a copyrighted article.

**Licences are derived, not chosen freely.** Code and data need separate licences. A pack's data licence is bounded by its most restrictive source, so `rights` should become structured (licence identifier, attribution requirement, redistribution class) and a build-time check should refuse a pack whose declared licence conflicts with an included source. A pack containing a non-commercial source cannot be labelled as freely reusable.

**Packs are declarative data, never code.** Installing a stranger's pack must not run anything. Chart templates, analytic functions and tour chapter formats live in the application; packs reference them by identifier. New templates enter the application through review, not through a pack.

## Proposal: anatomy and identity

- **Core registry pack** holding shared things: countries, major chokepoints, ports, common materials. Industry packs declare `depends_on` it and add only what is new.
- **Industry packs** hold the durable structure: entities, supply-chain stages, history, significance criteria.
- **Brief add-ons** hold dated investigations (for example the 2025-Q3 to 2026-Q2 oil disruption brief). This follows the earlier decision that an industry contains investigations.
- **Identity anchored on Wikidata Q-identifiers**, which the taxonomy research found stable and widely known. Two packs that both include "Strait of Malacca" or "China" merge on that identifier instead of colliding.
- A manifest per pack: id, semantic version, schema version, dependencies, licence, content hash.

## Proposal: install and update semantics

Installing reuses the existing machinery: pack records arrive as candidates through the same import path fixtures use today, and updates arrive as proposals against the current accepted revision. A user's local review decisions are never overwritten, because history is append-only. Source verification should report three states, not pass or fail: matches what the maintainer saw, changed since packaging, or unreachable. A changed page is information, not an error.

Start simple: a `packs/` directory, a manifest schema, and install as a migration. A package server, signing and a registry can wait until there are outside users.

## Proposal: security of user-shared packs

If users can share packs, the risk is not a "virus" inside JSON, which cannot execute. It is everything around it:

- **Code execution:** packs are declarative JSON only. No scripts, macros or plugin hooks.
- **Archive attacks:** reject paths outside the pack root (zip-slip), reject symlinks, cap file count and total uncompressed size (decompression bombs).
- **Parser and denial of service:** strict schema that forbids unknown fields (the `Source` model already does), with limits on depth, string length and record count.
- **UI injection:** render all pack text as text, never as HTML. If markdown is ever allowed, sanitise it. Restrict links to https and show the domain. Packs may not load remote images or fonts, which can track readers.
- **SQL:** `scripts/generate-additive-migration.py` builds SQL by quoting strings. That is acceptable for a maintainer's own fixtures and unsafe for untrusted packs. Untrusted installs must use parameterised statements.
- **False or poisoned content:** imported as unreviewed candidates labelled with the pack's origin, never auto-accepted. A bad pack is retracted by marking, not deleting, so history stays append-only.
- **Prompt injection:** text from a pack is untrusted data. The chat agent may act only through the validated action API, and pack text can never grant it new actions or change its instructions.
- **Authenticity:** a manifest with a content hash now, maintainer signatures later. Unsigned packs are shown as unverified origin.

## Open questions

- **Licences:** which licence for code, which for maintained data, and whether share-alike is acceptable.
- **Review state in shipped packs:** a pack can carry "maintainer-reviewed" as provenance, distinct from the user's own acceptance. Otherwise every install means re-reviewing every claim. What should the UI show for each?
- **Granularity:** is the industry pack the right unit, or should chapters or regions be installable separately?
- **Hash drift:** a page hash proves what the maintainer saw, not what is true now. How prominently should that be shown?
- **Copper's rights notes** should be audited before that pack is treated as distributable.
