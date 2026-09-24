# G. Hosting, cost and identity

## Recommendation

Publish a permitted, read-only static snapshot first; keep review and acquisition local.
Use the same frontend with an API/snapshot data adapter.
A small VPS can fit the stated budget, but it creates maintenance and security work.
Managed compute plus managed PostgreSQL leaves little or no budget margin.
No visitor accounts or hosted model calls are needed for the first public version.

### Fetched price comparison

USD list prices retrieved for this review (2026-09-24 UTC / 2026-09-23 project brief date). Tax, exchange rates, optional domain and provider-specific extras are excluded. The user's dollar currency is unspecified, so these are not a promise to fit CAD 20.

| Architecture | Retrieved baseline | Assessment |
|---|---|---|
| Cloudflare Pages static files, no Functions | Static requests free and unlimited on free/paid plans, per [Pages pricing](https://developers.cloudflare.com/pages/functions/pricing/) | Recommended $0 platform starting point within applicable limits/terms; no database/API/model service |
| DigitalOcean Basic VPS; FastAPI + PostgreSQL on one machine | 1 GiB $6/month; 2 GiB $12/month; weekly backup option 20% of Droplet price, per [Droplet pricing](https://www.digitalocean.com/pricing/droplets) | Prefer testing 2 GiB: $14.40 with weekly VM backup. Separate database/object backup allowance and taxes still needed; capacity not benchmarked |
| DigitalOcean App Platform + managed PostgreSQL | App 512 MiB $5/month, 50 GiB transfer; [App Platform pricing](https://www.digitalocean.com/pricing/app-platform). Smallest listed managed PostgreSQL row $15.15/month; storage also described at $0.215/GiB-month; [database pricing](https://www.digitalocean.com/pricing/managed-databases) | Displayed compute+DB floor $20.15, already over $20 before resolving storage billing/taxes. Do not select under this cap |

Render's pricing page was fetched but its returned text omitted plan amounts; current Render totals are **UNVERIFIED**, not filled in from memory. Managed free tiers could help, but durability, suspension, quotas and overage exposure require a separate verified comparison. A cheap development database is not a substitute for a durable review-history service.

### How traffic changes cost

Cost model: `fixed hosting + backup/storage + billable transfer + map requests + model/tool calls`. Static frontend requests need no Python or SQL work per visitor. Illustrative, not measured: a 10 MB cold-load export at 1,000 / 10,000 / 100,000 visits transfers about 10 / 100 / 1,000 GB before caching; map tiles are additional. Measure actual compressed assets and cold/warm visits before forecasting costs. The $12 VPS row includes 2,000 GiB transfer; CPU/RAM may become a limit sooner. No supported concurrent-user number has been measured.

App Platform lists transfer overages at $0.02/GiB; its 50 GiB allowance is not the VPS allowance. Cloudflare's static-request pricing does not pay a third-party map provider's bill. Set application-side concurrency/data limits and budget alerts; an alert is not a hard spending cap. Avoid automatic paid scaling under this budget.

**Maps are the main unresolved public-deployment dependency.** [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/) requires attribution, appropriate caching and forbids bulk/offline download; the standard service has no SLA and may block problematic usage. “Keyless” does not mean unlimited hosted capacity. Esri's [master agreement page](https://www.esri.com/en-us/legal/terms/master-agreement?rsource=https://www.esri.com/en-us/legal/terms/full-master-agreement) was fetched, but public use of the exact unauthenticated World Imagery endpoint was not established. Its public-traffic entitlement/cost remains **UNVERIFIED**. Until settled, offer a self-contained Natural Earth globe/map with visible credits; satellite imagery is optional, not a release blocker.

No hosted chat means $0 hosted model charges. Local inference has no paid API charges but consumes the user's hardware/electricity and must pass H. BYOK transfers provider billing to the key owner; it is not zero total cost. Keep keys in the local backend/OS secret storage, not an exported bundle or public-site browser storage. Do not add public BYOK until its threat model, provider terms and abuse controls are designed.

Identity: anonymous static viewing needs no Nexus account. Maintainers need hosting/git access, separate from visitors. A single-user local install can retain self-labelled reviewers while clearly disclosing no verified identity; multi-user hosted writing requires authenticated principals, authorization, session/CSRF protection and audit identity before enabling write endpoints. Current loopback header/origin checks are not public authentication. A static export must contain no write capability, private raw snapshots, keys or internal logs.

Community contributions can use git patches/PRs: declarative pack manifest, new source/claim candidates, licence metadata and evaluation fixtures. CI validates schema/rights/references; maintainer review builds an immutable release. A contributor's git attribution is provenance, not evidence truth or the local user's acceptance. Installing a release never overwrites local review history.

## Evidence from the repo

`technical-stack.md` already sketches the static adapter and local key storage. `backend/README.md` and `main.py` describe local-only review protections. `storage/backup.py` backs up PostgreSQL; future source objects need their own consistent backup manifest. The repository has no deployed hosting configuration verified by this review. The 44 claims are tiny; geometry, raw documents and globe assets will dominate payload before the claim table does.

## Options considered

| Option | Best use |
|---|---|
| Static public / local authoring | Lowest running cost and simplest identity boundary |
| Single VPS | Public dynamic reads or a deliberately authenticated editor after testing |
| Managed stack | Lower operations burden, but this checked configuration misses the cap |

## Migration and compatibility impact

No changes to append-only history or 44 claim IDs. Export a coherent pinned evidence/geometry/tour release, resolving A aliases and keeping candidate/accepted labels. Do not export `current_claims()` blindly: it can contain unaccepted/rejected candidate states. The additive generator is unrelated to export and remains unchanged; a static export is a derivative with a manifest, not a new accepted version. VPS migration would require tested DB-plus-object restore, not just copying fixtures. Nothing is deployed by this review.

## Risks

Unexpected tile/model spend, tax/currency margin, operational time and accidental public write exposure. VM snapshots alone may not meet application-consistent restore needs. Desktop-first Cesium performance is a browser concern even if hosting is free.

## Effort

**S–M** static export; **M** VPS operations; larger for public writing. Depends on J redistribution clearance and F release pinning; A–D correctness precedes export.

## Decisions needed from the user

Use static public viewing with local authoring first? Is the $10–20 cap USD or CAD, including tax/domain/backups?

## Unverified or not checked

No hosting benchmark, account quote, deployment, map entitlement decision or model-provider pricing performed. Domain, tax, exchange rates, extra managed storage treatment and public Esri costs are **UNVERIFIED**. Prices must be rechecked before purchase.
