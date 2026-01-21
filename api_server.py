from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import numpy as np
import umap
import json
import subprocess
from typing import List, Optional

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ExtractRequest(BaseModel):
    tokens: List[str]
    layers: Optional[List[int]] = [10, 20, 30]
    model: Optional[str] = "llama3:8b"

class OllamaExtractor:
    def __init__(self):
        self.cache = {}
    
    def get_activations(self, tokens: List[str], model: str, layers: List[int]):
        manifold_data = {}
        for token in tokens:
            result = subprocess.run(
                ["ollama", "show", model, "--modelfile"],
                capture_output=True, text=True, check=True
            )
            
            # Query embeddings via ollama API
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/embeddings", 
                 "-d", json.dumps({"model": model, "prompt": token})],
                capture_output=True, text=True
            )
            data = json.loads(result.stdout)
            embedding = data.get("embedding", [])
            
            # Simulate multi-layer by chunking embedding
            chunk_size = len(embedding) // len(layers)
            manifold_data[token] = {
                f"layer_{layers[i]}": embedding[i*chunk_size:(i+1)*chunk_size]
                for i in range(len(layers))
            }
        return manifold_data
    
    def project_to_3d(self, manifold_data):
        all_vecs, labels = [], []
        for token, layers_dict in manifold_data.items():
            for layer_name, vec in layers_dict.items():
                all_vecs.append(vec)
                labels.append(f"{token}_{layer_name}")
        
        reducer = umap.UMAP(n_components=3, n_neighbors=min(15, len(all_vecs)-1), min_dist=0.1)
        coords = reducer.fit_transform(np.array(all_vecs))
        
        return [{"label": labels[i], "x": float(c[0]), "y": float(c[1]), "z": float(c[2])} 
                for i, c in enumerate(coords)]

extractor = OllamaExtractor()

@app.post("/extract")
async def extract_manifold(req: ExtractRequest):
    try:
        raw_data = extractor.get_activations(req.tokens, req.model, req.layers)
        coords = extractor.project_to_3d(raw_data)
        return {"status": "success", "data": coords}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    try:
        subprocess.run(["ollama", "list"], check=True, capture_output=True)
        return {"status": "healthy", "ollama": "connected"}
    except:
        return {"status": "degraded", "ollama": "disconnected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
