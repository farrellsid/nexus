import { createStandaloneApplication } from './standalone/application.js';
import { describeError } from './standalone/errors.js';
import {
  hasUsableWebGl,
  mountFallbackMap,
  wantsFallback,
} from './nexus/fallbackMap.ts';

/** Replace the shell with the flat map: same records and caveats, no WebGL needed. */
function showFallback(reason) {
  document.body.classList.add('nexus-fallback-active');
  mountFallbackMap(document.body, { reason });
}

let application = null;
if (wantsFallback(window.location.search)) {
  showFallback('the 2D view was requested');
} else if (!hasUsableWebGl()) {
  showFallback('WebGL is not available in this browser');
} else {
  application = createStandaloneApplication({
    allowQaRegistration: import.meta.env.DEV,
  });
  application.start().catch((error) => {
    console.error('Nexus shell initialization failed:', error);
    showFallback(describeError(error));
  });
}

export { application };
