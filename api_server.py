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
            # Single token - place at origin
            result = [{"label": req.tokens[0], "x": 0.0, "y": 0.0, "z": 0.0}]
        else:
            print(f"Projecting {len(embeddings)} embeddings to 3D")
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
