// The shell's Vite configuration. Upstream's version loaded provider proxies, API keys and a
// key-setup panel from server/; those were stripped in M5 step B1. This uses the explicit,
// environment-free browser config that upstream already kept in build/vite.js.
import { createBrowserViteConfig } from './build/vite.js';

export default createBrowserViteConfig({ host: '127.0.0.1', port: 4173 });
