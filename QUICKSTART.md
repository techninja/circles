# Quick Start

## Architecture
- **Node.js Server** (port 5252): Frontend hosting + API proxy
- **Python API** (port 8000): Ollama integration + UMAP projection
- **Ollama** (port 11434): LLM embeddings backend

## Setup & Run
```bash
npm install
npm run dev
```

This will:
1. Check for Python 3 and Ollama
2. Download llama3:8b model if needed
3. Create Python venv and install dependencies
4. Start both Node and Python servers

## API Usage

### Extract Manifold Data
```bash
curl -X POST http://localhost:5252/api/extract \
  -H "Content-Type: application/json" \
  -d '{"tokens": ["house", "skeleton", "truth"], "model": "llama3:8b"}'
```

### Health Check
```bash
curl http://localhost:5252/api/health
```

## Multi-GPU Support
The Python API uses Ollama which automatically detects and utilizes available GPUs. For larger models:
```bash
ollama pull llama3:70b
# Then use "model": "llama3:70b" in API requests
```
