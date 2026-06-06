/**
 * Patch @tarojs/webpack5-runner's BaseConfig.js to drop the bundled
 * `webpackbar` plugin (whose legacy options break webpack 5.97+'s
 * ProgressPlugin schema validation) and use a plain `webpack.ProgressPlugin`
 * with the new API instead. Runs idempotently on every `pnpm install`.
 */
import { readFileSync, writeFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const projectRoot = dirname(here);

const MARKER = '/* PATCH: webpackbar replaced by vanilla ProgressPlugin */';

let patched = 0;

function walk(dir) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      walk(full);
    } else if (entry === 'BaseConfig.js') {
      patch(full);
    }
  }
}

function patch(file) {
  const src = readFileSync(file, 'utf8');
  if (src.includes(MARKER)) return;

  // The block to replace starts at "plugin: {\n                webpackbar:"
  // and ends at "})\n            },\n            watchOptions:".
  // We replace everything from the opening "plugin: {" through the
  // closing "}),\n            },\n" of the plugin object, keeping
  // "watchOptions: {" intact.
  const start = src.indexOf('plugin: {\n                webpackbar: WebpackPlugin_1.default.getWebpackBarPlugin({');
  if (start === -1) return;

  const endOfClosing = src.indexOf('})\n            },\n            watchOptions:', start);
  if (endOfClosing === -1) return;
  // Cut through the closing brace + comma of the plugin object, but keep
  // the "\n            watchOptions:" segment that follows it.
  const cutEnd = endOfClosing + '})\n            },'.length; // includes the trailing "\n            },"

  const replacement = `plugin: {
                progress: {
                    plugin: require('webpack').ProgressPlugin,
                    args: [{ activeModules: true, modules: true, entries: true }]
                }
            },
            ${MARKER}`;

  const out = src.slice(0, start) + replacement + src.slice(cutEnd);
  writeFileSync(file, out, 'utf8');
  patched += 1;
  console.log(`[patch-taro-webpackbar] patched ${file}`);
}

const pnpmRoot = join(projectRoot, 'node_modules', '.pnpm');
try {
  statSync(pnpmRoot);
} catch {
  console.log('[patch-taro-webpackbar] node_modules/.pnpm not found, skipping');
  process.exit(0);
}

for (const entry of readdirSync(pnpmRoot)) {
  if (!entry.startsWith('@tarojs+webpack5-runner@')) continue;
  const dist = join(
    pnpmRoot,
    entry,
    'node_modules',
    '@tarojs',
    'webpack5-runner',
    'dist',
    'webpack',
  );
  try {
    statSync(dist);
    walk(dist);
  } catch {
    // not present
  }
}

if (patched === 0) {
  console.log('[patch-taro-webpackbar] no files needed patching');
} else {
  console.log(`[patch-taro-webpackbar] ${patched} file(s) patched`);
}
