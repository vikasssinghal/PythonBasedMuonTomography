// Three.js 3D WebGL Rendering for Muon Tomography Dashboard

class ThreeRenderer {
    constructor(canvasContainerId) {
        this.container = document.getElementById(canvasContainerId);
        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;
        
        this.setupScene();
        this.setupLights();
        this.setupDetectorGeometry();
        this.setupInteractionObjects();
        this.setupVoxelVisuals();
        
        this.activeTracks = [];
        this.pocaPoints = [];
        
        // Persistent Hit Points System
        this.persistentHitPositions = [];
        this.persistentHitsGeometry = new THREE.BufferGeometry();
        this.persistentHitsMaterial = new THREE.PointsMaterial({
            color: 0xffcc00, // glowing amber/yellow
            size: 1.0,
            transparent: true,
            opacity: 0.85,
            sizeAttenuation: true
        });
        this.persistentHitsMesh = new THREE.Points(this.persistentHitsGeometry, this.persistentHitsMaterial);
        this.scene.add(this.persistentHitsMesh);
        
        // Persistent Track Lines System
        this.persistentTrackPositionsIn = [];
        this.persistentTrackPositionsOut = [];
        this.persistentTracksGeomIn = new THREE.BufferGeometry();
        this.persistentTracksGeomOut = new THREE.BufferGeometry();
        
        this.persistentTracksMatIn = new THREE.LineBasicMaterial({
            color: 0x1e90ff, // dodger blue
            transparent: true,
            opacity: 0.15,   // low opacity to form a nice particle cloud
            linewidth: 1
        });
        
        this.persistentTracksMatOut = new THREE.LineBasicMaterial({
            color: 0xff0080, // hot pink
            transparent: true,
            opacity: 0.15,
            linewidth: 1
        });
        
        this.persistentTracksMeshIn = new THREE.LineSegments(this.persistentTracksGeomIn, this.persistentTracksMatIn);
        this.persistentTracksMeshOut = new THREE.LineSegments(this.persistentTracksGeomOut, this.persistentTracksMatOut);
        
        this.scene.add(this.persistentTracksMeshIn);
        this.scene.add(this.persistentTracksMeshOut);
        
        // Reconstructed 3D Shape Group
        this.reconstructedGroup = new THREE.Group();
        this.scene.add(this.reconstructedGroup);
        
        window.addEventListener('resize', () => this.onWindowResize());
    }

    setupScene() {
        // Scene & Camera
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a0d); // deep dark grey
        
        this.camera = new THREE.PerspectiveCamera(50, this.width / this.height, 0.1, 1000);
        this.camera.position.set(130, 90, 160);
        
        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.width, this.height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);
        
        // Controls
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.maxPolarAngle = Math.PI / 2.0 + 0.1; // allow slightly below ground view
        
        // Grid helper at floor (Z = -90)
        const gridHelper = new THREE.GridHelper(160, 32, 0x3a3a4a, 0x1f1f28);
        gridHelper.position.y = -85;
        this.scene.add(gridHelper);
    }

    setupLights() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);
        
        const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.6);
        dirLight1.position.set(80, 150, 80);
        this.scene.add(dirLight1);
        
        const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.2);
        dirLight2.position.set(-80, -100, -80);
        this.scene.add(dirLight2);
    }

    setupDetectorGeometry() {
        this.detectorPlanesGroup = new THREE.Group();
        this.scene.add(this.detectorPlanesGroup);
        
        this.fiberGridsGroup = new THREE.Group();
        this.scene.add(this.fiberGridsGroup);
        
        this.mapmtGroup = new THREE.Group();
        this.scene.add(this.mapmtGroup);
        
        this.planesGeometries = [];
        this.fiberLines = [];
    }

    rebuildDetectorPlanes(zPlanes) {
        // Clear old geometries
        while(this.detectorPlanesGroup.children.length > 0) {
            this.detectorPlanesGroup.remove(this.detectorPlanesGroup.children[0]);
        }
        while(this.fiberGridsGroup.children.length > 0) {
            this.fiberGridsGroup.remove(this.fiberGridsGroup.children[0]);
        }
        while(this.mapmtGroup.children.length > 0) {
            this.mapmtGroup.remove(this.mapmtGroup.children[0]);
        }
        
        this.planesGeometries = [];
        this.fiberLines = [];
        
        // 1. Create transparent scintillator slabs (100x100x7.8 cm)
        const slabGeom = new THREE.BoxGeometry(100, 7.8, 100);
        const slabMat = new THREE.MeshPhongMaterial({
            color: 0x1a2e40, // deep blue
            transparent: true,
            opacity: 0.08,
            shininess: 30,
            specular: 0xffffff,
            depthWrite: false
        });
        
        const mapmtGeom = new THREE.BoxGeometry(8, 8, 4);
        const mapmtMat = new THREE.MeshPhongMaterial({ color: 0x222226, shininess: 80 });
        
        const gridVerticesX = [];
        const gridVerticesY = [];
        const curveVerticesX = [];
        const curveVerticesY = [];
        
        zPlanes.forEach((zp, idx) => {
            // Scintillator Slab Mesh
            const slab = new THREE.Mesh(slabGeom, slabMat);
            slab.position.set(0, zp, 0);
            this.detectorPlanesGroup.add(slab);
            
            // Slab Outlines
            const edges = new THREE.EdgesGeometry(slabGeom);
            const outline = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x3fa0f0, transparent: true, opacity: 0.25 }));
            outline.position.set(0, zp, 0);
            this.detectorPlanesGroup.add(outline);
            
            // MAPMT modules
            const mapmtX = new THREE.Mesh(mapmtGeom, mapmtMat);
            mapmtX.position.set(0, zp, 56);
            this.mapmtGroup.add(mapmtX);
            
            const mapmtY = new THREE.Mesh(mapmtGeom, mapmtMat);
            mapmtY.position.set(56, zp, 0);
            mapmtY.rotation.y = Math.PI / 2.0;
            this.mapmtGroup.add(mapmtY);
            
            // Create 1cm x 1cm crossed grids
            // X-fibers run parallel to Z (from Z=-50 to Z=50), spaced at x = -49.5 to 49.5
            for (let i = 0; i < 100; i++) {
                const x = -50.0 + i + 0.5;
                // Add active grid segment
                gridVerticesX.push(x, zp + 0.1, -50.0);
                gridVerticesX.push(x, zp + 0.1, 50.0);
                
                // Curve segment from (x, zp + 0.1, 50) to MAPMT face at (0, zp, 56)
                const xMapmt = 0.0;
                const zMapmt = 54.0;
                const yMapmt = zp;
                
                let lastPt = [x, zp + 0.1, 50.0];
                for (let k = 1; k <= 8; k++) {
                    const t = k / 8.0;
                    const cpX = x;
                    const cpY = zp + 0.1;
                    const cpZ = 52.0;
                    
                    const nextX = (1-t)**2 * x + 2*(1-t)*t * cpX + t**2 * (xMapmt + (i - 49.5) * 0.06); // fan into MAPMT face
                    const nextY = (1-t)**2 * (zp + 0.1) + 2*(1-t)*t * cpY + t**2 * yMapmt;
                    const nextZ = (1-t)**2 * 50.0 + 2*(1-t)*t * cpZ + t**2 * zMapmt;
                    
                    curveVerticesX.push(lastPt[0], lastPt[1], lastPt[2]);
                    curveVerticesX.push(nextX, nextY, nextZ);
                    lastPt = [nextX, nextY, nextZ];
                }
            }
            
            // Y-fibers run parallel to X (from X=-50 to X=50), spaced at z = -49.5 to 49.5
            for (let j = 0; j < 100; j++) {
                const z = -50.0 + j + 0.5;
                // Add active grid segment
                gridVerticesY.push(-50.0, zp - 0.1, z);
                gridVerticesY.push(50.0, zp - 0.1, z);
                
                // Curve segment from (50, zp - 0.1, z) to MAPMT face at (56, zp, 0)
                const xMapmt = 54.0;
                const zMapmt = 0.0;
                const yMapmt = zp;
                
                let lastPt = [50.0, zp - 0.1, z];
                for (let k = 1; k <= 8; k++) {
                    const t = k / 8.0;
                    const cpX = 52.0;
                    const cpY = zp - 0.1;
                    const cpZ = z;
                    
                    const nextX = (1-t)**2 * 50.0 + 2*(1-t)*t * cpX + t**2 * xMapmt;
                    const nextY = (1-t)**2 * (zp - 0.1) + 2*(1-t)*t * cpY + t**2 * yMapmt;
                    const nextZ = (1-t)**2 * z + 2*(1-t)*t * cpZ + t**2 * (zMapmt + (j - 49.5) * 0.06); // fan into MAPMT face
                    
                    curveVerticesY.push(lastPt[0], lastPt[1], lastPt[2]);
                    curveVerticesY.push(nextX, nextY, nextZ);
                    lastPt = [nextX, nextY, nextZ];
                }
            }
        });
        
        // 2. Create high-density merged grid meshes
        const geomGridX = new THREE.BufferGeometry();
        geomGridX.setAttribute('position', new THREE.Float32BufferAttribute(gridVerticesX, 3));
        const matGridX = new THREE.LineBasicMaterial({ color: 0x00d2ff, transparent: true, opacity: 0.12 });
        const gridSegmentsX = new THREE.LineSegments(geomGridX, matGridX);
        this.fiberGridsGroup.add(gridSegmentsX);
        
        const geomGridY = new THREE.BufferGeometry();
        geomGridY.setAttribute('position', new THREE.Float32BufferAttribute(gridVerticesY, 3));
        const matGridY = new THREE.LineBasicMaterial({ color: 0xff0080, transparent: true, opacity: 0.12 });
        const gridSegmentsY = new THREE.LineSegments(geomGridY, matGridY);
        this.fiberGridsGroup.add(gridSegmentsY);
        
        // 3. Create high-density merged curve meshes (running to MAPMT faces)
        const geomCurveX = new THREE.BufferGeometry();
        geomCurveX.setAttribute('position', new THREE.Float32BufferAttribute(curveVerticesX, 3));
        const matCurveX = new THREE.LineBasicMaterial({ color: 0x00d2ff, transparent: true, opacity: 0.08 });
        const curveSegmentsX = new THREE.LineSegments(geomCurveX, matCurveX);
        this.fiberGridsGroup.add(curveSegmentsX);
        
        const geomCurveY = new THREE.BufferGeometry();
        geomCurveY.setAttribute('position', new THREE.Float32BufferAttribute(curveVerticesY, 3));
        const matCurveY = new THREE.LineBasicMaterial({ color: 0xff0080, transparent: true, opacity: 0.08 });
        const curveSegmentsY = new THREE.LineSegments(geomCurveY, matCurveY);
        this.fiberGridsGroup.add(curveSegmentsY);
    }

    setupInteractionObjects() {
        // Steel Container
        const containerGeom = new THREE.BoxGeometry(40, 40, 40);
        const containerMat = new THREE.MeshPhongMaterial({
            color: 0xcccccc,
            transparent: true,
            opacity: 0.1,
            depthWrite: false,
            shininess: 10
        });
        this.containerMesh = new THREE.Mesh(containerGeom, containerMat);
        this.containerMesh.position.set(0, 0, 0);
        this.scene.add(this.containerMesh);
        
        // Container Wireframe
        const edges = new THREE.EdgesGeometry(containerGeom);
        this.containerFrame = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x888888, width: 2 }));
        this.containerFrame.position.set(0, 0, 0);
        this.scene.add(this.containerFrame);
        
        // Target Object Group
        this.targetGroup = new THREE.Group();
        this.scene.add(this.targetGroup);
        
        this.hiddenObjectMesh = null;
    }

    updateHiddenObjectVisuals(obj, showOverride = false) {
        // Clear old mesh
        if (this.hiddenObjectMesh) {
            this.targetGroup.remove(this.hiddenObjectMesh);
            this.hiddenObjectMesh = null;
        }
        
        if (!obj) return;
        
        // Determine object opacity and color
        // If hidden and showOverride is false, render very faint grey wireframe box
        const isHidden = !showOverride;
        const color = isHidden ? 0x444444 : obj.material.color;
        const opacity = isHidden ? 0.05 : 0.45;
        
        const mat = new THREE.MeshPhongMaterial({
            color: color,
            transparent: true,
            opacity: opacity,
            shininess: isHidden ? 0 : 50,
            depthWrite: !isHidden
        });
        
        let geom;
        if (obj.shapeType === 'cube') {
            const sz = obj.params.size;
            geom = new THREE.BoxGeometry(sz, sz, sz);
            this.hiddenObjectMesh = new THREE.Mesh(geom, mat);
        } else if (obj.shapeType === 'sphere') {
            geom = new THREE.SphereGeometry(obj.params.radius, 32, 32);
            this.hiddenObjectMesh = new THREE.Mesh(geom, mat);
        } else if (obj.shapeType === 'cylinder') {
            geom = new THREE.CylinderGeometry(obj.params.radius, obj.params.radius, obj.params.height, 32);
            this.hiddenObjectMesh = new THREE.Mesh(geom, mat);
            // Cylinders in Three.js are aligned along Y, which matches Z in physics
        } else if (obj.shapeType === 'irregular') {
            // 3D Cross
            geom = new THREE.BoxGeometry(10, 30, 10);
            const mesh1 = new THREE.Mesh(geom, mat);
            
            const geom2 = new THREE.BoxGeometry(30, 10, 10);
            const mesh2 = new THREE.Mesh(geom2, mat);
            
            const crossGroup = new THREE.Group();
            crossGroup.add(mesh1);
            crossGroup.add(mesh2);
            this.hiddenObjectMesh = crossGroup;
        }
        
        if (this.hiddenObjectMesh) {
            this.hiddenObjectMesh.position.set(obj.center[0], obj.center[2], obj.center[1]); // X, Z, Y
            this.targetGroup.add(this.hiddenObjectMesh);
            
            if (isHidden) {
                // Add faint wireframe
                const edges = new THREE.EdgesGeometry(geom);
                const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x555555, transparent: true, opacity: 0.15 }));
                this.hiddenObjectMesh.add(line);
            }
        }
    }

    setupVoxelVisuals() {
        this.voxelGroup = new THREE.Group();
        this.scene.add(this.voxelGroup);
        
        // We will represent voxels using THREE.Points for instant 60 FPS rendering
        this.voxelGeometry = new THREE.BufferGeometry();
        this.voxelPositions = [];
        this.voxelColors = [];
        this.voxelSizes = [];
        
        const pMat = new THREE.PointsMaterial({
            size: 2.0,
            vertexColors: true,
            transparent: true,
            opacity: 0.55,
            sizeAttenuation: true
        });
        
        this.voxelPoints = new THREE.Points(this.voxelGeometry, pMat);
        this.voxelGroup.add(this.voxelPoints);
        
        this.pocaGroup = new THREE.Group();
        this.scene.add(this.pocaGroup);
        
        // POCA points material
        this.pocaGeometry = new THREE.BufferGeometry();
        this.pocaPositions = [];
        this.pocaMat = new THREE.PointsMaterial({
            size: 1.5,
            color: 0xff0000,
            transparent: true,
            opacity: 0.8
        });
        this.pocaMesh = new THREE.Points(this.pocaGeometry, this.pocaMat);
        this.pocaGroup.add(this.pocaMesh);
    }

    updateReconstructionVisuals(physics) {
        // 1. Update Voxels
        const maxVal = physics.maxVoxelVal || 1.0;
        const size = physics.voxelSize;
        const halfCont = physics.containerSize / 2.0;
        const numVox = physics.numVoxels;
        
        const posArr = [];
        const colorArr = [];
        
        const threshold = maxVal * 0.05;
        
        // We scan the density grid to locate active voxels
        for (let iz = 0; iz < numVox; iz++) {
            for (let iy = 0; iy < numVox; iy++) {
                for (let ix = 0; ix < numVox; ix++) {
                    const idx = ix + iy * 40 + iz * 1600;
                    const val = physics.densityGrid[idx];
                    
                    if (val > threshold) {
                        const px = -halfCont + ix * size + 0.5 * size;
                        const py = -halfCont + iy * size + 0.5 * size;
                        const pz = -halfCont + iz * size + 0.5 * size;
                        
                        // Pos in ThreeJS coordinates (X, Z, Y -> X, Z, Y)
                        // Physics X -> Three.js X
                        // Physics Y -> Three.js Z
                        // Physics Z -> Three.js Y
                        posArr.push(px, pz, py);
                        
                        // Color mapping Yellow-Orange-Red
                        const intensity = val / maxVal;
                        
                        const color = new THREE.Color();
                        // Mix Yellow (1.0, 1.0, 0.0) to Red (1.0, 0.0, 0.0)
                        color.setHSL(0.16 * (1.0 - intensity), 1.0, 0.5);
                        colorArr.push(color.r, color.g, color.b);
                    }
                }
            }
        }
        
        this.voxelGeometry.setAttribute('position', new THREE.Float32BufferAttribute(posArr, 3));
        this.voxelGeometry.setAttribute('color', new THREE.Float32BufferAttribute(colorArr, 3));
        this.voxelGeometry.computeBoundingSphere();
        
        // 2. Update POCA Points
        const pocaPosArr = [];
        physics.recentPOCAs.forEach(pt => {
            pocaPosArr.push(pt[0], pt[2], pt[1]); // X, Z, Y
        });
        
        this.pocaGeometry.setAttribute('position', new THREE.Float32BufferAttribute(pocaPosArr, 3));
        this.pocaGeometry.computeBoundingSphere();
    }

    addPersistentTrackAndHits(track) {
        if (!track) return;
        
        // 1. Push fitted incoming track to persistent line segment buffer
        const fitIn = track.incomingFit;
        const xInStart = fitIn.slopeX * 85.0 + fitIn.interceptX;
        const yInStart = fitIn.slopeY * 85.0 + fitIn.interceptY;
        const xInEnd = fitIn.slopeX * 20.0 + fitIn.interceptX;
        const yInEnd = fitIn.slopeY * 20.0 + fitIn.interceptY;
        
        this.persistentTrackPositionsIn.push(xInStart, 85.0, yInStart);
        this.persistentTrackPositionsIn.push(xInEnd, 20.0, yInEnd);
        
        // 2. Push fitted outgoing track to persistent line segment buffer
        const fitOut = track.outgoingFit;
        const xOutStart = fitOut.slopeX * -20.0 + fitOut.interceptX;
        const yOutStart = fitOut.slopeY * -20.0 + fitOut.interceptY;
        const xOutEnd = fitOut.slopeX * -85.0 + fitOut.interceptX;
        const yOutEnd = fitOut.slopeY * -85.0 + fitOut.interceptY;
        
        this.persistentTrackPositionsOut.push(xOutStart, -20.0, yOutStart);
        this.persistentTrackPositionsOut.push(xOutEnd, -85.0, yOutEnd);
        
        // 3. Push hit points to persistent hits system
        track.hitPixels.forEach(hp => {
            const half = 50.0;
            const hx = -half + hp.px + 0.5;
            const hy = hp.z;
            const hz = -half + hp.py + 0.5;
            this.persistentHitPositions.push(hx, hy, hz);
        });
        
        // Update geometries
        this.persistentTracksGeomIn.setAttribute(
            'position',
            new THREE.Float32BufferAttribute(this.persistentTrackPositionsIn, 3)
        );
        this.persistentTracksGeomIn.computeBoundingSphere();
        
        this.persistentTracksGeomOut.setAttribute(
            'position',
            new THREE.Float32BufferAttribute(this.persistentTrackPositionsOut, 3)
        );
        this.persistentTracksGeomOut.computeBoundingSphere();
        
        this.persistentHitsGeometry.setAttribute(
            'position',
            new THREE.Float32BufferAttribute(this.persistentHitPositions, 3)
        );
        this.persistentHitsGeometry.computeBoundingSphere();
    }

    animateMuonTrack(track, callback) {
        if (!track) return;
        
        const muonId = track.muonId;
        const scatAngleMrad = (track.scatAngle * 1000.0).toFixed(2);
        const shiftVal = track.shift.toFixed(3);
        const pGev = (track.momentum / 1000.0).toFixed(2);
        const avgOffset = (track.hitPixels.reduce((sum, hp) => sum + hp.offset, 0) / 8.0).toFixed(3);
        const fitIn = track.incomingFit;
        const fitOut = track.outgoingFit;
        
        // Add detailed hit log to console UI
        const logFeed = document.getElementById('log-feed');
        if (logFeed) {
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `<span class="tag tag-cyan">Muon #${muonId}</span> momentum: ${pGev} GeV/c, scattering angle: <span class="tag tag-pink">${scatAngleMrad} mrad</span>, avg pixel offset: <span class="tag tag-cyan">${avgOffset} cm</span>, shift: ${shiftVal} cm`;
            logFeed.insertBefore(entry, logFeed.firstChild);
            
            // Limit log list size to 50
            if (logFeed.children.length > 50) logFeed.removeChild(logFeed.lastChild);
        }
        
        // 1. Create Glowing Muon Particle (Sphere)
        const partGeom = new THREE.SphereGeometry(1.2, 8, 8);
        const partMat = new THREE.MeshBasicMaterial({ color: 0xffff00 });
        const particle = new THREE.Mesh(partGeom, partMat);
        this.scene.add(particle);
        
        // 2. Create Muon Track Lines
        // Incoming Track (Plane 1 to Container Entry)
        // Outgoing Track (Container Exit to Plane 8)
        const traj = track.trajPoints;
        
        // Draw incoming segment (fitted track from Z=85 down to Z=20)
        const inPoints = [
            new THREE.Vector3(fitIn.slopeX * 85.0 + fitIn.interceptX, 85.0, fitIn.slopeY * 85.0 + fitIn.interceptY),
            new THREE.Vector3(fitIn.slopeX * 20.0 + fitIn.interceptX, 20.0, fitIn.slopeY * 20.0 + fitIn.interceptY)
        ];
        const inGeom = new THREE.BufferGeometry().setFromPoints(inPoints);
        const inMat = new THREE.LineBasicMaterial({ color: 0x1e90ff, linewidth: 2, transparent: true, opacity: 0.75 });
        const inLine = new THREE.Line(inGeom, inMat);
        this.scene.add(inLine);
        
        // Draw scattered outgoing segment (fitted track from Z=-20 down to Z=-85)
        const outPoints = [
            new THREE.Vector3(fitOut.slopeX * -20.0 + fitOut.interceptX, -20.0, fitOut.slopeY * -20.0 + fitOut.interceptY),
            new THREE.Vector3(fitOut.slopeX * -85.0 + fitOut.interceptX, -85.0, fitOut.slopeY * -85.0 + fitOut.interceptY)
        ];
        const outGeom = new THREE.BufferGeometry().setFromPoints(outPoints);
        const outMat = new THREE.LineBasicMaterial({ color: 0xff0080, linewidth: 2, transparent: true, opacity: 0.75 });
        const outLine = new THREE.Line(outGeom, outMat);
        this.scene.add(outLine);
        
        // Combine full path for particle animation
        // Flatten curve points in container
        const fullPath = [];
        traj.forEach(pt => {
            fullPath.push(new THREE.Vector3(pt[0], pt[2], pt[1]));
        });
        
        // Lit up pixels visual markers group
        const litPixels = [];
        const pixelGeom = new THREE.BoxGeometry(1.2, 0.2, 1.2);
        const pixelMat = new THREE.MeshBasicMaterial({ color: 0xffff00 });
        
        // Animate particle down the track
        let progress = 0.0;
        const speed = 0.04; // steps
        
        const animateSegment = () => {
            if (progress >= 1.0) {
                // Clean up particle
                this.scene.remove(particle);
                particle.geometry.dispose();
                particle.material.dispose();
                
                // Fade out tracks
                let fadeCount = 0;
                const fadeInterval = setInterval(() => {
                    inMat.opacity -= 0.08;
                    outMat.opacity -= 0.08;
                    litPixels.forEach(p => p.material.opacity -= 0.08);
                    
                    fadeCount++;
                    if (fadeCount >= 10) {
                        clearInterval(fadeInterval);
                        this.scene.remove(inLine);
                        this.scene.remove(outLine);
                        litPixels.forEach(p => {
                            this.scene.remove(p);
                            p.geometry.dispose();
                            p.material.dispose();
                        });
                        inGeom.dispose();
                        inMat.dispose();
                        outGeom.dispose();
                        outMat.dispose();
                    }
                }, 40);
                
                if (callback) callback();
                return;
            }
            
            // Find current interpolated point on the path
            const idx = Math.floor(progress * (fullPath.length - 1));
            const nextIdx = Math.min(idx + 1, fullPath.length - 1);
            const localT = (progress * (fullPath.length - 1)) - idx;
            
            const pStart = fullPath[idx];
            const pEnd = fullPath[nextIdx];
            
            particle.position.lerpVectors(pStart, pEnd, localT);
            
            // Check if particle crossed a detector plane to light up pixel
            track.hitPixels.forEach(hp => {
                // If particle position Y is close to the plane Z position
                if (Math.abs(particle.position.y - hp.z) < 1.5 && !hp.activated) {
                    hp.activated = true;
                    
                    const pix = new THREE.Mesh(pixelGeom, new THREE.MeshBasicMaterial({ color: 0xffff00, transparent: true, opacity: 1.0 }));
                    // Align position: X -> X, Z -> Y
                    const half = 50.0;
                    const hx = -half + hp.px + 0.5;
                    const hy = hp.z;
                    const hz = -half + hp.py + 0.5;
                    pix.position.set(hx, hy, hz);
                    this.scene.add(pix);
                    litPixels.push(pix);
                }
            });
            
            progress += speed;
            requestAnimationFrame(animateSegment);
        };
        
        animateSegment();
    }

    clearRecon() {
        this.voxelGeometry.setAttribute('position', new THREE.Float32BufferAttribute([], 3));
        this.voxelGeometry.setAttribute('color', new THREE.Float32BufferAttribute([], 3));
        this.pocaGeometry.setAttribute('position', new THREE.Float32BufferAttribute([], 3));
        
        // Clear persistent hit points
        this.persistentHitPositions = [];
        this.persistentHitsGeometry.setAttribute('position', new THREE.Float32BufferAttribute([], 3));
        this.persistentHitsGeometry.computeBoundingSphere();
        
        // Clear persistent track lines
        this.persistentTrackPositionsIn = [];
        this.persistentTrackPositionsOut = [];
        this.persistentTracksGeomIn.setAttribute('position', new THREE.Float32BufferAttribute([], 3));
        this.persistentTracksGeomOut.setAttribute('position', new THREE.Float32BufferAttribute([], 3));
        this.persistentTracksGeomIn.computeBoundingSphere();
        this.persistentTracksGeomOut.computeBoundingSphere();
        
        // Clear reconstructed 3D mesh
        while (this.reconstructedGroup.children.length > 0) {
            const child = this.reconstructedGroup.children[0];
            this.reconstructedGroup.remove(child);
            if (child.geometry) child.geometry.dispose();
            if (child.material) child.material.dispose();
        }
    }

    drawReconstructedMesh(reconObj) {
        // Clear old reconstructed mesh
        while (this.reconstructedGroup.children.length > 0) {
            const child = this.reconstructedGroup.children[0];
            this.reconstructedGroup.remove(child);
            if (child.geometry) child.geometry.dispose();
            if (child.material) child.material.dispose();
        }
        
        if (!reconObj || !reconObj.dims || !reconObj.dims.w) return;
        
        const dims = reconObj.dims;
        const centroid = reconObj.centroid;
        
        // Create glowing cyan wireframe material
        const mat = new THREE.MeshBasicMaterial({
            color: 0x00ffff, // bright cyan
            transparent: true,
            opacity: 0.25,
            wireframe: true
        });
        
        // Bounding Box Geometry: X -> w, Y -> h (vertical in Three.js, Z in physics), Z -> d
        const geom = new THREE.BoxGeometry(dims.w, dims.h, dims.d);
        const mesh = new THREE.Mesh(geom, mat);
        mesh.position.set(centroid[0], centroid[2], centroid[1]); // X, Z, Y
        
        // Add solid bounding edges for a technical outline look
        const edges = new THREE.EdgesGeometry(geom);
        const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x00ffff, transparent: true, opacity: 0.5 }));
        mesh.add(line);
        
        this.reconstructedGroup.add(mesh);
    }

    onWindowResize() {
        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;
        
        this.camera.aspect = this.width / this.height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(this.width, this.height);
    }

    render() {
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
}
