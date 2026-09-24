# F. Guided tours

## Recommendation

Curate one tour per industry and publish immutable tour releases.
Pin evidence and measurement versions; resolve numbers through validated slots.
Generation may draft chapter structure/prose, never invent factual slots or select unreviewed substitutions.
Superseded or withdrawn evidence flags the chapter for review; it does not silently update published narration.
Drive mouse, tour and later chat through the same allowlisted read/display actions; advance on Next.

### Proposed chapter contract

```json
{
  "id": "oil-movement",
  "chapter_version": 1,
  "industry_id": "oil",
  "title": "How it moves",
  "stance": "evidence_summary",
  "blocks": [
    {"type": "text", "text": "Reported Hormuz flow for the selected quarter:"},
    {"type": "measurement_slot", "binding": "hormuz_flow"}
  ],
  "claim_bindings": [{"legacy_claim_id": "O-C02", "version_ref": null}],
  "measurement_bindings": [{"name": "hormuz_flow", "version_ref": null}],
  "scene": {
    "camera": {"mode": "fit_geometry", "legacy_geometry_id": "O-G01"},
    "layers": ["sourced_anchors"],
    "highlight_entity_ids": ["oil-hormuz"]
  },
  "advance": "next",
  "status": "draft_unbound"
}
```

This is an illustrative **unpublishable** draft using real legacy IDs. Null version bindings must block release. A complete binding contains release ID, immutable claim/measurement version, source passage IDs, allowed formatting and period/unit/status display. No invented revision number is supplied. A candidate can be included only under a declared candidate-brief policy with its actual proposal/hash reference and a visible candidate label; it must not masquerade as accepted.

`tour_release(id, industry_id, version, evidence_release_id, geometry_release_id, chapter_version_ids, manifest_hash, published_at)`; `chapter_version(id, chapter_id, prior_version_id?, payload, author, recorded_at)`; append-only `chapter_review(id, chapter_version_id, reviewer, decision, reason, recorded_at)`; dependency index from each chapter to pinned records. A dependency change creates `chapter_review_needed(reason, old_ref, replacement_ref?)`. Existing release continues to reproduce its content with an outdated-evidence banner; withdrawal of essential evidence can hide that chapter from default navigation pending a new release.

### Complete reusable chapter template

| Chapter | Required evidence / display | Interpretation boundary |
|---|---|---|
| What it is and what it is for | Material forms, process/use relationships, glossary and cited process diagram | Explanatory ordering is editorial; physical relationships need sources |
| Current state | Selected measures with period, unit, status, vintage and gaps | “Current” is an explicit cutoff, not the machine clock |
| Where it comes from | Significant producing countries, assets and input materials; sourced significance or curated display tier | Selection is editorial; production shares require denominators |
| How it moves | Chokepoints, transport modes, supported networks and limitations | Modelled alternative paths explicitly labelled; no implied cargo tracing |
| Main players and countries | Roles, dated contracts/policy actors; versioned entity links | Corporate presence is not market dominance |
| History | Sourced dated milestones and longer-term comparisons where comparable | Narrative synthesis labelled; avoid unsupported continuity across gaps |
| Geopolitics | Reported actions, attributed analysis, competing explanations | Causal interpretation separate from observed chronology |
| Outlook | Issuer, issue date, target horizon and assumptions for each forecast/scenario | Never shown as actual future outcomes |
| Where a student might fit | Curated skill/task pathways tied to the described industry activities | Editorial learning suggestions; current jobs/eligibility require separate fresh sources |

Every chapter supports “What supports this?”, “What is missing?” and a plain-text fallback. Optional chapters with insufficient evidence display a coverage gap rather than generated filler. The oil pack does not currently support complete history or student-opportunity coverage.

Actions: `select_entity(id)`, `focus_geometry(version_ref, camera_preset_id)`, `set_layers(allowlisted_ids)`, `highlight_measurements(version_refs)`, `show_evidence(version_refs)`, `set_period(period_ref)`. Validate against the active release; reject unknown IDs and unresolved geometry. Camera height/heading are presentation settings, not observed feature coordinates. Enter saves prior view state; exit restores it; Next cancels outstanding camera transitions before applying the next scene. Reduce-motion and skip-camera modes retain content access. A render failure cannot alter claims or trigger acceptance commands.

## Evidence from the repo

`ReadingPrompt` in `investigation.py` contains authored answer text and claim IDs, with no chapters, slots or version bindings. `GeoStop` has camera-target coordinates but no scene state. `Workbench.tsx` displays `expected_answer` directly. `frontend-rebuild.md` records the shared action API, Next navigation and curated tours as user decisions. Reference `src/scenes/director.js`, `cameraMotion.js`, `sharing.js` and `sharelink.js` provide reuse entry points; copying default scene packs would also pull unrelated event content (J).

## Options considered

| Option | Assessment |
|---|---|
| Fully regenerate tours on each refresh | Reject: silently changes claims and interpretation |
| Handwrite every number in prose | Drifts and duplicates facts |
| Curated chapters + pinned slots + review queue | Recommended; repeatable and updateable |

## Migration and compatibility impact

No mutation of the 44 claims or append-only review rows. Add immutable chapter/release tables and dependencies; slots consume A–D measurement versions. Keep legacy reading guides accessible, but treat their answers as authored assertions requiring review rather than proven evaluations. The additive generator cannot manage chapter-only changes; use a separate declarative release import. Preserve accepted versions and old tours even after newer chapters are approved. Regenerate contracts only during implementation.

## Risks

Slotting numbers does not make surrounding causal prose true. Automatically swapping a forecast for an observation can change an argument. Sharing camera state must not share secrets or authorize record mutations; pin the release and validate decoded URLs.

## Effort

**M**, depends on A–D and E for scenes; H gates factual blocks, I supports updates and J clears assets.

## Decisions needed from the user

Allow visibly labelled candidate evidence in curated draft tours, while reserving published accepted tours for reviewed versions?

## Unverified or not checked

No tour schema implemented or rendered. The reference director was located, not ported or fully behavior-tested. No new industry history, career claims or forecast facts researched.
