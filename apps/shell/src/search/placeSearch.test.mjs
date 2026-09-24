import test from 'node:test';
import assert from 'node:assert/strict';
import { createPlaceSearch, } from './index.js';

test('one cancelled caller cannot cancel another caller of the same service', async () => {
  const controller = new AbortController();
  const service = createPlaceSearch({ providers: [{ async geocode(_query, { signal }) {
    await new Promise((resolve) => setImmediate(resolve)); signal.throwIfAborted();
    return { place: { lat: 1, lng: 2 }, answered: true };
  } }] });
  const first = service.geocode('same', { signal: controller.signal });
  const second = service.geocode('same');
  controller.abort();
  await assert.rejects(first, { name: 'AbortError' });
  assert.equal((await second).place.lat, 1);
});

test('definitive misses expire while outage outcomes are never cached', async () => {
  let now = 0, calls = 0, answered = true;
  const service = createPlaceSearch({ now: () => now, providers: [{ async geocode() { calls++; return { place: null, answered }; } }] });
  await service.geocode('miss'); await service.geocode('miss'); assert.equal(calls, 1);
  now = 30_001; answered = false;
  await service.geocode('miss'); await service.geocode('miss'); assert.equal(calls, 3);
});


test('cancellation before lookup makes no provider call', async () => {
  const controller = new AbortController();
  controller.abort();
  let calls = 0;
  const service = createPlaceSearch({ providers: [{ async geocode() { calls++; return { place: null, answered: true }; } }] });
  await assert.rejects(service.geocode('Hanoi', { signal: controller.signal }), { name: 'AbortError' });
  assert.equal(calls, 0);
});

test('service lifetime cancellation also rejects cache hits', async () => {
  const controller = new AbortController();
  const service = createPlaceSearch({
    signal: controller.signal,
    providers: [{ async geocode() { return { place: { lat: 21.03, lng: 105.85 }, answered: true }; } }],
  });
  assert.ok((await service.geocode('Hanoi')).place);
  controller.abort();
  await assert.rejects(service.geocode('Hanoi'), { name: 'AbortError' });
});
