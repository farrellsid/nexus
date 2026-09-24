import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  KEY_SETUP_APPEND_HEADER,
  KEY_SETUP_KEYS,
  KEY_SETUP_VALUE_LIMIT,
  commandCompletedSuccessfully,
  isKeySetupExternallyManaged,
  keySetupStatus,
  keySetupRequirement,
  knownKeySetupEnvVars,
  parseWindowsUserSid,
  upsertDotenvValues,
  validateKeySetupUpdates,
} from './keySetupCore.mjs';

test('provider requirements name the registry env vars and next step', () => {
  assert.equal(
    keySetupRequirement('cesium-ion'),
    'Needs CESIUM_ION_TOKEN — add it in Provider Settings',
  );
  assert.equal(keySetupRequirement('unknown'), '');
});

