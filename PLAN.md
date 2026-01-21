# Implementation Plan

## Phase 1: Data Pipeline (The "Truth" Layer)
- [ ] Implement multi-layer extraction (Low layers = Structure, High layers = Meaning).
- [ ] Create a local API/WebSocket to stream coordinate updates from Python to the Frontend.
- [ ] Generate a "Comparison Dataset" (e.g., contrasting "Individual" bias vectors vs "Global" vectors).

## Phase 2: 2D Physics (The "Rubber Band" Layer)
- [ ] Setup `Matter.js` or `P5.js` for the top-down view.
- [ ] Implement "Membrane" logic: Points connected by elastic constraints.
- [ ] Create "Venn Overlap" visualizer: When two membranes touch, calculate shared nearest neighbors in the LLM space.

## Phase 3: 3D Manifolds (The "Perspective" Layer)
- [ ] Integrate `Three.js` with `Marching Cubes`.
- [ ] Map 3D points from `extraction.py` to "Metaball" influence points.
- [ ] **The "Perspective Proof" UI:**
    - [ ] Add a "Lock View" button that restricts the camera to a specific 2D slice of the 3D manifold.
    - [ ] Add an "Unlock Truth" button that lerps the camera into a full 3D orbital view, revealing the connected geometry.

## Phase 4: Interaction & Polish
- [ ] Drag-and-drop token injection.
- [ ] Real-time "Elasticity" adjustment (modifying UMAP parameters on the fly).
- [ ] Exportable "Perspective Snapshots" to share specific conceptual "islands."