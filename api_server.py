from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import umap
import json
import requests
from typing import List, Optional

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ExtractRequest(BaseModel):
    tokens: List[str]
    model: Optional[str] = "llama3:8b"

@app.post("/extract")
async def extract_manifold(req: ExtractRequest):
    try:
        embeddings = []
        for token in req.tokens:
            res = requests.post('http://localhost:11434/api/embeddings', 
                json={"model": req.model, "prompt": token})
            embeddings.append(res.json()["embedding"])
        
        # Project to 3D
        reducer = umap.UMAP(n_components=3, n_neighbors=min(5, len(embeddings)), min_dist=0.1)
        coords = reducer.fit_transform(np.array(embeddings))
        
        result = [{"label": req.tokens[i], "x": float(coords[i][0]), 
                   "y": float(coords[i][1]), "z": float(coords[i][2])} 
                  for i in range(len(coords))]
        
        return {"status": "success", "data": result}
    except Exception as e:
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
