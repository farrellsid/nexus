import test from 'node:test';
import assert from 'node:assert/strict';
import * as Cesium from 'cesium';
import { createDefaultMapSources } from './defaultSources.js';
import { createKeylessTerrain } from './terrain.js';

test('the default sources are the two keyless imagery stacks over keyless terrain', async () => {
  const originalTerrain = Cesium.CesiumTerrainProvider.fromUrl;
  const calls = [];
  Cesium.CesiumTerrainProvider.fromUrl = async (url) => {
    calls.push(url);
    return { url };
  };
  try {
    const registry = createDefaultMapSources();
    assert.deepEqual(
      registry.sources.map(({ descriptor }) => descriptor.id),
      ['esri-imagery', 'osm'],
    );
    assert.equal(registry.defaultId, 'esri-imagery');
    for (const source of registry.sources) {
      assert.equal(source.available, true);
      assert.equal(source.terrain.id, 'keyless');
      assert.equal(source.terrain.create, createKeylessTerrain);
    }
    await registry.sources[0].terrain.create();
    assert.deepEqual(calls, [
      'https://terrain.reearth.land/cesium-mesh/ellipsoid',
    ]);
  } finally {
    Cesium.CesiumTerrainProvider.fromUrl = originalTerrain;
  }
});

test('Esri falls back to OSM when it cannot be built or its tiles fail', () => {
  const esri = createDefaultMapSources().sources.find(
    ({ descriptor }) => descriptor.id === 'esri-imagery',
  );
  assert.equal(esri.constructionFallback.id, 'osm');
  assert.equal(esri.tileFailureFallback.id, 'osm');
  assert.equal(esri.tileFailureFallback.threshold, 2);
});

test('terrain falls back to the flat ellipsoid when the keyless service is unavailable', async () => {
  const originalTerrain = Cesium.CesiumTerrainProvider.fromUrl;
  const originalWarn = console.warn;
  Cesium.CesiumTerrainProvider.fromUrl = async () => {
    throw new Error('offline');
  };
  console.warn = () => {};
  try {
    const { provider } = await createKeylessTerrain();
    assert.ok(provider instanceof Cesium.EllipsoidTerrainProvider);
  } finally {
    Cesium.CesiumTerrainProvider.fromUrl = originalTerrain;
    console.warn = originalWarn;
  }
});
