import * as esbuild from 'esbuild';
import path from 'path';
import fs from 'fs';

const deps = ['three', 'matter-js', 'umap-js'];
const outputDir = path.resolve('public/deps');

if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

console.log('📦 Bundling 3rd-party dependencies for browser...');

deps.forEach(async (dep) => {
  try {
    await esbuild.build({
      entryPoints: [dep],
      bundle: true,
      format: 'esm',
      outfile: path.join(outputDir, `${dep}.js`),
      minify: true,
      sourcemap: true,
    });
    console.log(`✅ Bundled: ${dep}`);
  } catch (err) {
    console.error(`❌ Failed to bundle ${dep}:`, err);
  }
});