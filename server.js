import express from 'express';
import cors from 'cors';
import axios from 'axios';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = 5252;
const PYTHON_API_PORT = 8000;

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Start Python API server
let pythonProcess;
function startPythonAPI() {
  const pythonPath = process.platform === 'win32' ? 'venv\\Scripts\\python' : './venv/bin/python';
  pythonProcess = spawn(pythonPath, ['api_server.py']);
  
  pythonProcess.stdout.on('data', (data) => console.log(`[Python API] ${data}`));
  pythonProcess.stderr.on('data', (data) => console.error(`[Python API] ${data}`));
  
  console.log(`🐍 Python API starting on port ${PYTHON_API_PORT}...`);
}

startPythonAPI();

// Proxy to Python extraction API
app.post('/api/extract', async (req, res) => {
  try {
    const response = await axios.post(`http://localhost:${PYTHON_API_PORT}/extract`, req.body);
    res.json(response.data);
  } catch (error) {
    console.error('Extraction API Error:', error.message);
    res.status(500).json({ error: 'Python API unavailable' });
  }
});

app.get('/api/health', async (req, res) => {
  try {
    const response = await axios.get(`http://localhost:${PYTHON_API_PORT}/health`);
    res.json(response.data);
  } catch (error) {
    res.status(503).json({ status: 'degraded', python_api: 'disconnected' });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Circles running at http://localhost:${PORT}`);
});

process.on('SIGINT', () => {
  if (pythonProcess) pythonProcess.kill();
  process.exit();
});