// Fail if more than one copy of @cesium/engine is installed. Two copies once produced two WebGL
// context-limit singletons and a globe that never rendered (see docs/development-log.md).
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';

const root = resolve(new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const copies = [];

function search(dir, depth) {
  if (depth > 6 || !existsSync(dir)) return;
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    let isDir = false;
    try {
      isDir = statSync(path).isDirectory();
    } catch {
      continue;
    }
    if (!isDir) continue;
    if (name === '@cesium' && existsSync(join(path, 'engine', 'package.json'))) {
      copies.push(join(path, 'engine'));
    } else if (name === 'node_modules' || name.startsWith('@') || depth === 0) {
      search(path, depth + 1);
    } else {
      search(join(path, 'node_modules'), depth + 1);
    }
  }
}

search(join(root, 'node_modules'), 0);
const found = copies.map((dir) => ({
  where: relative(root, dir).replaceAll('\\', '/'),
  version: JSON.parse(readFileSync(join(dir, 'package.json'), 'utf8')).version,
}));
console.log(`@cesium/engine copies installed: ${found.length}`);
for (const copy of found) console.log(`  ${copy.version}  ${copy.where}`);
if (found.length !== 1) {
  console.error('expected exactly one @cesium/engine (see the @cesium/widgets override in apps/web/package.json)');
  process.exit(1);
}
