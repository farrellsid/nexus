# Third-party notices

## God's Eye View

Parts of the Cesium viewer configuration and keyless map-source design in `apps/web/src/workbench/CesiumGeographyMap.tsx` are adapted from God's Eye View: <https://github.com/bilawalsidhu/gods-eye-view>.

MIT License

Copyright (c) 2026 Bilawal Sidhu

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

God's Eye View's third-party data and assets are outside its MIT grant. Nexus does not copy those bundled datasets or models in this integration.

## Map and renderer services

- CesiumJS is licensed under Apache-2.0. See <https://github.com/CesiumGS/cesium>.
- The default imagery layer is Esri World Imagery. Its on-map provider credit is retained.
- The fallback tile layer is OpenStreetMap. Its on-map `© OpenStreetMap contributors` credit is retained.
- The local no-WebGL fallback uses Natural Earth land geometry distributed by `world-atlas`. Natural Earth places its map data in the public domain.

## Nexus shell (`apps/shell`)

`apps/shell` is a stripped fork of God's Eye View at commit `f01b6a5`, under the MIT notice above (`apps/shell/LICENSE` is the upstream licence file). Its code, stylesheets and interface layout are adapted; `apps/shell/UPSTREAM.md` records every removal and change. Upstream's bundled datasets, 3D models, event media, logo and unattributed icons are not part of the fork: they were removed or never imported, and the logo and interface icons that ship were drawn for Nexus.

Other material the shell build contains:

- **CesiumJS** and `@cesium/engine`, Apache-2.0, <https://github.com/CesiumGS/cesium>. Its `ThirdParty.json` ships with the build in `cesium/`.
- **Inter**, SIL Open Font License 1.1, copyright The Inter Project Authors, <https://github.com/rsms/inter>. **JetBrains Mono**, SIL Open Font License 1.1, copyright The JetBrains Mono Project Authors, <https://github.com/JetBrains/JetBrainsMono>. **Material Symbols Outlined** (a subset limited to the glyphs the shell names), Apache-2.0, copyright Google, <https://github.com/google/material-design-icons>. The fonts are self-hosted from `apps/shell/public/fonts`; `manifest.json` there holds their hashes. The full licence texts still have to be added to the build before anything is published; the manifests record that this has not been done.
- **d3-geo**, **topojson-client** and **world-atlas**, ISC, used for the flat fallback map. The land geometry is Natural Earth, public domain.
- **egm96-universal**, MIT, embedding the EGM96 geoid grid published by the US National Geospatial-Intelligence Agency.
- Esri World Imagery and OpenStreetMap tiles and the Re:Earth terrain service are used as remote services during local development, with their on-map credits. They are recorded as unverified in `licences/components.json` and are not cleared for a public build.
