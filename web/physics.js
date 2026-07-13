// Real-time Physics Engine for Muon Tomography in JavaScript

// Reference Materials Database
const MATERIALS = {
    'Air': { name: 'Air', radiationLength: 30516.0, density: 0.0012, color: '#a0c0ff' },
    'Water': { name: 'Water', radiationLength: 36.08, density: 1.00, color: '#00d2ff' },
    'Plastic': { name: 'Plastic', radiationLength: 41.70, density: 1.05, color: '#ff00d2' },
    'Aluminium': { name: 'Aluminium', radiationLength: 8.89, density: 2.70, color: '#d2ff00' },
    'Concrete': { name: 'Concrete', radiationLength: 11.55, density: 2.30, color: '#a0a0a0' },
    'Iron': { name: 'Iron', radiationLength: 1.76, density: 7.87, color: '#ff6c00' },
    'Copper': { name: 'Copper', radiationLength: 1.43, density: 8.96, color: '#ffaa00' },
    'Lead': { name: 'Lead', radiationLength: 0.56, density: 11.34, color: '#8b8b8b' },
    'Tungsten': { name: 'Tungsten', radiationLength: 0.35, density: 19.30, color: '#ffb400' },
    'Uranium': { name: 'Uranium', radiationLength: 0.32, density: 18.95, color: '#00ff6c' }
};

class PhysicsEngine {
    constructor() {
        this.reset();
    }

    reset() {
        this.muonsSimulated = 0;
        this.muonsReconstructed = 0;
        this.activePlaneSpacing = 15.0; // cm
        this.zPlanes = [75.0, 60.0, 45.0, 30.0, -30.0, -45.0, -60.0, -75.0];
        this.energyMode = 'random';
        this.manualEnergyGeV = 3.0;
        
        // Container Setup
        this.containerSize = 40.0;
        this.wallThickness = 0.5;
        this.steelX0 = 1.76;
        
        // Voxel Grid (40x40x40 voxels)
        this.numVoxels = 40;
        this.voxelSize = 1.0;
        this.densityGrid = new Float32Array(this.numVoxels * this.numVoxels * this.numVoxels);
        this.hitGrid = new Uint32Array(this.numVoxels * this.numVoxels * this.numVoxels);
        this.maxVoxelVal = 0;
        
        // Classifier Accumulators
        this.avgMeasuredAngle = 0;
        this.avgMeasuredShift = 0;
        this.intersectCount = 0;
        this.accMomenta = 0;
        this.accThickness = 0;
        this.accExpectedAngle = {};
        this.accExpectedShift = {};
        Object.keys(MATERIALS).forEach(m => {
            this.accExpectedAngle[m] = 0.0;
            this.accExpectedShift[m] = 0.0;
        });
        
        this.predictedMaterial = "Air";
        this.classificationConfidence = 1.0;
        this.materialConfidences = {};
        Object.keys(MATERIALS).forEach(m => this.materialConfidences[m] = 0.1);
        
        // Plane Offset Accumulators (Digitization Offset)
        this.planeOffsetsSum = new Float64Array(8);
        this.planeOffsetsCount = new Uint32Array(8);
        
        // Track list for visualization cache (max 200 tracks)
        this.recentTracks = [];
        this.recentPOCAs = [];
    }

    updatePlanePositions(spacing) {
        this.activePlaneSpacing = spacing;
        this.zPlanes = [
            30.0 + 3.0 * spacing,
            30.0 + 2.0 * spacing,
            30.0 + spacing,
            30.0,
            -30.0,
            -30.0 - spacing,
            -30.0 - 2.0 * spacing,
            -30.0 - 3.0 * spacing
        ];
    }

    setupHiddenObject(shapeType, materialName) {
        // Randomize shape and material if set to 'random'
        let mat = materialName;
        if (!mat || mat === 'random') {
            const keys = Object.keys(MATERIALS);
            mat = keys[Math.floor(Math.random() * keys.length)];
        }
        
        let shape = shapeType;
        if (!shape || shape === 'random') {
            const shapes = ['cube', 'sphere', 'cylinder', 'irregular'];
            shape = shapes[Math.floor(Math.random() * shapes.length)];
        }
        
        // Slight offset from origin
        const cx = (Math.random() - 0.5) * 6.0;
        const cy = (Math.random() - 0.5) * 6.0;
        const cz = (Math.random() - 0.5) * 6.0;
        
        this.hiddenObject = {
            shapeType: shape,
            materialName: mat,
            material: MATERIALS[mat],
            center: [cx, cy, cz],
            params: {}
        };
        
        // Select size based on shape
        if (shape === 'cube') {
            this.hiddenObject.params.size = 20.0 + Math.random() * 6.0;
        } else if (shape === 'sphere') {
            this.hiddenObject.params.radius = 10.0 + Math.random() * 3.0;
        } else if (shape === 'cylinder') {
            this.hiddenObject.params.radius = 8.0 + Math.random() * 3.0;
            this.hiddenObject.params.height = 22.0 + Math.random() * 6.0;
        } else if (shape === 'irregular') {
            this.hiddenObject.params.crossWidth = 30.0;
            this.hiddenObject.params.crossThickness = 10.0;
        }
    }

    // Vector Ray-AABB intersection
    intersectAABB(S, D, boxMin, boxMax) {
        let tmin = -Infinity;
        let tmax = Infinity;
        
        for (let i = 0; i < 3; i++) {
            const d = D[i];
            const s = S[i];
            
            if (Math.abs(d) < 1e-9) {
                if (s < boxMin[i] || s > boxMax[i]) return null;
            } else {
                const t1 = (boxMin[i] - s) / d;
                const t2 = (boxMax[i] - s) / d;
                
                const tEntry = Math.min(t1, t2);
                const tExit = Math.max(t1, t2);
                
                tmin = Math.max(tmin, tEntry);
                tmax = Math.min(tmax, tExit);
            }
        }
        
        if (tmin <= tmax && tmax > 0) {
            return { tmin: Math.max(0.0, tmin), tmax: tmax };
        }
        return null;
    }

    // Ray-Sphere intersection
    intersectSphere(S, D, center, radius) {
        // V = S - C
        const Vx = S[0] - center[0];
        const Vy = S[1] - center[1];
        const Vz = S[2] - center[2];
        
        const b = 2.0 * (Vx * D[0] + Vy * D[1] + Vz * D[2]);
        const c = (Vx*Vx + Vy*Vy + Vz*Vz) - radius*radius;
        const disc = b*b - 4.0 * c;
        
        if (disc < 0) return null;
        
        const sqrtDisc = Math.sqrt(disc);
        const t1 = (-b - sqrtDisc) / 2.0;
        const t2 = (-b + sqrtDisc) / 2.0;
        
        if (t2 < 0) return null;
        return { tmin: Math.max(0.0, t1), tmax: t2 };
    }

    // Ray-Cylinder intersection
    intersectCylinder(S, D, center, radius, height) {
        const Cx = center[0];
        const Cy = center[1];
        const Cz = center[2];
        
        const zMin = Cz - height / 2.0;
        const zMax = Cz + height / 2.0;
        
        const Vx = S[0] - Cx;
        const Vy = S[1] - Cy;
        const Dx = D[0];
        const Dy = D[1];
        
        const A = Dx*Dx + Dy*Dy;
        if (A < 1e-9) {
            // Parallel to Z axis
            if (Vx*Vx + Vy*Vy <= radius*radius) {
                if (Math.abs(D[2]) < 1e-9) return null;
                const t1 = (zMin - S[2]) / D[2];
                const t2 = (zMax - S[2]) / D[2];
                return { tmin: Math.min(t1, t2), tmax: Math.max(t1, t2) };
            }
            return null;
        }
        
        const B = 2.0 * (Vx*Dx + Vy*Dy);
        const C_coeff = Vx*Vx + Vy*Vy - radius*radius;
        const disc = B*B - 4.0 * A * C_coeff;
        
        if (disc < 0) return null;
        
        const sqrtDisc = Math.sqrt(disc);
        const tCyl1 = (-B - sqrtDisc) / (2.0 * A);
        const tCyl2 = (-B + sqrtDisc) / (2.0 * A);
        const tCylMin = Math.min(tCyl1, tCyl2);
        const tCylMax = Math.max(tCyl1, tCyl2);
        
        if (Math.abs(D[2]) < 1e-9) {
            if (S[2] >= zMin && S[2] <= zMax) {
                return { tmin: Math.max(0.0, tCylMin), tmax: tCylMax };
            }
            return null;
        }
        
        const tZ1 = (zMin - S[2]) / D[2];
        const tZ2 = (zMax - S[2]) / D[2];
        const tZMin = Math.min(tZ1, tZ2);
        const tZMax = Math.max(tZ1, tZ2);
        
        const tmin = Math.max(tCylMin, tZMin);
        const tmax = Math.min(tCylMax, tZMax);
        
        if (tmin <= tmax && tmax > 0) {
            return { tmin: Math.max(0.0, tmin), tmax: tmax };
        }
        return null;
    }

    getObjectThickness(S, D) {
        const obj = this.hiddenObject;
        if (!obj) return null;
        
        if (obj.shapeType === 'cube') {
            const sz = obj.params.size;
            const bMin = [obj.center[0] - sz/2, obj.center[1] - sz/2, obj.center[2] - sz/2];
            const bMax = [obj.center[0] + sz/2, obj.center[1] + sz/2, obj.center[2] + sz/2];
            return this.intersectAABB(S, D, bMin, bMax);
        } else if (obj.shapeType === 'sphere') {
            return this.intersectSphere(S, D, obj.center, obj.params.radius);
        } else if (obj.shapeType === 'cylinder') {
            return this.intersectCylinder(S, D, obj.center, obj.params.radius, obj.params.height);
        } else if (obj.shapeType === 'irregular') {
            // Union of two boxes forming a cross
            const cx = obj.center[0], cy = obj.center[1], cz = obj.center[2];
            const b1Min = [cx - 5.0, cy - 5.0, cz - 15.0];
            const b1Max = [cx + 5.0, cy + 5.0, cz + 15.0];
            const b2Min = [cx - 15.0, cy - 5.0, cz - 5.0];
            const b2Max = [cx + 15.0, cy + 5.0, cz + 5.0];
            
            const r1 = this.intersectAABB(S, D, b1Min, b1Max);
            const r2 = this.intersectAABB(S, D, b2Min, b2Max);
            
            if (!r1 && !r2) return null;
            if (r1 && !r2) return r1;
            if (!r1 && r2) return r2;
            
            // Overlapping case: union
            const tmin = Math.min(r1.tmin, r2.tmin);
            const tmax = Math.max(r1.tmax, r2.tmax);
            return { tmin: tmin, tmax: tmax };
        }
        return null;
    }

    // Highland Formula scattering calculation
    computeHighlandTheta0(x, X0, p) {
        if (x <= 1e-10) return 0.0;
        const m_mu = 105.66;
        const E = Math.sqrt(p*p + m_mu*m_mu);
        const beta = p / E;
        const beta_p = beta * p;
        
        const ratio = x / X0;
        const logTerm = Math.log(Math.max(1e-10, ratio));
        
        return (13.6 / beta_p) * Math.sqrt(ratio) * (1.0 + 0.038 * logTerm);
    }

    // Standard deviation box scatter helper
    scatterDirection(D, theta_0) {
        if (theta_0 <= 0.0) return [...D];
        
        // Box-Muller transform for Gaussian randoms
        const u1 = Math.random() || 1e-10;
        const u2 = Math.random() || 1e-10;
        const g1 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
        
        const u3 = Math.random() || 1e-10;
        const u4 = Math.random() || 1e-10;
        const g2 = Math.sqrt(-2.0 * Math.log(u3)) * Math.cos(2.0 * Math.PI * u4);
        
        const dtheta1 = g1 * theta_0;
        const dtheta2 = g2 * theta_0;
        
        // Build local frame
        let e1 = [0, 0, 0];
        if (Math.abs(D[0]) < 1e-5 && Math.abs(D[1]) < 1e-5) {
            e1 = [1.0, 0.0, 0.0];
        } else {
            e1 = [-D[1], D[0], 0.0];
            const norm = Math.sqrt(e1[0]*e1[0] + e1[1]*e1[1]);
            e1[0] /= norm;
            e1[1] /= norm;
        }
        
        // e2 = D x e1
        const e2 = [
            D[1]*e1[2] - D[2]*e1[1],
            D[2]*e1[0] - D[0]*e1[2],
            D[0]*e1[1] - D[1]*e1[0]
        ];
        
        const newD = [
            D[0] + dtheta1 * e1[0] + dtheta2 * e2[0],
            D[1] + dtheta1 * e1[1] + dtheta2 * e2[1],
            D[2] + dtheta1 * e1[2] + dtheta2 * e2[2]
        ];
        
        const len = Math.sqrt(newD[0]*newD[0] + newD[1]*newD[1] + newD[2]*newD[2]);
        return [newD[0]/len, newD[1]/len, newD[2]/len];
    }

    simulateSingleMuon() {
        this.muonsSimulated++;
        
        // 1. Target-biased starting position & direction (guarantees 100% reconstructibility)
        const halfWidth = 50.0;
        const margin = 5.0;
        const limitRange = halfWidth - margin; // 45.0 cm
        
        const x1 = (Math.random() - 0.5) * limitRange * 2.0;
        const y1 = (Math.random() - 0.5) * limitRange * 2.0;
        
        const x8 = (Math.random() - 0.5) * limitRange * 2.0;
        const y8 = (Math.random() - 0.5) * limitRange * 2.0;
        
        const dx = x8 - x1;
        const dy = y8 - y1;
        const zPlane1 = this.zPlanes[0];
        const zPlane8 = this.zPlanes[7];
        const dz = zPlane8 - zPlane1; // from Plane 1 to Plane 8
        const len = Math.sqrt(dx*dx + dy*dy + dz*dz);
        
        const ux = dx / len;
        const uy = dy / len;
        const uz = dz / len;
        
        // Project start position back to Z = zPlane1 + 10.0
        const zStart = zPlane1 + 10.0;
        const tStart = (zStart - zPlane1) / uz;
        const x0 = x1 + tStart * ux;
        const y0 = y1 + tStart * uy;
        const z0 = zStart;
        
        let momentum;
        if (this.energyMode === 'manual') {
            momentum = this.manualEnergyGeV * 1000.0;
        } else {
            momentum = 1000.0 + Math.random() * 9000.0; // 1 to 10 GeV/c
        }
        
        let S = [x0, y0, z0];
        let D = [ux, uy, uz];
        
        // Tracks coordinates history for visualization
        const trajPoints = [];
        trajPoints.push([...S]);
        
        // 2. Propagate to Planes 1-4 (Z_planes[0..3])
        const hitCoords = [];
        let hitMask = 0; // bits representing plane hits
        
        for (let d = 0; d < 4; d++) {
            const zp = this.zPlanes[d];
            const t = (zp - S[2]) / D[2];
            const x = S[0] + t * D[0];
            const y = S[1] + t * D[1];
            hitCoords.push([x, y, zp]);
            
            if (x >= -50.0 && x <= 50.0 && y >= -50.0 && y <= 50.0) {
                hitMask |= (1 << d);
            }
        }
        
        trajPoints.push([...hitCoords[3]]); // Plane 4 exit
        
        // 3. Propagate through Container
        const outerMin = [-20, -20, -20];
        const outerMax = [20, 20, 20];
        const innerMin = [-19.5, -19.5, -19.5];
        const innerMax = [19.5, 19.5, 19.5];
        
        const S_plane4 = hitCoords[3];
        const tOuter = this.intersectAABB(S_plane4, D, outerMin, outerMax);
        
        let didIntersectObject = false;
        let objectThickness = 0.0;
        
        if (tOuter) {
            const P_entry = [
                S_plane4[0] + tOuter.tmin * D[0],
                S_plane4[1] + tOuter.tmin * D[1],
                S_plane4[2] + tOuter.tmin * D[2]
            ];
            
            trajPoints.push([...P_entry]);
            
            const tInner = this.intersectAABB(S_plane4, D, innerMin, innerMax);
            if (tInner) {
                // Entry Steel Wall
                const sWall1 = tInner.tmin - tOuter.tmin;
                const theta0_wall1 = this.computeHighlandTheta0(sWall1, this.steelX0, momentum);
                D = this.scatterDirection(D, theta0_wall1);
                
                const P_cavity_entry = [
                    P_entry[0] + sWall1 * D[0],
                    P_entry[1] + sWall1 * D[1],
                    P_entry[2] + sWall1 * D[2]
                ];
                
                // Cavity space with Hidden Object
                const tObj = this.getObjectThickness(P_cavity_entry, D);
                const sCavity = tInner.tmax - tInner.tmin;
                let P_cavity_exit;
                
                if (tObj) {
                    didIntersectObject = true;
                    objectThickness = tObj.tmax - tObj.tmin;
                    
                    const P_obj_entry = [
                        P_cavity_entry[0] + tObj.tmin * D[0],
                        P_cavity_entry[1] + tObj.tmin * D[1],
                        P_cavity_entry[2] + tObj.tmin * D[2]
                    ];
                    
                    trajPoints.push([...P_obj_entry]);
                    
                    // Scatter in hidden object
                    const theta0_obj = this.computeHighlandTheta0(objectThickness, this.hiddenObject.material.radiationLength, momentum);
                    D = this.scatterDirection(D, theta0_obj);
                    
                    const P_obj_exit = [
                        P_obj_entry[0] + objectThickness * D[0],
                        P_obj_entry[1] + objectThickness * D[1],
                        P_obj_entry[2] + objectThickness * D[2]
                    ];
                    
                    trajPoints.push([...P_obj_exit]);
                    
                    const sAir2 = Math.max(0.0, sCavity - tObj.tmax);
                    P_cavity_exit = [
                        P_obj_exit[0] + sAir2 * D[0],
                        P_obj_exit[1] + sAir2 * D[1],
                        P_obj_exit[2] + sAir2 * D[2]
                    ];
                } else {
                    // Scatter in Air
                    const theta0_air = this.computeHighlandTheta0(sCavity, MATERIALS['Air'].radiationLength, momentum);
                    D = this.scatterDirection(D, theta0_air);
                    P_cavity_exit = [
                        P_cavity_entry[0] + sCavity * D[0],
                        P_cavity_entry[1] + sCavity * D[1],
                        P_cavity_entry[2] + sCavity * D[2]
                    ];
                }
                
                // Exit Steel Wall
                const sWall2 = tOuter.tmax - tInner.tmax;
                const theta0_wall2 = this.computeHighlandTheta0(sWall2, this.steelX0, momentum);
                D = this.scatterDirection(D, theta0_wall2);
                
                const P_exit = [
                    P_cavity_exit[0] + sWall2 * D[0],
                    P_cavity_exit[1] + sWall2 * D[1],
                    P_cavity_exit[2] + sWall2 * D[2]
                ];
                
                trajPoints.push([...P_exit]);
                S = P_exit;
            } else {
                // Skims wall only
                const sSteel = tOuter.tmax - tOuter.tmin;
                const theta0_steel = this.computeHighlandTheta0(sSteel, this.steelX0, momentum);
                D = this.scatterDirection(D, theta0_steel);
                const P_exit = [
                    P_entry[0] + sSteel * D[0],
                    P_entry[1] + sSteel * D[1],
                    P_entry[2] + sSteel * D[2]
                ];
                trajPoints.push([...P_exit]);
                S = P_exit;
            }
        } else {
            // Misses container completely
            const tToZ = (-20.0 - S_plane4[2]) / D[2];
            const P_fake_exit = [
                S_plane4[0] + tToZ * D[0],
                S_plane4[1] + tToZ * D[1],
                -20.0
            ];
            trajPoints.push([...P_fake_exit]);
            S = P_fake_exit;
        }
        
        // 4. Propagate to Planes 5-8
        for (let d = 4; d < 8; d++) {
            const zp = this.zPlanes[d];
            const t = (zp - S[2]) / D[2];
            const x = S[0] + t * D[0];
            const y = S[1] + t * D[1];
            hitCoords.push([x, y, zp]);
            
            if (x >= -50.0 && x <= 50.0 && y >= -50.0 && y <= 50.0) {
                hitMask |= (1 << d);
            }
        }
        
        trajPoints.push([...hitCoords[7]]); // Plane 8 exit
        
        // 5. Track Reconstruction
        const isReconstructible = (hitMask === 255); // hit all 8 planes
        let scatAngle = 0.0;
        let shift = 0.0;
        let pocaPoint = null;
        let hitPixels = [];
        
        if (isReconstructible) {
            this.muonsReconstructed++;
            
            // Linear regression on Planes 1-4
            const fitIn = this.fitLineLeastSquares(hitCoords.slice(0, 4));
            // Linear regression on Planes 5-8
            const fitOut = this.fitLineLeastSquares(hitCoords.slice(4, 8));
            
            // Reconstructed direction vectors (downward)
            const dirIn = [-fitIn.slopeX, -fitIn.slopeY, -1.0];
            const lenIn = Math.sqrt(dirIn[0]*dirIn[0] + dirIn[1]*dirIn[1] + dirIn[2]*dirIn[2]);
            dirIn[0] /= lenIn; dirIn[1] /= lenIn; dirIn[2] /= lenIn;
            
            const dirOut = [-fitOut.slopeX, -fitOut.slopeY, -1.0];
            const lenOut = Math.sqrt(dirOut[0]*dirOut[0] + dirOut[1]*dirOut[1] + dirOut[2]*dirOut[2]);
            dirOut[0] /= lenOut; dirOut[1] /= lenOut; dirOut[2] /= lenOut;
            
            // Scattering angle
            let dot = dirIn[0]*dirOut[0] + dirIn[1]*dirOut[1] + dirIn[2]*dirOut[2];
            dot = Math.max(-1.0, Math.min(1.0, dot));
            scatAngle = Math.acos(dot);
            
            // Centroid displacement on Plane 5 (Z = -30.0)
            const z_p5 = this.zPlanes[4];
            const xPred = fitIn.slopeX * z_p5 + fitIn.interceptX;
            const yPred = fitIn.slopeY * z_p5 + fitIn.interceptY;
            const xMeas = hitCoords[4][0];
            const yMeas = hitCoords[4][1];
            shift = Math.sqrt((xMeas - xPred)**2 + (yMeas - yPred)**2);
            
            // POCA calculation
            pocaPoint = this.computePOCA(fitIn.centroid, dirIn, fitOut.centroid, dirOut);
            
            // Accumulate Voxel Density if POCA inside container and angle is significant
            if (pocaPoint && scatAngle > 0.005) {
                const px = pocaPoint[0], py = pocaPoint[1], pz = pocaPoint[2];
                if (px >= -20 && px < 20 && py >= -20 && py < 20 && pz >= -20 && pz < 20) {
                    const ix = Math.floor(px + 20);
                    const iy = Math.floor(py + 20);
                    const iz = Math.floor(pz + 20);
                    
                    const idx = ix + iy * 40 + iz * 1600;
                    
                    // Increment weight: angle squared (proportional to 1/X0)
                    this.densityGrid[idx] += (scatAngle * scatAngle);
                    this.hitGrid[idx]++;
                    
                    if (this.densityGrid[idx] > this.maxVoxelVal) {
                        this.maxVoxelVal = this.densityGrid[idx];
                    }
                    
                    // Add POCA to cache
                    this.recentPOCAs.push([px, py, pz, scatAngle]);
                    if (this.recentPOCAs.length > 1000) this.recentPOCAs.shift();
                }
            }
            
            // Build Pixel Hits list
            hitCoords.forEach((hc, d) => {
                const half = 50.0;
                const px = Math.min(Math.max(Math.floor((hc[0] + half) / 1.0), 0), 99);
                const py = Math.min(Math.max(Math.floor((hc[1] + half) / 1.0), 0), 99);
                
                // 1cm x 1cm pixel centroid coordinates
                const xCent = -half + px + 0.5;
                const yCent = -half + py + 0.5;
                
                 // 2D distance from continuous hit (hc[0], hc[1]) to discrete pixel centroid (xCent, yCent)
                const offset = Math.sqrt((hc[0] - xCent)**2 + (hc[1] - yCent)**2);
                
                // Accumulate digitization offset for this plate
                this.planeOffsetsSum[d] += offset;
                this.planeOffsetsCount[d]++;
                
                hitPixels.push({
                    planeId: d + 1,
                    px: px,
                    py: py,
                    z: hc[2],
                    x: hc[0],
                    y: hc[1],
                    xCent: xCent,
                    yCent: yCent,
                    offset: offset
                });
            });
            
            // Classify target
            if (didIntersectObject && objectThickness > 0) {
                this.intersectCount++;
                this.avgMeasuredAngle = (this.avgMeasuredAngle * (this.intersectCount - 1) + scatAngle) / this.intersectCount;
                this.avgMeasuredShift = (this.avgMeasuredShift * (this.intersectCount - 1) + shift) / this.intersectCount;
                this.accMomenta = (this.accMomenta * (this.intersectCount - 1) + momentum) / this.intersectCount;
                this.accThickness = (this.accThickness * (this.intersectCount - 1) + objectThickness) / this.intersectCount;
                
                // Accumulate expected values for each material for this specific muon's momentum & thickness
                const thickSteel1 = 0.5 / Math.max(1e-5, Math.abs(D[2])); // top wall adjusted for angle
                const thickSteel2 = 0.5 / Math.max(1e-5, Math.abs(D[2])); // bottom wall adjusted for angle
                const z_p5 = this.zPlanes[4];
                const L_entry = Math.abs(20.0 - z_p5);
                const L_exit = Math.abs(-20.0 - z_p5);
                const L_obj = Math.abs(this.hiddenObject.center[2] - z_p5);
                const m_mu = 105.66;
                const E = Math.sqrt(momentum*momentum + m_mu*m_mu);
                const beta = momentum / E;
                const beta_p = beta * momentum;
                
                // Steel entry wall scattering
                const ratioSteel1 = thickSteel1 / 1.76;
                const logTermSteel1 = ratioSteel1 > 1e-10 ? Math.log(ratioSteel1) : 0.0;
                const thetaSteel1 = ratioSteel1 > 1e-10 ? (13.6 / beta_p) * Math.sqrt(ratioSteel1) * (1.0 + 0.038 * logTermSteel1) : 0.0;
                
                // Steel exit wall scattering
                const ratioSteel2 = thickSteel2 / 1.76;
                const logTermSteel2 = ratioSteel2 > 1e-10 ? Math.log(ratioSteel2) : 0.0;
                const thetaSteel2 = ratioSteel2 > 1e-10 ? (13.6 / beta_p) * Math.sqrt(ratioSteel2) * (1.0 + 0.038 * logTermSteel2) : 0.0;
                
                Object.keys(MATERIALS).forEach(matName => {
                    const material = MATERIALS[matName];
                    const ratioObj = objectThickness / material.radiationLength;
                    const logTermObj = ratioObj > 1e-10 ? Math.log(ratioObj) : 0.0;
                    const thetaObj = ratioObj > 1e-10 ? (13.6 / beta_p) * Math.sqrt(ratioObj) * (1.0 + 0.038 * logTermObj) : 0.0;
                    
                    const thetaTotal = Math.sqrt(thetaObj*thetaObj + thetaSteel1*thetaSteel1 + thetaSteel2*thetaSteel2);
                    
                    // Rayleigh mean scattering angle = theta_0 * sqrt(pi/2)
                    this.accExpectedAngle[matName] += thetaTotal * Math.sqrt(Math.PI / 2.0);
                    
                    // Rayleigh mean centroid displacement in quadrature
                    const varShift = (thetaSteel1 * L_entry)**2 + (thetaSteel2 * L_exit)**2 + (thetaObj * L_obj)**2;
                    this.accExpectedShift[matName] += Math.sqrt(varShift) * Math.sqrt(Math.PI / 2.0);
                });
                
                this.updateClassification();
            }
            
            // Store trace details
            const trackDetail = {
                muonId: this.muonsSimulated,
                momentum: momentum,
                scatAngle: scatAngle,
                shift: shift,
                hitPixels: hitPixels,
                trajPoints: trajPoints,
                incomingFit: { slopeX: fitIn.slopeX, interceptX: fitIn.interceptX, slopeY: fitIn.slopeY, interceptY: fitIn.interceptY },
                outgoingFit: { slopeX: fitOut.slopeX, interceptX: fitOut.interceptX, slopeY: fitOut.slopeY, interceptY: fitOut.interceptY }
            };
            
            this.recentTracks.push(trackDetail);
            if (this.recentTracks.length > 150) this.recentTracks.shift();
            
            return trackDetail;
        }
        
        return null;
    }

    fitLineLeastSquares(points) {
        // points: array of 4 coordinates [x, y, z]
        let meanZ = 0.0;
        let meanX = 0.0;
        let meanY = 0.0;
        
        points.forEach(p => {
            meanZ += p[2];
            meanX += p[0];
            meanY += p[1];
        });
        
        meanZ /= 4.0;
        meanX /= 4.0;
        meanY /= 4.0;
        
        let numX = 0.0, numY = 0.0, denom = 0.0;
        points.forEach(p => {
            const zd = p[2] - meanZ;
            numX += zd * (p[0] - meanX);
            numY += zd * (p[1] - meanY);
            denom += zd * zd;
        });
        
        const slopeX = numX / denom;
        const slopeY = numY / denom;
        
        const interceptX = meanX - slopeX * meanZ;
        const interceptY = meanY - slopeY * meanZ;
        
        return {
            slopeX: slopeX, interceptX: interceptX,
            slopeY: slopeY, interceptY: interceptY,
            centroid: [meanX, meanY, meanZ]
        };
    }

    computePOCA(C1, u, C2, v) {
        const w0 = [C1[0] - C2[0], C1[1] - C2[1], C1[2] - C2[2]];
        
        const b = u[0]*v[0] + u[1]*v[1] + u[2]*v[2];
        const d = u[0]*w0[0] + u[1]*w0[1] + u[2]*w0[2];
        const e = v[0]*w0[0] + v[1]*w0[1] + v[2]*w0[2];
        
        const denom = 1.0 - b*b;
        if (denom < 1e-9) return null; // Parallel tracks
        
        const t1 = (b * e - d) / denom;
        const t2 = (e - b * d) / denom;
        
        const P1 = [C1[0] + t1 * u[0], C1[1] + t1 * u[1], C1[2] + t1 * u[2]];
        const P2 = [C2[0] + t2 * v[0], C2[1] + t2 * v[1], C2[2] + t2 * v[2]];
        
        return [
            0.5 * (P1[0] + P2[0]),
            0.5 * (P1[1] + P2[1]),
            0.5 * (P1[2] + P2[2]),
            Math.sqrt((P1[0]-P2[0])**2 + (P1[1]-P2[1])**2 + (P1[2]-P2[2])**2) // track distance
        ];
    }

    updateClassification() {
        if (this.intersectCount < 5) return;
        
        const scores = {};
        
        Object.keys(MATERIALS).forEach(matName => {
            const expAvgAngle = this.accExpectedAngle[matName] / this.intersectCount;
            const expAvgShift = this.accExpectedShift[matName] / this.intersectCount;
            
            const errAngle = Math.abs(this.avgMeasuredAngle - expAvgAngle) / (expAvgAngle + 1e-9);
            const errShift = Math.abs(this.avgMeasuredShift - expAvgShift) / (expAvgShift + 1e-9);
            
            scores[matName] = 0.7 * errAngle + 0.3 * errShift;
        });
        
        // Find minimum score for stable softmax
        const minScore = Math.min(...Object.values(scores));
        
        // Softmax conversion
        const temp = 0.05;
        let sumWeights = 0.0;
        const weights = {};
        
        Object.keys(scores).forEach(matName => {
            const w = Math.exp(-(scores[matName] - minScore) / temp);
            weights[matName] = w;
            sumWeights += w;
        });
        
        let bestConf = 0.0;
        let bestMat = "Air";
        
        Object.keys(weights).forEach(matName => {
            const conf = weights[matName] / sumWeights;
            this.materialConfidences[matName] = conf;
            if (conf > bestConf) {
                bestConf = conf;
                bestMat = matName;
            }
        });
        
        this.predictedMaterial = bestMat;
        this.classificationConfidence = bestConf;
    }

    reconstructShapeAndSize() {
        if (this.recentPOCAs.length < 10) {
            return { sizeText: "Calibrating...", centroid: [0, 0, 0], dims: {} };
        }
        
        const pts = this.recentPOCAs;
        
        // Calculate centroid (mean)
        let sumX = 0, sumY = 0, sumZ = 0;
        pts.forEach(p => {
            sumX += p[0];
            sumY += p[1];
            sumZ += p[2];
        });
        const mx = sumX / pts.length;
        const my = sumY / pts.length;
        const mz = sumZ / pts.length;
        
        // Calculate standard deviations
        let varX = 0, varY = 0, varZ = 0;
        pts.forEach(p => {
            varX += (p[0] - mx)**2;
            varY += (p[1] - my)**2;
            varZ += (p[2] - mz)**2;
        });
        const stdX = Math.sqrt(varX / pts.length);
        const stdY = Math.sqrt(varY / pts.length);
        const stdZ = Math.sqrt(varZ / pts.length);
        
        // Calculate bounding size along each axis (3.46 * stdDev)
        const w = Math.min(40.0, Math.max(8.0, 3.46 * stdX));
        const d = Math.min(40.0, Math.max(8.0, 3.46 * stdY));
        const h = Math.min(40.0, Math.max(8.0, 3.46 * stdZ));
        
        const sizeText = `${w.toFixed(1)} x ${d.toFixed(1)} x ${h.toFixed(1)} cm`;
        
        return { sizeText: sizeText, centroid: [mx, my, mz], dims: { w: w, d: d, h: h } };
    }
}
