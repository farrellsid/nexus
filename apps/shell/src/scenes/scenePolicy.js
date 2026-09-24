// src/scenes/scenePolicy.js — pure decisions for cinematic scene playback.
//
// The scene director was written when the app shipped four data layers, and its
// shot recipes (src/scenes/recipes.js) still declare exactly those four:
// flights, satellites, earthquakes, traffic. The registry has since grown to
// sixteen. The original reconcile walked the LIVE registry and forced every
// layer absent from the shot to off, so a recipe that never had an opinion
// about CCTV, vessels, fires, radio, dams or datacenters silently tore
// them down — and nothing puts them back, because playback has no restore pass.
//
// A shot's layer map is an assertion about the layers it NAMES, not a claim of
// authority over every layer that will ever exist. Recipes already spell out
// the layers they want OFF (see 'thermal-threats', which declares
// flights/satellites/traffic false), so honouring only the declared keys keeps
// every authored intent intact while leaving undeclared layers alone.
//
// Operator-captured shots are unaffected: captureShot() snapshots the whole
// registry (director._captureLayerStates), so those shots declare all sixteen
// keys and still reconcile in full.

/**
 * Build the ordered layer reconcile plan for one shot.
 *
 * Only layers the shot explicitly declares are touched. Declared layers that
 * are no longer registered (an imported or long-stored project referencing a
 * retired layer) are skipped rather than pushed at the data manager.
 *
 * @param {Object.<string, { enabled: boolean, params?: Object }>} targetStates
 *   The shot's normalized layer map.
 * @param {Set<string>|Iterable<string>} [registeredIds] Layer ids the data
 *   manager currently knows about. Omit to skip the registration filter.
 * @returns {Array<{ id: string, enabled: boolean, params: Object|undefined }>}
 */
export function sceneLayerPlan(targetStates, registeredIds) {
  const known =
    registeredIds instanceof Set
      ? registeredIds
      : registeredIds
        ? new Set(registeredIds)
        : null;

  const plan = [];
  for (const [id, target] of Object.entries(targetStates || {})) {
    if (known && !known.has(id)) continue;
    plan.push({
      id,
      enabled: !!(target && target.enabled),
      params: target && target.params ? target.params : undefined,
    });
  }
  return plan;
}
