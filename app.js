import * as THREE from 'three';
import { MarchingCubes } from 'three/examples/jsm/objects/MarchingCubes';

// The 'Circle' as a 3D blob
const resolution = 64;
const material = new THREE.MeshStandardMaterial({ color: 0x00ff88, wireframe: true });
const effect = new MarchingCubes(resolution, material, true, true, 100000);

function updateManifold(points) {
    effect.reset();
    points.forEach(p => {
        // Use coordinates from our Python extraction
        effect.addBall(p.x, p.y, p.z, strength, subtract);
    });
}