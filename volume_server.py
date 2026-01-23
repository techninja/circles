from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import requests
import traceback
from typing import List, Optional
from scipy.spatial.distance import cdist

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class VolumeRequest(BaseModel):
    seed: str
    model: Optional[str] = "llama3:8b"
    resolution: Optional[int] = 32

@app.post("/volume")
async def extract_volume(req: VolumeRequest):
    """Extract 3D scalar field for iso-surface rendering"""
    try:
        print(f"Extracting volume for: {req.seed}")
        
        # Generate contextual variations
        prompts = [
            req.seed,
            f"A {req.seed}",
            f"The {req.seed}",
            f"{req.seed} is",
            f"About {req.seed}",
            f"Regarding {req.seed}",
            f"Concerning {req.seed}",
            f"Example of {req.seed}"
        ]
        
        # Get embeddings for all variations
        embeddings = []
        for prompt in prompts:
            res = requests.post('http://localhost:11434/api/embeddings',
                json={"model": req.model, "prompt": prompt}, timeout=30)
            embeddings.append(res.json()["embedding"])
        
        embeddings = np.array(embeddings)
        print(f"Got {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")
        
        # Compute centroid and spread
        centroid = embeddings.mean(axis=0)
        
        # Use PCA to get principal directions
        centered = embeddings - centroid
        cov = np.cov(centered.T)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        
        # Take top 3 principal components
        top3_idx = np.argsort(eigenvalues)[-3:]
        principal_axes = eigenvectors[:, top3_idx]
        
        # Project embeddings onto 3D space
        points_3d = centered @ principal_axes
        
        print(f"3D projection range: {points_3d.min(axis=0)} to {points_3d.max(axis=0)}")
        
        # Create 3D grid
        res = req.resolution
        grid_range = points_3d.max() - points_3d.min()
        margin = grid_range * 0.3
        
        x = np.linspace(points_3d[:, 0].min() - margin, points_3d[:, 0].max() + margin, res)
        y = np.linspace(points_3d[:, 1].min() - margin, points_3d[:, 1].max() + margin, res)
        z = np.linspace(points_3d[:, 2].min() - margin, points_3d[:, 2].max() + margin, res)
        
        # Compute scalar field using metaball influence
        scalar_field = np.zeros((res, res, res))
        
        for i in range(res):
            for j in range(res):
                for k in range(res):
                    point = np.array([x[i], y[j], z[k]])
                    
                    # Sum of inverse distance squared (metaball formula)
                    influence = 0
                    for p3d in points_3d:
                        dist = np.linalg.norm(point - p3d)
                        if dist > 0:
                            influence += 1.0 / (dist ** 2 + 0.1)
                    
                    scalar_field[i, j, k] = influence
        
        # Normalize
        scalar_field = (scalar_field - scalar_field.min()) / (scalar_field.max() - scalar_field.min())
        
        print(f"Scalar field range: {scalar_field.min()} to {scalar_field.max()}")
        
        return {
            "status": "success",
            "data": {
                "field": scalar_field.flatten().tolist(),
                "resolution": res,
                "bounds": {
                    "x": [float(x[0]), float(x[-1])],
                    "y": [float(y[0]), float(y[-1])],
                    "z": [float(z[0]), float(z[-1])]
                },
                "seed": req.seed
            }
        }
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
