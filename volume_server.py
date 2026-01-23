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

class NeighborsRequest(BaseModel):
    seed: str
    model: Optional[str] = "llama3:8b"
    count: Optional[int] = 5

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
        
        # Compute scalar field using Gaussian influence
        scalar_field = np.zeros((res, res, res))
        sigma = grid_range / 4  # Gaussian width
        
        for i in range(res):
            for j in range(res):
                for k in range(res):
                    point = np.array([x[i], y[j], z[k]])
                    
                    # Sum of Gaussian influences
                    influence = 0
                    for p3d in points_3d:
                        dist_sq = np.sum((point - p3d) ** 2)
                        influence += np.exp(-dist_sq / (2 * sigma ** 2))
                    
                    scalar_field[i, j, k] = influence
        
        # Normalize to 0-1 range
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

@app.post("/neighbors")
async def get_neighbors(req: NeighborsRequest):
    """Get semantically related neighbor concepts"""
    try:
        print(f"Finding neighbors for: {req.seed}")
        
        prompt = f"List {req.count} related concepts to '{req.seed}'. Only output comma-separated words:"
        res = requests.post('http://localhost:11434/api/generate',
            json={"model": req.model, "prompt": prompt, "stream": False}, timeout=30)
        
        response_text = res.json()["response"].strip()
        neighbors = [t.strip() for t in response_text.replace('\n', ',').split(',') if t.strip()][:req.count]
        
        print(f"Found neighbors: {neighbors}")
        
        return {"status": "success", "neighbors": neighbors}
    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/metaball")
async def get_metaball(req: VolumeRequest):
    """Returns physics properties instead of a voxel grid"""
    # ... (Keep embedding generation logic) ...
    
    # Calculate "Mass" and "Radius" based on semantic spread
    # High variance in embeddings = Larger, fluffier concept
    # Low variance = Tight, dense concept
    centroid = embeddings.mean(axis=0)
    distances = np.linalg.norm(embeddings - centroid, axis=1)
    radius = float(np.mean(distances)) * 5.0  # Scale factor for visual
    density = 1.0 / (float(np.std(distances)) + 0.1)

    return {
        "status": "success",
        "data": {
            "seed": req.seed,
            "mass": density,
            "radius": radius,
            # We don't send X/Y/Z yet, the frontend physics engine determines that
        }
    }

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
