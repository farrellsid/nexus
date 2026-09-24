// Find dangling imports and unreachable modules after each strip step.
//
//   node scripts/nexus-dead-modules.mjs              report only
//   node scripts/nexus-dead-modules.mjs --strict     exit 1 on any dangling import or unreachable
//                                                    module not in scripts/dead-modules-allowed.json,
//                                                    and on a listed entry that no longer occurs
//   node scripts/nexus-dead-modules.mjs --record     write the current findings as the allowed list
//
// Reachability starts at index.html's module scripts, vite.config.js and build/*.js and follows
// static, dynamic and `new URL(..., import.meta.url)` imports of relative paths. Test files
// (*.test.mjs) are not roots: a module only tests use is reported as unreachable, which is the
// point, because a stripped feature's leftovers should not survive on the strength of their tests.
import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';

const root = resolve(new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const strict = process.argv.includes('--strict');
const allowedPath = join(root, 'scripts', 'dead-modules-allowed.json');
const allowedFile = existsSync(allowedPath) ? JSON.parse(readFileSync(allowedPath, 'utf8')) : {};
const allowed = new Set(allowedFile.modules ?? []);
const allowedDangling = new Set(allowedFile.dangling ?? []);
const record = process.argv.includes('--record');

const walk = (dir) =>
  readdirSync(dir).flatMap((name) => {
    if (name === 'node_modules' || name === 'dist' || name.startsWith('.')) return [];
    const path = join(dir, name);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });
const rel = (path) => relative(root, path).replaceAll('\\', '/');
const isSource = (path) => /\.(m?js)$/.test(path);
const isTest = (path) => /\.test\.mjs$/.test(path);

// Import statements must start a line, so import-shaped strings inside test fixtures do not count.
const IMPORT = /^[ \t]*(?:import|export)\s[^'"`;]*?from\s*['"]([^'"]+)['"]|^[ \t]*import\s*['"]([^'"]+)['"]|import\(\s*['"]([^'"]+)['"]\s*\)/gm;
const URL_REF = /new URL\(\s*['"]([^'"]+)['"]\s*,\s*import\.meta\.url/g;

function resolveImport(from, spec) {
  if (!spec.startsWith('.') && !spec.startsWith('/')) return { external: true };
  if (spec.startsWith('/node_modules/')) return { external: true }; // Vite's generated dependency cache
  const clean = spec.split('?')[0].split('#')[0];
  const base = clean.startsWith('/') ? join(root, clean) : resolve(dirname(from), clean);
  for (const candidate of [base, `${base}.js`, `${base}.mjs`, join(base, 'index.js'), join(base, 'index.mjs')]) {
    if (existsSync(candidate) && statSync(candidate).isFile()) return { path: candidate };
  }
  return { missing: base };
}

const importsOf = (file) => {
  const text = readFileSync(file, 'utf8');
  const specs = [...text.matchAll(IMPORT)].map((m) => m[1] ?? m[2] ?? m[3]).filter(Boolean);
  // A `new URL(path, import.meta.url)` may name a file or a directory; only a missing path is dangling.
  const urls = [...text.matchAll(URL_REF)].map((m) => m[1]).filter((s) => s.startsWith('.'));
  return { specs, urls };
};

const all = walk(root).filter((p) => isSource(p) && !p.includes(`${join(root, 'tests')}`));
const dangling = [];
const graph = new Map();
for (const file of all) {
  const edges = [];
  const { specs, urls } = importsOf(file);
  for (const spec of specs) {
    const target = resolveImport(file, spec);
    if (target.missing) dangling.push(`${rel(file)} imports ${spec}`);
    if (target.path) edges.push(target.path);
  }
  for (const spec of urls) {
    const path = resolve(dirname(file), spec.split('?')[0].split('#')[0]);
    if (!existsSync(path)) dangling.push(`${rel(file)} references ${spec}`);
    else if (statSync(path).isFile() && isSource(path)) edges.push(path);
  }
  graph.set(file, edges);
}

const roots = [];
const html = readFileSync(join(root, 'index.html'), 'utf8');
for (const m of html.matchAll(/<script[^>]*type="module"[^>]*src="([^"]+)"/g)) {
  const target = resolveImport(join(root, 'index.html'), m[1].startsWith('/') ? `.${m[1]}` : m[1]);
  if (target.path) roots.push(target.path);
}
for (const extra of ['vite.config.js', ...readdirSync(join(root, 'build')).map((n) => `build/${n}`)]) {
  const path = join(root, extra);
  if (existsSync(path)) roots.push(path);
}

const seen = new Set();
const stack = [...roots];
while (stack.length) {
  const file = stack.pop();
  if (seen.has(file) || !graph.has(file)) continue;
  seen.add(file);
  stack.push(...graph.get(file));
}

const unreachable = all
  .filter((f) => !seen.has(f) && !isTest(f) && rel(f).startsWith('src/'))
  .map(rel)
  .sort();
const newOrphans = unreachable.filter((f) => !allowed.has(f));
const newDangling = dangling.filter((d) => !allowedDangling.has(d));
const staleModules = [...allowed].filter((f) => !unreachable.includes(f));
const staleDangling = [...allowedDangling].filter((d) => !dangling.includes(d));

if (record) {
  writeFileSync(allowedPath, JSON.stringify({ modules: unreachable, dangling: [...dangling].sort() }, null, 2) + '\n');
  console.log(`recorded ${unreachable.length} unreachable modules and ${dangling.length} dangling references`);
  process.exit(0);
}

console.log(`modules: ${all.length} (${all.filter(isTest).length} tests), reachable from the entry: ${seen.size}`);
console.log(`dangling imports: ${dangling.length} (${newDangling.length} new); unreachable source modules: ${unreachable.length} (${newOrphans.length} new)`);
for (const line of newDangling) console.log(`  DANGLING  ${line}`);
for (const file of newOrphans.slice(0, 40)) console.log(`  UNREACHABLE  ${file}`);
if (newOrphans.length > 40) console.log(`  ... and ${newOrphans.length - 40} more`);
for (const f of [...staleModules, ...staleDangling]) console.log(`  STALE  ${f} is on the allowed list but no longer occurs: remove it`);
if (strict && (newDangling.length || newOrphans.length || staleModules.length || staleDangling.length)) process.exit(1);
