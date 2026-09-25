// Remove CSS rules whose selectors name an id or class that no markup or script mentions.
//
//   node scripts/nexus-prune-css.mjs            report what would be removed
//   node scripts/nexus-prune-css.mjs --write    rewrite the stylesheets
//
// After the strip, most of the inherited CSS styles panels that no longer exist. A selector is dead
// when it contains an `#id` or `.class` whose name appears nowhere in index.html, the HTML
// templates or the non-test scripts. A comma list keeps its live selectors; a rule with none left is
// removed, as is an @keyframes block nothing animates. The check is textual, so a class assembled
// at run time from pieces would be missed: run the smoke test and look at a screenshot afterwards.
import { readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import * as prettier from 'prettier';

const root = resolve(new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const write = process.argv.includes('--write');

const walk = (dir) =>
  readdirSync(dir).flatMap((name) => {
    if (name === 'node_modules' || name === 'dist' || name.startsWith('.')) return [];
    const path = join(dir, name);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });

const sources = [
  join(root, 'index.html'),
  ...walk(join(root, 'src')).filter((p) => /\.(html|m?js|ts)$/.test(p) && !/\.test\.(mjs|ts)$/.test(p)),
  ...walk(join(root, 'build')),
];
const corpus = sources.map((p) => readFileSync(p, 'utf8')).join('\n');
// Names Cesium or a template string builds at run time cannot be found by a text search.
const RUNTIME_PREFIXES = ['cesium-', 'feed-', 'chip-', 'is-', 'roll-', 'tray-'];
const mentioned = (name) => RUNTIME_PREFIXES.some((prefix) => name.startsWith(prefix)) || corpus.includes(name);

const cssFiles = walk(join(root, 'src/ui/styles')).filter((p) => p.endsWith('.css'));
const keyframeNames = new Map();
const removedTokens = new Set();
let totalRules = 0;
let removedRules = 0;

const splitSelectors = (text) => {
  const parts = [];
  let depth = 0;
  let start = 0;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '(' || ch === '[') depth++;
    else if (ch === ')' || ch === ']') depth--;
    else if (ch === ',' && depth === 0) {
      parts.push(text.slice(start, i));
      start = i + 1;
    }
  }
  parts.push(text.slice(start));
  return parts;
};

const deadToken = (selector) => {
  // strip attribute selectors and quoted strings so their values are not read as names
  const cleaned = selector.replace(/\[[^\]]*\]/g, '').replace(/(['"]).*?\1/g, '');
  for (const match of cleaned.matchAll(/([#.])(-?[_a-zA-Z][\w-]*)/g)) {
    const name = match[2];
    if (/^\d/.test(name)) continue;
    if (!mentioned(name)) return match[0];
  }
  return null;
};

async function prune(file) {
  const code = readFileSync(file, 'utf8').replace(/\r\n/g, '\n');
  const { ast } = await prettier.__debug.parse(code, { parser: 'css' });
  const edits = []; // {start, end, replacement}

  const visit = (nodes) => {
    for (const node of nodes ?? []) {
      if (node.type === 'css-rule') {
        totalRules++;
        const start = node.source.startOffset;
        const braceAt = code.indexOf('{', start);
        const selectorText = code.slice(start, braceAt);
        const selectors = splitSelectors(selectorText);
        const live = selectors.filter((selector) => {
          const dead = deadToken(selector);
          if (dead) removedTokens.add(dead);
          return !dead;
        });
        if (live.length === 0) {
          removedRules++;
          edits.push({ start, end: node.source.endOffset, replacement: '' });
        } else if (live.length !== selectors.length) {
          edits.push({ start, end: braceAt, replacement: `${live.map((s) => s.trim()).join(',\n')} ` });
        }
      } else if (node.type === 'css-atrule' && /^(media|supports|container|layer)$/i.test(node.name)) {
        visit(node.nodes);
      } else if (node.type === 'css-atrule' && /keyframes$/i.test(node.name)) {
        keyframeNames.set(node.params, { file, node });
      }
    }
  };
  visit(ast.nodes);

  let out = code;
  for (const edit of edits.sort((a, b) => b.start - a.start)) {
    out = out.slice(0, edit.start) + edit.replacement + out.slice(edit.end);
  }
  return { code, out };
}

const results = [];
for (const file of cssFiles) results.push({ file, ...(await prune(file)) });

// keyframes and empty at-rules after the rule pass
const stillUsed = (name) => results.some(({ out }) => new RegExp(`animation[^;{}]*\\b${name}\\b`).test(out));
for (const result of results) {
  let out = result.out;
  const { ast } = await prettier.__debug.parse(out, { parser: 'css' });
  const edits = [];
  for (const node of ast.nodes) {
    if (node.type === 'css-atrule' && /keyframes$/i.test(node.name) && !stillUsed(node.params.trim())) {
      edits.push({ start: node.source.startOffset, end: node.source.endOffset });
    } else if (node.type === 'css-atrule' && /^(media|supports|container)$/i.test(node.name) && (node.nodes ?? []).length === 0) {
      edits.push({ start: node.source.startOffset, end: node.source.endOffset });
    }
  }
  for (const edit of edits.sort((a, b) => b.start - a.start)) out = out.slice(0, edit.start) + out.slice(edit.end);
  result.out = out;
}

for (const { file, code, out } of results) {
  const rel = file.slice(root.length + 1).replaceAll('\\', '/');
  const tidy = await prettier.format(out, { parser: 'css', ...(await prettier.resolveConfig(file)) });
  console.log(`${rel}: ${code.length} -> ${tidy.length} bytes`);
  if (write) writeFileSync(file, tidy);
}
console.log(`rules: ${totalRules}, removed outright: ${removedRules}`);
if (process.argv.includes('--tokens')) console.log([...removedTokens].sort().join(' '));
