import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import umap
import numpy as np
import json

class SemanticExtractor:
    def __init__(self, model_id="meta-llama/Meta-Llama-3-8B"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            torch_dtype=torch.float16, 
            device_map="auto"
        )

    def get_token_activations(self, tokens, layers=[10, 20, 30]):
        """
        Extracts activations from multiple depths to show 
        syntactic vs. semantic 'perspectives'.
        """
        manifold_data = {}
        
        for token in tokens:
            inputs = self.tokenizer(token, return_tensors="pt").to("cuda")
            with torch.no_grad():
                outputs = self.model(**inputs, output_hidden_states=True)
                
                # Capture specific layers for 'multi-perspective' viewing
                activations = {
                    f"layer_{idx}": outputs.hidden_states[idx][0, -1, :].cpu().numpy().tolist()
                    for idx in layers
                }
                manifold_data[token] = activations
        return manifold_data

    def project_to_3d(self, manifold_data):
        """Reduces high-dim activations to 3D coordinates for Three.js."""
        all_vecs = []
        labels = []
        for token, layers in manifold_data.items():
            for layer_name, vec in layers.items():
                all_vecs.append(vec)
                labels.append(f"{token}_{layer_name}")

        reducer = umap.UMAP(n_components=3, n_neighbors=15, min_dist=0.1)
        coords = reducer.fit_transform(np.array(all_vecs))
        
        output = []
        for i, coord in enumerate(coords):
            output.append({
                "label": labels[i],
                "x": float(coord[0]),
                "y": float(coord[1]),
                "z": float(coord[2])
            })
        return output

if __name__ == "__main__":
    probe = SemanticExtractor()
    concepts = ["house", "skeleton", "Jeremy", "goated", "allah"]
    raw_data = probe.get_token_activations(concepts)
    vis_data = probe.project_to_3d(raw_data)
    
    with open("manifold_data.json", "w") as f:
        json.dump(vis_data, f)