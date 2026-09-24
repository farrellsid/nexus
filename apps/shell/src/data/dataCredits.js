import * as Cesium from 'cesium';

/**
 * Attribution for the data the shell shows, registered into Cesium's credit display.
 *
 * Imagery credits itself (Esri and OpenStreetMap, see src/maps/imagery.js). This list covers the
 * rest: the terrain, the geoid and the oil fixture. The credits are registered once at start-up as
 * static credits with showOnScreen=false, so they live in the expandable "Data attribution"
 * popover rather than the on-globe line. Add a credit here in the same change that adds a source.
 *
 * @type {{ key: string, html: string }[]}
 */
export const DATA_CREDITS = [
  {
    key: 'reearth-terrain',
    html:
      'Terrain: <a href="https://reearth.io" target="_blank" rel="noopener">Re:Earth</a> ' +
      'quantized mesh built from Mapterhorn elevation data (CC BY 4.0)',
  },
  {
    key: 'egm96',
    html:
      'Altitude above mean sea level: EGM96 geoid model, ' +
      'US National Geospatial-Intelligence Agency',
  },
  {
    key: 'oil-fixture-wikidata',
    html:
      'Oil place anchors: coordinates from ' +
      '<a href="https://www.wikidata.org" target="_blank" rel="noopener">Wikidata</a> (CC0). ' +
      'Each anchor is a label point, not a boundary, route or vessel position',
  },
  {
    key: 'oil-fixture-eia',
    html:
      'Oil-system context: ' +
      '<a href="https://www.eia.gov" target="_blank" rel="noopener">US Energy Information Administration</a> ' +
      '(US Government work, public domain)',
  },
];

/**
 * Register every data credit into the viewer's credit display.
 * @param {Cesium.Viewer} viewer — the initialized Cesium viewer
 */
export function registerDataCredits(viewer, credits = DATA_CREDITS) {
  const creditDisplay = viewer?.creditDisplay;
  if (!creditDisplay || typeof creditDisplay.addStaticCredit !== 'function') {
    return;
  }
  for (const { html } of credits) {
    creditDisplay.addStaticCredit(new Cesium.Credit(html, false));
  }
}
