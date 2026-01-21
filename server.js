import express from 'express';
import cors from 'cors';
import axios from 'axios';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = 5252;

app.use(cors());
app.use(express.json());

// 1. Static Hosting
app.use(express.static('public'));

// 2. Proxy API to Local/Remote LLM
// Example: Connect to a local Ollama server running on 11434
app.post('/api/manifold-query', async (req, res) => {
  try {
    const { prompt } = req.body;
    
    // Replace this URL with your local LLM or high-perf backend
    const response = await axios.post('http://localhost:11434/api/generate', {
      model: 'llama3',
      prompt: `Extract semantic weights for: ${prompt}`,
      stream: false
    });

    res.json(response.data);
  } catch (error) {
    console.error('API Error:', error.message);
    res.status(500).json({ error: 'Backend connection failed' });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Circles running at http://localhost:${PORT}`);
  console.log(`📁 Static deps served from /deps/`);
});