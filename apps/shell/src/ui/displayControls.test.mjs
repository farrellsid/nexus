import assert from 'node:assert/strict';
import test from 'node:test';
import { bindDisplayControls } from './displayControls.js';

function element(value = '') {
  const el = new EventTarget();
  el.value = value;
  el.dataset = {};
  return el;
}

test('controls read current values without preventing native input behavior', () => {
  const bloomSlider = element('24');
  const hudLayout = element('tactical');
  const calls = [];
  const control = bindDisplayControls({
    elements: { bloomSlider, hudLayout },
    actions: {
      setBloomIntensity: (value) => calls.push(value),
      setHudLayout: (value) => calls.push(value),
    },
  });
  const event = new Event('input', { cancelable: true });
  bloomSlider.dispatchEvent(event);
  bloomSlider.value = '37';
  bloomSlider.dispatchEvent(new Event('input'));
  hudLayout.value = 'minimal';
  hudLayout.dispatchEvent(new Event('change'));
  assert.deepEqual(calls, [24, 37, 'minimal']);
  assert.equal(event.defaultPrevented, false);
  control.destroy();
});

test('destroyed and replaced controls cannot issue stale actions', () => {
  const bloomButton = element();
  let oldCalls = 0;
  let newCalls = 0;
  const first = bindDisplayControls({
    elements: { bloomButton },
    actions: { toggleBloom: () => oldCalls++ },
  });
  bloomButton.dispatchEvent(new Event('click'));
  first.destroy();
  const second = bindDisplayControls({
    elements: { bloomButton },
    actions: { toggleBloom: () => newCalls++ },
  });
  first.destroy();
  bloomButton.dispatchEvent(new Event('click'));
  assert.equal(oldCalls, 1);
  assert.equal(newCalls, 1);
  second.destroy();
  bloomButton.dispatchEvent(new Event('click'));
  assert.equal(newCalls, 1);
});

test('style choices retain their data attribute', () => {
  const style = element();
  style.dataset.style = 'thermal';
  const calls = [];
  const control = bindDisplayControls({
    elements: { styleButtons: [style] },
    actions: { setStyle: (value) => calls.push(value) },
  });
  style.dispatchEvent(new Event('click'));
  assert.deepEqual(calls, ['thermal']);
  control.destroy();
});

test('optional controls are absent safely and subscriptions stay instance-owned', () => {
  const calls = [];
  const a = element();
  const b = element();
  a.dataset.style = 'a';
  b.dataset.style = 'b';
  const one = bindDisplayControls({
    elements: { styleButtons: [null, a] },
    actions: { setStyle: (value) => calls.push(value) },
  });
  const two = bindDisplayControls({
    elements: { styleButtons: [b] },
    actions: { setStyle: (value) => calls.push(value) },
  });
  one.destroy();
  a.dispatchEvent(new Event('click'));
  b.dispatchEvent(new Event('click'));
  assert.deepEqual(calls, ['b']);
  two.destroy();
});
