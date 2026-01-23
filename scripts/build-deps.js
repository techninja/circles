import * as esbuild from 'esbuild';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outputDir = path.resolve('public/deps');

if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });

console.log('📦 Bundling Three.js for browser...');

try {
  await esbuild.build({
    entryPoints: ['three'],
    bundle: true,
    format: 'esm',
    outfile: path.join(outputDir, 'three.js'),
    minify: false,
    sourcemap: true,
  });
  console.log('✅ Bundled: three');
  
  // Copy three/examples for addons
  const threeExamplesDir = path.join(outputDir, 'three/examples/jsm');
  fs.mkdirSync(threeExamplesDir, { recursive: true });
  
  const nodeModulesThree = path.resolve('node_modules/three/examples/jsm');
  fs.cpSync(nodeModulesThree, threeExamplesDir, { recursive: true });
  console.log('✅ Copied: three/examples/jsm');
} catch (err) {
  console.error('❌ Failed to bundle three:', err);
}