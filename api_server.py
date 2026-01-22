from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import umap
import json
import requests
import traceback
from typing import List, Optional

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ExtractRequest(BaseModel):
    tokens: List[str]
    model: Optional[str] = "llama3:8b"

class ExpandRequest(BaseModel):
    seed: str
    model: Optional[str] = "llama3:8b"
    count: Optional[int] = 30

@app.post("/expand")
async def expand_manifold(req: ExpandRequest):
    """Generate related terms around a seed concept"""
    try:
        print(f"Expanding manifold around: {req.seed}")
        
        # Ask LLM for related terms
        prompt = f"List {req.count} related terms to '{req.seed}'. Only output comma-separated words, no explanations:"
        res = requests.post('http://localhost:11434/api/generate',
            json={"model": req.model, "prompt": prompt, "stream": False}, timeout=60)
        
        response_text = res.json()["response"].strip()
        print(f"LLM response: {response_text}")
        
        # Parse terms
        related = [t.strip() for t in response_text.replace('\n', ',').split(',') if t.strip()]
        related = [req.seed] + related[:req.count]
        
        print(f"Extracted terms: {related}")
        
        # Get embeddings
        embeddings = []
        for term in related:
            res = requests.post('http://localhost:11434/api/embeddings',
                json={"model": req.model, "prompt": term}, timeout=30)
            embeddings.append(res.json()["embedding"])
        
        # Project to 3D
        if len(embeddings) > 1:
            n_neighbors = min(5, len(embeddings) - 1)
            reducer = umap.UMAP(n_components=3, n_neighbors=n_neighbors, min_dist=0.1)
            coords = reducer.fit_transform(np.array(embeddings))
            result = [{"label": related[i], "x": float(coords[i][0]),
                       "y": float(coords[i][1]), "z": float(coords[i][2])}
                      for i in range(len(coords))]
        else:
            result = [{"label": related[0], "x": 0.0, "y": 0.0, "z": 0.0}]
        
        return {"status": "success", "data": result}
    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract")
async def extract_manifold(req: ExtractRequest):
    try:
        print(f"Extracting embeddings for: {req.tokens}")
        embeddings = []
        for token in req.tokens:
            print(f"Requesting embedding for: {token}")
            res = requests.post('http://localhost:11434/api/embeddings', 
                json={"model": req.model, "prompt": token}, timeout=30)
            res.raise_for_status()
            data = res.json()
            embeddings.append(data["embedding"])
            print(f"Got embedding of length: {len(data['embedding'])}")
        
        # Project to 3D
        if len(embeddings) == 1:
            result = [{"label": req.tokens[0], "x": 0.0, "y": 0.0, "z": 0.0}]
        else:
            n_neighbors = min(5, len(embeddings) - 1)
            reducer = umap.UMAP(n_components=3, n_neighbors=n_neighbors, min_dist=0.1)
            coords = reducer.fit_transform(np.array(embeddings))
            
            result = [{"label": req.tokens[i], "x": float(coords[i][0]), 
                       "y": float(coords[i][1]), "z": float(coords[i][2])} 
                      for i in range(len(coords))]
        
        print(f"Success! Returning {len(result)} coordinates")
        return {"status": "success", "data": result}
    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    try:
        res = requests.get('http://localhost:11434/api/tags', timeout=2)
        return {"status": "healthy", "ollama": "connected"}
    except:
        return {"status": "degraded", "ollama": "disconnected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
