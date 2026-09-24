import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DATA_CREDITS } from './dataCredits.js';

test('every credit carries a unique key and some markup to render', () => {
  const keys = DATA_CREDITS.map((entry) => entry.key);
  assert.equal(
    new Set(keys).size,
    keys.length,
    'a duplicate key would silently shadow one provider’s credit',
  );
  for (const entry of DATA_CREDITS) {
    assert.ok(entry.key, 'a credit without a key cannot be registered');
    assert.ok(
      entry.html && entry.html.trim().length > 0,
      `credit ${entry.key} has nothing to show`,
    );
  }
});

test('the oil fixture credits its coordinate source and says its anchors are not routes', () => {
  const credit = DATA_CREDITS.find(
    (entry) => entry.key === 'oil-fixture-wikidata',
  );
  assert.ok(
    credit,
    'the anchors take their coordinates from Wikidata and must say so',
  );
  assert.match(credit.html, /wikidata\.org/);
  assert.match(credit.html, /not a boundary, route or vessel position/);
});
