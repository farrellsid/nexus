import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeFeedType, isVideoFeedType } from './cctvTypes.js';

test('camera aliases remain separate from player support decisions', () => {
  for (const [input, expected] of [
    ['JPEG', 'image'],
    ['mjpg', 'mjpeg'],
    ['video', 'mp4'],
    ['stream', 'hls'],
    ['', 'image'],
    ['other', 'other'],
  ]) {
    assert.equal(normalizeFeedType(input), expected);
  }
  assert.equal(isVideoFeedType('mjpeg'), false);
  assert.equal(isVideoFeedType('hls'), true);
});
