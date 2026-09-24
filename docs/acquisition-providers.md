# Acquisition providers: sampled facts and decisions

Sampled 2026-09-24 with read-only requests: no API key, nothing stored, nothing written to a database. **No adapter exists.** This page records what the endpoints returned so that you can decide which providers to use. It does not authorise scheduled fetching, keys, new costs or model calls.

## EIA (U.S. Energy Information Administration)

| Fact | Observed |
|---|---|
| Open Data API v2 root, `https://api.eia.gov/v2/` | HTTP 403 with `API_KEY_MISSING`: "Please register for one at https://www.eia.gov/opendata/register.php". A key is required. |
| Cost | The documentation page says EIA data is "provided free of charge and should be used in compliance with our Copyrights and Reuse Policy". Registration and the API Terms of Service Agreement "help EIA monitor usage". |
| Limits stated in the docs | At most 5,000 rows per response, with a `warning` field when a request is truncated. |
| Bulk download index, `https://www.eia.gov/opendata/bulk/` | HTTP 403 ("You do not have permission to view this directory or page"). Not usable as a keyless source. |
| Formats | JSON (and XML with `out=xml`). |
| Could replace | The STEO chokepoint tables behind O-C02, O-C03, O-C16 and metrics O-M01, O-M02, O-M06; weekly stocks (O-M07, O-M09); refinery capacity (O-M08). Route names and series IDs have not been mapped. |
| Not verified | Which API routes carry the chokepoint tables. The Copyrights and Reuse Policy exceptions for third-party material. |

## JODI (Joint Organisations Data Initiative), oil

| Fact | Observed |
|---|---|
| Downloads page, `https://www.jodidata.org/oil/database/data-downloads.aspx` | HTTP 200. States that data "from January 2002 to one month-old can be downloaded, for free, in .ivt (Beyond 20/20), .csv and formats". No key. |
| Example file | `.../oil-data/annual-csv/primary/primaryyear2026.csv`: 5,542,684 bytes, `Last-Modified: Tue, 22 Sep 2026 07:18:47 GMT`, `Content-Type: application/octet-stream`. |
| Columns (first rows read with a byte-range request) | `REF_AREA, TIME_PERIOD, ENERGY_PRODUCT, FLOW_BREAKDOWN, UNIT_MEASURE, OBS_VALUE, ASSESSMENT_CODE`. Monthly, per country, per product, flow and unit (for example `CRUDEOIL`, `INDPROD`, `KBD`); missing values appear as `-` or `x`. |
| Licence or reuse terms | **Not found on the downloads page**, which shows only "© Copyright JODI 2026". The terms must be read before storing or redistributing. |
| Size limit | The default fetch cap in `app/acquisition/fetch.py` is 5,000,000 bytes, so this file needs a per-provider limit. |
| Could replace | Country-level crude production and stocks in place of prose anchors, for the countries that report. It does not cover every OPEC+ member and its values can differ from the IEA's, so it is a second source for the comparability model, not a substitute. |
| Not verified | Which of the four O-M11 countries report to JODI for August 2026. The assessment-code meanings. |

## Independent hash check of two EIA pages (roadmap M4 [A])

The pages were fetched through `scripts/acquire.py fetch --confirm` (policy `hash_only`, against a scratch copy of the database) and separately with `curl` using the same user agent and `Accept-Encoding: identity`.

| Source | Tool vs curl, raw bytes | Two curl fetches, raw bytes | Extracted text |
|---|---|---|---|
| O-S24 (EIA Today in Energy, id 67905) | equal | **not equal** (same length, 51,692 bytes) | equal in every comparison |
| O-S26 (EIA Today in Energy, id 68125) | **not equal** (same length, 53,113 bytes) | equal | equal in every comparison |

What this shows and what it does not: a raw byte hash matched in only 1 of 4 comparisons, at identical lengths, so the page carries something that varies between fetches. I did not locate the varying bytes (two later fetches were byte-identical). The extracted-text hash matched in all 4. A byte hash alone would therefore have raised false "changed" alarms on EIA pages. The verifier reports byte and text matches separately, and `matches` needs only one of them. This is two pages on one publisher on one day, not a general reproducibility claim.

## Decisions taken by the user, 2026-09-24

- **Providers:** EIA (API v2) and JODI (CSV downloads), both.
- **Local storage:** every source is `store` in `licences/source-rights.json`, for private local research use under fair use. The user's stated intent is to collect everything now and filter what may be published later, so the working assumption is that the data may not be published publicly. The object store is under `.local/objects/` (git-ignored). The release gate (`scripts/check_licences.py --mode release`) is unchanged and still withholds unverified excerpts from any public build; it is where publication is filtered.
- **Not interpreted for the user:** the assistant has not read or applied the EIA reuse policy or the JODI terms. The choice to store is the user's.
- **EIA API key:** supplied by the user and saved in `.local/eia-api-key.txt` (git-ignored). It is read only when an adapter runs. The key appeared in the chat transcript, so it should be regenerated if that transcript is ever shared. **Before any adapter is written, logged URLs must have `api_key` redacted:** `fetch_attempt.requested_url` would otherwise store it in the database.
- **Migration 010** applied to the real database on 2026-09-24 (backup `.local/backups/nexus-20260924-064804-f1f23b.dump`, recorded history unchanged).

## EIA API v2: what the key returned (2026-09-24)

The key works (HTTP 200). Top-level routes: `coal`, `crude-oil-imports`, `electricity`, `international`, `natural-gas`, `nuclear-outages`, `petroleum`, `seds`, `steo`, `densified-biomass`, `total-energy`, `aeo`, `ieo`, `co2-emissions`. `petroleum` has sub-routes `sum`, `pri`, `crd`, `pnp`, `move`, `stoc`, `cons`. `international` is country-level by product and activity, monthly, quarterly and annual. `steo` is the Short-Term Energy Outlook with a `seriesId` facet. Which route carries the World Oil Transit Chokepoints tables (behind O-C02, O-C03, O-C16 and O-M01, O-M02, O-M06) is **not verified**; the route names alone do not say, and those tables may only be published as article tables.

## GDELT (sampled 2026-09-24)

| Fact | Observed |
|---|---|
| What it is | A machine-coded database of world news: events, mentions, and a global knowledge graph (themes, entities, tone), in over 100 languages, stated to reach back to 1979 with updates every 15 minutes. |
| Access | Keyless. The DOC API returned JSON for a sample query (`"Strait of Hormuz"`, English, last 7 days, 5 records): per article `url`, `title`, `seendate`, `domain`, `language`, `sourcecountry`. The 15-minute update list (`http://data.gdeltproject.org/gdeltv2/lastupdate.txt`) points to three zipped CSVs of about 75 KB (events), 92 KB (mentions) and 3.4 MB (knowledge graph) per interval. |
| Terms (its About page) | "available for unlimited and unrestricted use for any academic, commercial, or governmental use of any kind without fee"; may be redistributed in any form, but "any use or redistribution of the data must include a citation to the GDELT Project and a link to this website". |
| What the sample showed | 5 records from one query, mostly domestic-politics and military stories that mention the strait or the war, not supply-chain data. One small sample; not a measured precision. |
| Fit for Nexus | A **discovery layer, not an evidence layer.** It can list which articles discuss a chokepoint and when, feeding candidate URLs into the acquire pipeline, and it can supply a media-attention timeline. The articles remain the evidence (each with its own publisher rights), and GDELT's machine coding of actors, locations and tone is error-prone and repeats syndicated stories. It should never source a figure. |
| Epistemic handling | Anything derived from GDELT is `reported` by a publisher and machine-coded by GDELT, never `observed`; its records need a human-reviewed passage before becoming a claim. |
| Not verified | Rate limits (none read; the DOC API should be queried sparingly), query recall and precision for oil topics, coverage of the sources the packs use. |

## Adapters built (2026-09-24)

`backend/app/acquisition/providers/` holds pure parsers and no I/O: `eia.py` (build a keyed request URL and parse a page; an error body raises, a truncation warning is surfaced, values keep their original text), `jodi.py` (parse the CSV; `-` and `x` stay flags and never become zero), `compare.py` (exact scale changes only: thousand barrels, percent, barrels per calendar day, thousand barrels per day; an unlisted pair such as mass to volume raises `UnitError`) and `crosscheck.py`. **Key redaction** is in `policy.py` and applied inside `fetch`: `api_key`, `apikey`, `key`, `token`, `access_token`, `auth`, `password` and `secret` values are replaced in every logged URL, redirect chain and error message, while the real request still carries the key. The EIA response does not echo the key (checked), and a body containing a known secret is never stored. After a real run I searched 166 repository files, the five stored objects and the database for the key and found it nowhere.

## Cross-check of the oil pack against structured data (2026-09-24)

`scripts/crosscheck.py --confirm` made 4 EIA requests and 1 JODI download once each and compared the pack's metric values with the providers' numbers (report: `docs/crosscheck-report.md`; request hashes in `.local/crosscheck-manifest.json`; response bytes in `.local/objects/`).

| Pack metric | Provider series | Result |
|---|---|---|
| O-M07 U.S. commercial crude stocks, 3 weeks | EIA `petroleum/stoc/wstk`, `WCESTUS1` | 3 of 3 equal at the pack's precision (412,134 kbbl vs 412.1; 411,675 vs 411.7; 423,429 vs 423.4) |
| O-M09 refinery utilization, 2 weeks | EIA `petroleum/pnp/wiup`, `WPULEUS3` | 2 of 2 equal (96.1, 96.8) |
| O-M08 operable distillation capacity, 2 years | EIA `petroleum/pnp/cap1`, `8_NA_8D0_NUS_4` | 2 of 2 equal (18,423,493 and 18,160,493 b/cd vs 18.4 and 18.2) |
| O-M11 OPEC+ August 2026 production, 4 countries | JODI primary CSV; EIA `international` | **8 of 8 no observation**: JODI's latest month is 2026-07 and EIA's is 2026-06 |

Raw counts: 7 equal at pack precision, 8 no observation, 0 differing. This checks that the pack's numbers agree with the providers' own numbers; it does not show the pack cited them, and it says nothing about O-M11's August figures. Other findings from the same data:

- **JODI does not carry Iraq, Russia or Iran crude production for any month of 2026.** Every row is `-` with assessment code 3. Saudi Arabia reports (July 2026: 8,135 kb/d, assessment 1), so JODI can be a second source for Saudi Arabia only, and for a month the IEA figure does not cover.
- **JODI's 2026 file is 5.5 MB** (134,400 rows, 96 countries, seven months), above the default fetch cap; the script raises the cap per request.
- **EIA's international crude production** (crude including lease condensate, thousand b/d) for April 2026 was Iran 3,730, Iraq 1,420, Russia 9,827 and Saudi Arabia 6,600, against the IEA's August values in the pack (Iran 2.16, Iraq 3.86, Russia 8.36, Saudi Arabia 5.97 million b/d). Different months and providers; not comparable, and a reminder of how large the differences are.
- These provider series are not `evidence_sources` records, so the cross-check writes a manifest rather than logging attempts to the database. Whether to register them as sources is open (see below).

## Survey of other sources (2026-09-24)

Requests came from this machine with a browser-like user agent and no keys. "Reachable" means an HTTP 200 for the page, not that the data was verified.

| Source | What I found | Fit and limits |
|---|---|---|
| OPEC Monthly Oil Market Report | HTTP 403 to a scripted request (bot protection). Not verified. | Monthly supply, demand, stocks and forecasts with Excel appendix tables. Needs a browser-like fetch or a manual download; keep reported, estimated and forecast values distinct. |
| Energy Institute Statistical Review | HTTP 403 to a scripted request. The user's note says the download page asks for an email. | Annual historical context, not current months. Manual download. |
| IEA Oil Market Report (September 2026) | Page reachable; the summary is public and the page mentions login and subscription. Already cited (O-S20, O-S23). | Full data is subscription-dependent; nothing beyond what the pack retains can be fetched. |
| India PPAC | Reachable. Already cited (O-S19). | Imports, production, refining and consumption, but much is in PDFs; provisional figures and fiscal years need care. |
| Statistics Canada, table 25-10-0081-01 | **Best structured candidate after EIA and JODI.** A keyless CSV zip (1.6 MB) with 136,890 rows, latest month 2026-06. Columns: `REF_DATE, GEO, Supply and disposition, Products, UOM, SCALAR_FACTOR, VALUE, STATUS, SYMBOL, ...`. | Petroleum products by supply and disposition, by province, monthly. Retain product definitions, scalar factors and statistical flags. Whether crude oil rows are included was not checked. |
| Norwegian Offshore Directorate (Sodir) monthly by field | The page is reachable; no export link or licence text appeared in its static HTML. | Field-level production is valuable for tying geography to actual output. The data is probably served by script from another endpoint; not verified. Norway-specific; oil, gas, NGL and condensate are separate measures. |
| Global Energy Monitor oil infrastructure tracker | Reachable; data is offered through a `/download-data` request form; no licence text on the page. | Pipeline locations and status; some routes are approximated from endpoints. Relevant to the geometry pilot (M7). |
| Brazil ANP open data | Reachable, in Portuguese; lists datasets including production by well and processing; no direct CSV link in the static HTML (an accordion). | A large producer with open data; the dataset endpoints still need to be found. |
| UK NSTA | Reachable ("Data and insights"). | Not examined further. |
| Saudi GASTAT, Kazakhstan, Kuwait, Russia Minenergo, Canada CER | Reachable (Arabic, Russian or English pages). | Homepages only; no oil-production dataset located. |
| Mexico CNH | Returned a "Challenge Validation" page (bot check). | Not fetchable by script. |
| UAE FCSC | HTTP 403. | Not fetchable by script. |
| GDELT | See the section above. | Discovery layer, not evidence. |

## Does China release data like this? (asked by the user, 2026-09-24)

**Yes, in principle, and the pack already uses one channel.** O-C08 and O-S06 come from the National Bureau of Statistics (NBS): a monthly release of national energy production, including crude oil output and crude processing volume by enterprises above a designated size. The release URL carries the date 2026-07-17 for June data, so the lag is about two weeks. What I could and could not check:

- **NBS pages could not be reached from this machine** (`URLError` for the English site, the press-release list and the data portal, the same failure that left O-S06 unverifiable earlier). It may work from your browser or network. I cannot say whether there is a machine-readable feed; NBS also has a data query portal, not verified here.
- **The customs administration (GACC)** is the other official source: monthly crude import volume and value, with more detailed tables by origin published later. Its English homepage is reachable; its statistics query site returned HTTP 412 to a script, so it needs a browser-like adapter or manual export. This paragraph rests on general knowledge, not on data fetched here.
- **The National Energy Administration** site is reachable (Chinese only); policy and capacity announcements, not a monthly series that I found.
- **Company reports** (CNPC, Sinopec, CNOOC) are further sources, not sampled.
- **Limits:** mostly Chinese-language, published as releases and tables rather than APIs, with a defined enterprise scope (O-C08's caveat) and no published stocks series that I know of (unverified).

**Other large producers' governments**, from what was reachable: the U.S. (EIA, done), Canada (StatCan CSV, ready to adapt), Norway (Sodir, endpoint to find), Brazil (ANP, endpoints to find), the UK (NSTA). Saudi Arabia, Russia, Iraq and Iran mostly reach the world through JODI and secondary sources; JODI carries Saudi Arabia but none of Iraq, Russia or Iran for 2026. Government portals for Russia and the Gulf states either were not reachable or exposed no dataset I could find; that is a finding about this survey, not about whether such data exist.

## Decisions still open

1. **Register provider series as sources?** The cross-check shows seven pack values agree with EIA. To make that provenance part of the evidence (measurement-level source bindings, logged attempts, a baseline for each series), each provider series would become an `evidence_sources` record through a reviewed release. Do that for the seven verified series first?
2. **Next adapters:** Statistics Canada (ready), then Sodir and ANP once their endpoints are found; a browser-like fetch for OPEC and the Energy Institute; and a manual-download path for GEM.
3. **GDELT:** use it as a discovery tool only, after the adapters above?
4. **China:** try NBS and customs from your network first (an adapter I cannot test from here), or start with manual exports?

## Earlier decisions for reference (roadmap M4 [U])

1. **Which providers?** EIA API v2 (needs you to register a free key and accept its Terms of Service) and JODI CSV downloads (no key; terms to be read first). Or neither for now. *Answered: both.*
2. **What may be stored locally**, per publisher. Every source currently defaults to `hash_only` in `licences/source-rights.json`: the hash, size, headers and outcome are kept and the bytes are discarded. `store` keeps the bytes under `.local/objects/` (git-ignored, never published). Which publishers, if any, become `store`? A reasonable start is EIA (public data with a reuse policy) once you have read that policy; JODI after its terms are read; company sources not until audited.
3. **Per-provider size limits**, for example a larger cap for the JODI CSV files.
4. **Read the terms** yourself (EIA Copyrights and Reuse Policy and API Terms of Service; JODI terms of use) before any `store` decision. I have not read or interpreted them for you.
5. **Approve applying migration 010** to the real database.
