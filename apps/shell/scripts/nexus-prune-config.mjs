// Keep the configuration files that name source modules in step with the modules that exist.
//
//   node scripts/nexus-prune-config.mjs          report and write
//   node scripts/nexus-prune-config.mjs --check  report only; exit 1 if anything dangles
//
// Upstream lists every module in three places: the package.json `exports` map, the module groups
// in scripts/package-boundaries.json, and the format scope in scripts/format-scope.json. A strip
// step deletes modules but not those names, and the boundary check fails on a dangling name. This
// removes the names of deleted modules and drops any boundary group that has nothing left.
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const root = resolve(new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const check = process.argv.includes('--check');
const read = (name) => JSON.parse(readFileSync(join(root, name), 'utf8'));
const exists = (file) => existsSync(join(root, file));
const targetOf = (value) => (typeof value === 'string' ? value : Object.values(value).find((v) => typeof v === 'string'));

// JSON.stringify puts every array element on its own line; keep short string arrays inline.
function format(value) {
  return (
    JSON.stringify(value, null, 2).replace(/\[\n[^[\]]*?\]/g, (block) => {
      const inline = block.replace(/\s*\n\s*/g, ' ').replace('[ ', '[').replace(' ]', ']');
      return inline.length <= 70 ? inline : block;
    }) + '\n'
  );
}

const report = [];
const pkg = read('package.json');
for (const [key, value] of Object.entries(pkg.exports ?? {})) {
  const target = targetOf(value);
  if (target && !exists(target)) {
    report.push(`export ${key} -> ${target}`);
    delete pkg.exports[key];
  }
}

const groups = read('scripts/package-boundaries.json');
for (const [name, group] of Object.entries(groups)) {
  const exportsLeft = (group.exports ?? []).filter((key) => key in pkg.exports);
  const modulesLeft = (group.modules ?? []).filter(exists);
  const removed = (group.modules ?? []).length - modulesLeft.length + (group.exports ?? []).length - exportsLeft.length;
  if (exportsLeft.length === 0 || modulesLeft.length === 0) {
    report.push(`boundary group ${name} (${removed} names, group dropped)`);
    delete groups[name];
  } else if (removed) {
    report.push(`boundary group ${name}: ${removed} names`);
    groups[name] = { ...group, exports: exportsLeft, modules: modulesLeft };
  }
}

const scope = read('scripts/format-scope.json');
const scopeLeft = scope.filter(exists);
if (scopeLeft.length !== scope.length) report.push(`format scope: ${scope.length - scopeLeft.length} files`);

console.log(report.length ? report.map((line) => `  ${check ? 'DANGLING' : 'removed'}  ${line}`).join('\n') : 'configuration names only existing modules');
if (check) process.exit(report.length ? 1 : 0);
if (report.length) {
  writeFileSync(join(root, 'package.json'), JSON.stringify(pkg, null, 2) + '\n');
  writeFileSync(join(root, 'scripts/package-boundaries.json'), format(groups));
  writeFileSync(join(root, 'scripts/format-scope.json'), format(scopeLeft));
}
