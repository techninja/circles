import shell from 'shelljs';
import path from 'path';
import fs from 'fs';

console.log('🔍 Validating system dependencies...');

// 1. Check for Python 3
if (!shell.which('python3')) {
  console.error('❌ This project requires Python 3. Please install it to continue.');
  shell.exit(1);
}

// 2. Setup Virtual Environment
const venvPath = path.resolve('venv');
if (!fs.existsSync(venvPath)) {
  console.log('🐍 Creating Python virtual environment...');
  shell.exec('python3 -m venv venv');
}

// 3. Install Python Dependencies
console.log('📦 Installing Python ML dependencies (this may take a minute)...');
const pip = process.platform === 'win32' ? 'venv\\Scripts\\pip' : './venv/bin/pip';

const pyDeps = [
  'torch --index-url https://download.pytorch.org/whl/cpu', // Default to CPU for portability
  'transformers',
  'umap-learn',
  'numpy',
  'accelerate'
];

if (shell.exec(`${pip} install ${pyDeps.join(' ')}`).code !== 0) {
  console.error('❌ Python dependency installation failed.');
  shell.exit(1);
}

console.log('✅ System validation complete.');