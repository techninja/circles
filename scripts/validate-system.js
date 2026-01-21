import shell from 'shelljs';
import path from 'path';
import fs from 'fs';

console.log('🔍 Validating system dependencies...');

// 1. Check for Python 3
if (!shell.which('python3')) {
  console.error('❌ This project requires Python 3. Please install it to continue.');
  shell.exit(1);
}

// 2. Check for Ollama
if (!shell.which('ollama')) {
  console.error('❌ Ollama not found. Install from https://ollama.ai');
  shell.exit(1);
}

// 3. Verify Ollama is running
if (shell.exec('curl -s http://localhost:11434/api/tags', {silent: true}).code !== 0) {
  console.log('⚠️  Ollama not running. Starting ollama serve in background...');
  shell.exec('ollama serve > /dev/null 2>&1 &', {async: true});
  shell.exec('sleep 3');
}

// 4. Pull required model
const model = 'llama3:8b';
console.log(`📥 Ensuring ${model} is available...`);
const models = shell.exec('ollama list', {silent: true}).stdout;
if (!models.includes('llama3')) {
  console.log(`⬇️  Downloading ${model} (this may take several minutes)...`);
  if (shell.exec(`ollama pull ${model}`).code !== 0) {
    console.error('❌ Failed to download model');
    shell.exit(1);
  }
}

// 5. Setup Virtual Environment
const venvPath = path.resolve('venv');
if (!fs.existsSync(venvPath)) {
  console.log('🐍 Creating Python virtual environment...');
  shell.exec('python3 -m venv venv');
}

// 6. Install Python API Dependencies
console.log('📦 Installing Python API dependencies...');
const pip = process.platform === 'win32' ? 'venv\\Scripts\\pip' : './venv/bin/pip';

if (shell.exec(`${pip} install -r requirements.txt`).code !== 0) {
  console.error('❌ Python dependency installation failed.');
  shell.exit(1);
}

console.log('✅ System validation complete.');