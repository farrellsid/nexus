// Remove package.json `exports` entries whose target file no longer exists.
//
//   node scripts/nexus-prune-exports.mjs          report and write
//   node scripts/nexus-prune-exports.mjs --check  report only; exit 1 if any entry dangles
//
// Upstream exposed every module through a large export map and its boundary check fails on a
// dangling entry. After a strip step deletes a module, this removes the entry that named it.
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const root = resolve(new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const packagePath = join(root, 'package.json');
const pkg = JSON.parse(readFileSync(packagePath, 'utf8'));
const check = process.argv.includes('--check');

const targetOf = (value) => (typeof value === 'string' ? value : Object.values(value).find((v) => typeof v === 'string'));
const dangling = Object.entries(pkg.exports ?? {}).filter(([, value]) => {
  const target = targetOf(value);
  return target && !existsSync(join(root, target));
});

console.log(`exports: ${Object.keys(pkg.exports ?? {}).length}, dangling: ${dangling.length}`);
for (const [key, value] of dangling) console.log(`  ${check ? 'DANGLING' : 'removed'}  ${key} -> ${targetOf(value)}`);
if (check) process.exit(dangling.length ? 1 : 0);
for (const [key] of dangling) delete pkg.exports[key];
writeFileSync(packagePath, JSON.stringify(pkg, null, 2) + '\n');
