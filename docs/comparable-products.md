# Comparable supply-chain and trade products

Research date: 2026-09-15. Public documentation review; no authenticated product trials, integration tests, pricing quotes or independently validated coverage claims. Recommendations below are proposals, not changes to accepted implementation scope.

## What the market establishes

Commercial supply-chain visualization is an established category, but products answer different questions. Supplier networks describe relationships; shipment visibility describes movements; aggregate trade statistics describe country/product totals. Nexus should connect these views through explicit evidence and identifiers without treating them as interchangeable.

## Products and transferable patterns

| Product | Documented purpose and input | Useful lesson for Nexus |
| --- | --- | --- |
| Altana | Value-chain investigation combining public/commercial records, proprietary logistics and customer data. Its canvas distinguishes suggested suppliers from verified network entries. | Expand a focused network gradually; group entities; inspect relationship evidence; visibly distinguish inferred connections. |
| S&P Global Panjiva | Company and shipment investigation. Company profiles combine supplier/customer activity, trading partners, shipment records, events and research. | A company detail page should connect graph exploration to dated records and reporting. |
| Sourcemap | Supply-chain mapping and supplier data collection, including supplier-attested information. | Record who supplied a claim. Disclosure is a distinct evidence origin, not automatic independent corroboration. |
| Everstream Discover | Sub-tier discovery and risk visibility; vendor describes AI and proprietary trade data for finding upstream relationships. | Attach relevant developments to known entities and relationships, while preserving uncertainty about exposure and consequences. |
| project44 | Operational visibility across ocean, road, air and rail; carrier connections include telematics and API/EDI. | Use shipment milestones and data-freshness indicators when actual shipment observations exist. |
| Observatory of Economic Complexity (OEC) | Country/product trade visualization; a public website repository provides an additional implementation reference. | Use quantitative trade views for economic context. National totals cannot fill missing company-to-company quantities. |

### Primary sources

- Altana canvas: https://docs.altana.ai/workspaces/the-canvas/article.html
- Altana network statuses: https://docs.altana.ai/catalog/verified-and-suggested-network/article.html
- Altana data strategy: https://altana.ai/platform
- Panjiva company-profile tutorial: https://pages.marketintelligence.spglobal.com/Panjiva-Jump-Start-Company-Profiles.html
- Panjiva product: https://www.spglobal.com/market-intelligence/en/solutions/products/panjiva-supply-chain-intelligence
- Sourcemap mapping: https://www.sourcemap.com/technology/supply-chain-mapping
- Sourcemap disclosure: https://www.sourcemap.com/solutions/product-transparency-disclosure
- Everstream Discover: https://www.everstream.ai/platform/platform-sub-tier-visibility/
- Everstream high-tech use case: https://www.everstream.ai/industries/high-tech-supply-chain/
- project44 visibility and connection options: https://www.project44.com/platform/visibility/
- OEC trade visualization: https://oec.world/en/visualize/tree_map/hs92/import/all/show/all/undefined
- OEC website repository: https://github.com/Datawheel/oec-website

## Strongest interaction reference: Altana

Its public canvas documentation describes tier/location aggregation, upstream exploration, relationship transaction panels, date filters, and isolating paths between selected entities. Suggested suppliers have distinct styling and can be hidden. Facility matching constrains availability of transaction details. These are documented behaviors, not results of our own usability testing.

For Nexus, begin with a selected company, facility or material and a small surrounding network. Selecting a connection should reveal what is asserted, its product/time scope, sources and unknowns. Generic process requirements, commercial agreements and individual shipments need different relationship types. Do not copy a vendor's meaning of verified into Nexus without defining our own review semantics.

## Data access is part of the product

Altana explicitly describes combining proprietary logistics, public/commercial records and customer data. Sourcemap's collection workflow and project44's carrier integrations demonstrate why an attractive map does not imply an equivalent open dataset exists. Vendor APIs are not automatically free or redistributable; subscription, export, retention and demo rights require separate assessment before integration. No commercial API has been selected or purchased.

Public documentation can reveal workflows and stated data strategy, but it does not establish the vendors' internal database, rendering library, model quality or actual completeness. OEC's public repository can be studied separately; its presence does not establish that it matches the current production deployment or that every associated dataset has the same licence. No source-code or licence audit was performed here.

## Proposed Nexus design implications

1. Evidence inspection belongs in the first workbench: entity selection, relationship selection, source/date/status display and explicit unknowns.
2. Start graph exploration locally around one entity; add grouping and path isolation as real fixture complexity warrants them.
3. Give company relationships, shipments and country/product statistics separate views and types. A graph connection does not prove batch provenance.
4. Add news as dated, sourced events associated with entities. Exposure is a hypothesis unless the relevant dependency is documented; a headline is not proof of output loss.
5. Attach measurements to their correct subject, period, unit and production stage. Do not distribute a company's total production across outgoing edges without supporting allocation data.
6. Preserve graph/map shared selection for the later geographic trial. These products do not establish a need to build the globe first or change the accepted stack.

## Bounded next design exercise

Use the existing Kamoa -> Trafigura -> Aurubis -> Prysmian pilot for a workbench mockup: select a node, inspect a relationship, see dated evidence, and switch between the relationship view and a quantitative facts panel. Keep unavailable shipment quantities visibly unknown. This is a proposed next exercise, not implementation performed by this research.

A useful portfolio claim would be that Nexus helps a learner understand and audit one industrial chain, including where knowledge ends. Matching commercial global coverage is not a sensible MVP acceptance criterion. The differentiation is a proposed learning-oriented workflow, not a claim that competitors lack explanatory AI or news features.

## Open Sourcemap follow-up — 2026-09-21

Public browser inspection confirmed https://open.sourcemap.com/ is accessible without login, with industry categories, contributed maps, some OFFICIAL-labelled entries, and free registration advertised for map creation. This is distinct from Sourcemap's commercial product reviewed above. Sample inspected: https://open.sourcemap.com/maps/5910cfeab9b82abd5866a3b9 (Tantalum). Its page displayed an author, 'Updated ... 6 years ago', an embed control, and a Nodes and Links view at /things showing 90 entries. The actual entries were not exposed in the accessibility text, so their contents and sourcing were not validated. The sample appeared under LATEST on the homepage despite that update age: do not use placement to infer freshness. No documented current public export/API or data reuse licence was established by this bounded check. Useful as a visualization reference and discovery lead; not yet a verified ingestion source or current supply-chain database. No account created or data imported.
