# Licence manifests

Read by `scripts/check_licences.py`. See `docs/decisions.md` for the decisions and `docs/recommendations/10-assets-and-licences.md` for the reasoning.

- `components.json`: everything that may appear in a public build (software, fonts, data, services), each with its licence, evidence URL and `redistribution` status. `emitted_globs` claim files in `apps/web/dist`; `forbidden_globs` name material that must never ship.
- `source-rights.json`: one entry per source in the packs. `release_excerpt` says whether the retained quote may appear in a public release. A link to a source is always fine.
- `policy.json`: licences accepted for npm runtime dependencies without a human decision.

Run `python scripts/check_licences.py --mode dev` while working and `--mode release` before publishing. Release mode fails on anything unverified, on files no component covers, and on missing `LICENSE` files.

To add an asset: add a component that covers its emitted path, with the evidence URL you actually read and today's date. Never mark something `allowed` from memory.
