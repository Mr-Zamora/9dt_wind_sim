        document.addEventListener('DOMContentLoaded', function() {
            // API Configuration
            const API_BASE = window.location.origin + '/api';
            
            // State management
            let currentDesignId = null;
            let currentDesignGeometry = null;
            let lastScaleMode = 'miniature';
            let simulationRunning = false;

            const MATERIAL_DENSITIES = {
                'foam_composite': 1600,
                'carbon_fiber': 1750,
                'aluminum': 2700,
                'steel': 7850,
                'abs_plastic': 1040,
                'balsa_wood': 130
            };

            // Recalculate and update the editable mass input field based on loaded geometry, material, and scale
            function recalculateMass() {
                if (!currentDesignGeometry) return;
                const material = document.getElementById('material').value;
                const density = MATERIAL_DENSITIES[material] || 1600;
                const scaleMode = document.getElementById('scaleMode').value;
                
                // Calculate default mass in kg (structural factor 0.12)
                let calculatedMassKg = currentDesignGeometry.volume_m3 * density * 0.12;
                
                // If in full_scale mode, scale it by (scale_factor ** 3)
                if (scaleMode === 'full_scale') {
                    const origLength = currentDesignGeometry.length_m || currentDesignGeometry.dimensions.length;
                    const scaleFactor = 4.5 / Math.max(origLength, 0.01);
                    calculatedMassKg = calculatedMassKg * (scaleFactor ** 3);
                }
                
                // Format and display
                const isMiniature = scaleMode === 'miniature';
                const massInput = document.getElementById('geom-mass-input');
                const massUnit = document.getElementById('geom-mass-unit');
                const massLabel = document.getElementById('geom-mass-label');
                
                if (massInput) {
                    massInput.disabled = false;
                }
                
                const materialSelect = document.getElementById('material');
                const selectedMaterialLabel = materialSelect ? materialSelect.options[materialSelect.selectedIndex].text : 'Selected';
                if (massLabel) {
                    massLabel.textContent = `Mass (${selectedMaterialLabel})`;
                }
                
                if (isMiniature) {
                    if (massInput) massInput.value = Math.round(calculatedMassKg * 1000);
                    if (massUnit) massUnit.textContent = 'g';
                } else {
                    if (massInput) massInput.value = calculatedMassKg.toFixed(2);
                    if (massUnit) massUnit.textContent = 'kg';
                }
            }

            // Dynamically update the engine power slider UI limits and labels
            function updatePowerSliderUI() {
                const scaleMode = document.getElementById('scaleMode').value;
                const powerLabel = document.getElementById('enginePowerLabel');
                const powerSlider = document.getElementById('enginePower');
                const sliderValueDiv = powerSlider.nextElementSibling; // the .slider-value div
                
                if (scaleMode === 'miniature') {
                    if (powerLabel) powerLabel.textContent = 'Motor Power';
                    
                    // Save current HP value if switching
                    if (powerSlider.max === '500') {
                        powerSlider.dataset.lastHp = powerSlider.value;
                    }
                    
                    powerSlider.min = '10';
                    powerSlider.max = '100';
                    // Restore last saved Watts or default to 25
                    powerSlider.value = powerSlider.dataset.lastWatts || '25';
                    
                    if (sliderValueDiv) {
                        sliderValueDiv.innerHTML = `
                            <span>10 W</span>
                            <span class="current-value">${powerSlider.value} W</span>
                            <span>100 W</span>
                        `;
                    }
                } else {
                    if (powerLabel) powerLabel.textContent = 'Engine Power';
                    
                    // Save current Watts value if switching
                    if (powerSlider.max === '100') {
                        powerSlider.dataset.lastWatts = powerSlider.value;
                    }
                    
                    powerSlider.min = '50';
                    powerSlider.max = '500';
                    // Restore last saved HP or default to 150
                    powerSlider.value = powerSlider.dataset.lastHp || '150';
                    
                    if (sliderValueDiv) {
                        sliderValueDiv.innerHTML = `
                            <span>50 HP</span>
                            <span class="current-value">${powerSlider.value} HP</span>
                            <span>500 HP</span>
                        `;
                    }
                }
            }

            // Dynamic unit format helper based on length of model
            function getFormattedMetrics(geometry, massKg) {
                const length = geometry.length_m;
                const isMiniature = length < 1.0;

                if (isMiniature) {
                    return {
                        length: `${Number((geometry.length_m * 1000).toFixed(1))} mm`,
                        width: `${Number((geometry.width_m * 1000).toFixed(1))} mm`,
                        height: `${Number((geometry.height_m * 1000).toFixed(1))} mm`,
                        frontalArea: `${Number((geometry.frontal_area_m2 * 10000).toFixed(1))} cm²`,
                        volume: `${Number((geometry.volume_m3 * 1000000).toFixed(1))} cm³`,
                        mass: `${Math.round(massKg * 1000).toLocaleString()} g`,
                        massUnit: 'g',
                        massVal: Math.round(massKg * 1000)
                    };
                } else {
                    return {
                        length: `${geometry.length_m.toFixed(2)} m`,
                        width: `${geometry.width_m.toFixed(2)} m`,
                        height: `${geometry.height_m.toFixed(2)} m`,
                        frontalArea: `${geometry.frontal_area_m2.toFixed(2)} m²`,
                        volume: `${geometry.volume_m3.toFixed(4)} m³`,
                        mass: `${Math.round(massKg).toLocaleString()} kg`,
                        massUnit: 'kg',
                        massVal: Math.round(massKg)
                    };
                }
            }

            // Three.js Core State Variables
            let scene, camera, renderer, controls;
            let carMesh = null;
            let carGeometry = null;
            let dirLight = null;
            let gridHelper = null;
            const clipPlane = new THREE.Plane(new THREE.Vector3(-1, 0, 0), 100);
            
            let metallicMaterial, pressureMaterial;
            let currentViewMode = '3d';
            
            // Streamline state
            const streamlineGroup = new THREE.Group();
            let streamlineCurves = [];
            let streamlineParticles = [];
            
            // Slice Cap mesh
            let sliceCapMesh = null;

            // Initialize Three.js Viewport
            function initThree() {
                const container = document.getElementById('canvas-container');
                if (!container) return;
                
                const width = container.clientWidth || 800;
                const height = container.clientHeight || 500;
                
                // Scene
                scene = new THREE.Scene();
                scene.background = new THREE.Color(0x111625);
                
                // Camera
                camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
                camera.position.set(4, 2, 5);
                
                // Renderer
                renderer = new THREE.WebGLRenderer({ antialias: true });
                renderer.setSize(width, height);
                renderer.setPixelRatio(window.devicePixelRatio);
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFSoftShadowMap; // Beautiful soft shadows
                renderer.localClippingEnabled = true;
                container.appendChild(renderer.domElement);
                
                // OrbitControls
                controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.maxPolarAngle = Math.PI / 2 + 0.05; // limit looking below floor
                controls.minDistance = 1;
                controls.maxDistance = 20;
                
                // Lights
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
                scene.add(ambientLight);
                
                dirLight = new THREE.DirectionalLight(0xffffff, 0.85);
                dirLight.position.copy(camera.position);
                scene.add(dirLight);

                // Fixed top-down spotlight for casting beautiful soft shadows under the car
                const shadowLight = new THREE.DirectionalLight(0xffffff, 0.6);
                shadowLight.position.set(0, 8, 0);
                shadowLight.target.position.set(0, -1.0, 0);
                shadowLight.castShadow = true;
                shadowLight.shadow.mapSize.width = 1024;
                shadowLight.shadow.mapSize.height = 1024;
                shadowLight.shadow.camera.near = 0.5;
                shadowLight.shadow.camera.far = 15;
                shadowLight.shadow.camera.left = -3;
                shadowLight.shadow.camera.right = 3;
                shadowLight.shadow.camera.top = 3;
                shadowLight.shadow.camera.bottom = -3;
                shadowLight.shadow.bias = -0.001;
                scene.add(shadowLight);
                scene.add(shadowLight.target);
                
                // Floor grid at Y = -1.0
                // Both colors set to 0x425586 makes the grid perfectly periodic with period 1.0,
                // making the translation snap completely invisible to the eye!
                gridHelper = new THREE.GridHelper(30, 30, 0x425586, 0x425586);
                gridHelper.position.y = -1.0;
                scene.add(gridHelper);

                // Sleek, dark ground plane for receiving shadows and reflections
                const floorGeo = new THREE.PlaneGeometry(60, 60);
                const floorMat = new THREE.MeshStandardMaterial({
                    color: 0x0c0f1d,
                    roughness: 0.35,
                    metalness: 0.75,
                    transparent: true,
                    opacity: 0.8
                });
                const floorMesh = new THREE.Mesh(floorGeo, floorMat);
                floorMesh.rotation.x = -Math.PI / 2;
                floorMesh.position.y = -1.002; // slightly below the grid to avoid Z-fighting
                floorMesh.receiveShadow = true;
                scene.add(floorMesh);
                
                // Add streamline group to scene
                scene.add(streamlineGroup);
                
                // Pre-configure Materials
                metallicMaterial = new THREE.MeshStandardMaterial({
                    color: 0x90a4ae,
                    roughness: 0.35,
                    metalness: 0.75,
                    clippingPlanes: [clipPlane]
                });
                
                pressureMaterial = new THREE.MeshStandardMaterial({
                    vertexColors: true,
                    roughness: 0.4,
                    metalness: 0.2,
                    clippingPlanes: [clipPlane]
                });
                
                // Handle container resize dynamically
                const resizeObserver = new ResizeObserver(() => {
                    const w = container.clientWidth;
                    const h = container.clientHeight;
                    if (w && h) {
                        camera.aspect = w / h;
                        camera.updateProjectionMatrix();
                        renderer.setSize(w, h);
                    }
                });
                resizeObserver.observe(container);
                
                // Start animation loop
                requestAnimationFrame(animate);
            }

            // Vertex-normal HSL pressure heatmap coloring
            function applyPressureColoring(geometry) {
                const position = geometry.attributes.position;
                const normal = geometry.attributes.normal;
                if (!position || !normal) return;

                const colors = [];
                const normArray = normal.array;
                for (let i = 0; i < position.count; i++) {
                    const nx = normArray[i * 3];
                    // Map normal x component to [0, 1] range
                    const t = (nx + 1.0) / 2.0;
                    // HSL spectrum: Hue goes from 240 (Blue/Rear Wake) to 0 (Red/Front Stagnation)
                    const hue = (1.0 - t) * 240; 
                    
                    const color = new THREE.Color();
                    color.setHSL(hue / 360, 1.0, 0.5);
                    colors.push(color.r, color.g, color.b);
                }
                
                geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
            }

            // ── Wind-tunnel streamlines ─────────────────────────────────────────
            // Directly places each streamline point at surfaceProfile(x) + gap.
            // No integration drift — lines are mathematically pinned to the mesh
            // silhouette at every X step: windshield slope, flat body, rear taper
            // -- Wind-tunnel streamlines (max-clamping / silhouette-following) ----
            // Each streamline point is placed at:
            //   y = max(seedY, roofProfile(x) + gap)   [above car]
            //   y = min(seedY, bellyProfile(x) - gap)  [below car]
            // The max/min do all the work: seeds that are lower than the car roof
            // get lifted to ride the exact silhouette; far seeds stay undisturbed.
            // This correctly handles ANY car shape automatically.
            function createStreamlines() {
                console.log('createStreamlines called');
                while (streamlineGroup.children.length > 0) {
                    streamlineGroup.remove(streamlineGroup.children[0]);
                }
                streamlineCurves = [];
                streamlineParticles = [];
                if (!carGeometry || !carMesh) {
                    console.log('Missing carGeometry or carMesh');
                    return;
                }

                console.log('Computing bounding box...');
                carGeometry.computeBoundingBox();
                const box  = carGeometry.boundingBox;
                console.log('Bounding box:', box);
                if (!box || !box.min || !box.max) {
                    console.error('Invalid bounding box for car geometry');
                    return;
                }
                const size = new THREE.Vector3(); box.getSize(size);
                console.log('Box size:', size);

                // -- 1. Sample mesh profiles (X=flow, Y=height, Z=width) --------
                const N   = 200;
                const xLo = box.min.x, xHi = box.max.x;
                const dxP = (xHi - xLo) / N;
                const yOff = carMesh.position.y;

                const roofArr  = new Float32Array(N).fill(-Infinity);
                const bellyArr = new Float32Array(N).fill( Infinity);
                const sideArr  = new Float32Array(N).fill(0);

                const pa = carGeometry.attributes.position;
                console.log('Position attributes:', pa);
                if (!pa) {
                    console.error('No position attributes on geometry');
                    return;
                }
                const ix = carGeometry.index;
                console.log('Index:', ix);
                const hit = (vx, vy, vz) => {
                    const si = Math.floor((vx - xLo) / dxP);
                    if (si < 0 || si >= N) return;
                    if (vy > roofArr[si])           roofArr[si]  = vy;
                    if (vy < bellyArr[si])          bellyArr[si] = vy;
                    if (Math.abs(vz) > sideArr[si]) sideArr[si]  = Math.abs(vz);
                };
                console.log('Starting geometry loop, vertex count:', pa.count);
                const posArray = pa.array;

                const sampleTriangle = (ax, ay, az, bx, by, bz, cx, cy, cz) => {
                    // 1. Hit the vertices directly
                    hit(ax, ay, az);
                    hit(bx, by, bz);
                    hit(cx, cy, cz);

                    // 2. Hit the three edges continuously by interpolating across spanned X slices
                    const sampleEdge = (x0, y0, z0, x1, y1, z1) => {
                        const xMin = Math.min(x0, x1);
                        const xMax = Math.max(x0, x1);
                        const siStart = Math.max(0, Math.ceil((xMin - xLo) / dxP));
                        const siEnd = Math.min(N - 1, Math.floor((xMax - xLo) / dxP));

                        const dxEdge = x1 - x0;
                        if (Math.abs(dxEdge) > 1e-8) {
                            for (let si = siStart; si <= siEnd; si++) {
                                const xSlice = xLo + si * dxP;
                                const t = (xSlice - x0) / dxEdge;
                                const yInterp = y0 + t * (y1 - y0);
                                const zInterp = z0 + t * (z1 - z0);
                                hit(xSlice, yInterp, zInterp);
                            }
                        }
                    };

                    sampleEdge(ax, ay, az, bx, by, bz);
                    sampleEdge(bx, by, bz, cx, cy, cz);
                    sampleEdge(cx, cy, cz, ax, ay, az);
                };

                if (ix) {
                    console.log('Using indexed geometry');
                    const idxArray = ix.array;
                    const triCount = ix.count / 3;
                    for (let i = 0; i < triCount; i++) {
                        const k0 = idxArray[i * 3];
                        const k1 = idxArray[i * 3 + 1];
                        const k2 = idxArray[i * 3 + 2];

                        sampleTriangle(
                            posArray[k0 * 3], posArray[k0 * 3 + 1], posArray[k0 * 3 + 2],
                            posArray[k1 * 3], posArray[k1 * 3 + 1], posArray[k1 * 3 + 2],
                            posArray[k2 * 3], posArray[k2 * 3 + 1], posArray[k2 * 3 + 2]
                        );
                    }
                } else {
                    console.log('Using non-indexed geometry');
                    const triCount = pa.count / 3;
                    for (let i = 0; i < triCount; i++) {
                        const k0 = i * 3;
                        const k1 = i * 3 + 1;
                        const k2 = i * 3 + 2;

                        sampleTriangle(
                            posArray[k0 * 3], posArray[k0 * 3 + 1], posArray[k0 * 3 + 2],
                            posArray[k1 * 3], posArray[k1 * 3 + 1], posArray[k1 * 3 + 2],
                            posArray[k2 * 3], posArray[k2 * 3 + 1], posArray[k2 * 3 + 2]
                        );
                    }
                }

                // Fill empty slices robustly using linear interpolation/extrapolation
                console.log('Filling empty slices robustly...');
                const fillArray = (arr, fallbackVal) => {
                    const n = arr.length;
                    const validIndices = [];
                    for (let i = 0; i < n; i++) {
                        if (isFinite(arr[i]) && arr[i] !== -Infinity && arr[i] !== Infinity) {
                            validIndices.push(i);
                        }
                    }
                    
                    if (validIndices.length === 0) {
                        arr.fill(fallbackVal);
                        return;
                    }
                    
                    // Constantly extrapolate the ends
                    const firstValidIdx = validIndices[0];
                    const firstValidVal = arr[firstValidIdx];
                    for (let i = 0; i < firstValidIdx; i++) {
                        arr[i] = firstValidVal;
                    }
                    
                    const lastValidIdx = validIndices[validIndices.length - 1];
                    const lastValidVal = arr[lastValidIdx];
                    for (let i = lastValidIdx + 1; i < n; i++) {
                        arr[i] = lastValidVal;
                    }
                    
                    // Linearly interpolate intermediate gaps
                    for (let k = 0; k < validIndices.length - 1; k++) {
                        const leftIdx = validIndices[k];
                        const rightIdx = validIndices[k+1];
                        const leftVal = arr[leftIdx];
                        const rightVal = arr[rightIdx];
                        
                        for (let i = leftIdx + 1; i < rightIdx; i++) {
                            const t = (i - leftIdx) / (rightIdx - leftIdx);
                            arr[i] = leftVal + (rightVal - leftVal) * t;
                        }
                    }
                };

                fillArray(roofArr, 0.0);
                fillArray(bellyArr, 0.0);

                // Interpolate sideArr gaps (where sideArr[i] === 0)
                const validSideIndices = [];
                for (let i = 0; i < N; i++) {
                    if (sideArr[i] > 0) {
                        validSideIndices.push(i);
                    }
                }
                if (validSideIndices.length > 0) {
                    const firstVal = sideArr[validSideIndices[0]];
                    for (let i = 0; i < validSideIndices[0]; i++) sideArr[i] = firstVal;
                    
                    const lastVal = sideArr[validSideIndices[validSideIndices.length - 1]];
                    for (let i = validSideIndices[validSideIndices.length - 1] + 1; i < N; i++) sideArr[i] = lastVal;
                    
                    for (let k = 0; k < validSideIndices.length - 1; k++) {
                        const leftIdx = validSideIndices[k];
                        const rightIdx = validSideIndices[k+1];
                        const leftVal = sideArr[leftIdx];
                        const rightVal = sideArr[rightIdx];
                        for (let i = leftIdx + 1; i < rightIdx; i++) {
                            const t = (i - leftIdx) / (rightIdx - leftIdx);
                            sideArr[i] = leftVal + (rightVal - leftVal) * t;
                        }
                    }
                }

                // Variable-window smoothing at bounds to avoid edge jumps, creating extremely smooth, organic waves
                console.log('Smoothing arrays...');
                const smooth = (arr, w=10) => {
                    const out = new Float32Array(arr);
                    for (let i = 0; i < arr.length; i++) {
                        const currentW = Math.min(w, i, arr.length - 1 - i);
                        let s = 0;
                        for (let k = -currentW; k <= currentW; k++) {
                            s += arr[i + k];
                        }
                        out[i] = s / (2 * currentW + 1);
                    }
                    return out;
                };
                const roof  = smooth(roofArr,  6);
                const belly = smooth(bellyArr, 6);
                const side  = smooth(sideArr,  7);
                console.log('Smoothing complete');

                // -- 2. Continuous profile interpolation --------------------------
                const lerp = (arr, xGeom) => {
                    const t  = Math.max(0, Math.min(N - 1, (xGeom - xLo) / dxP));
                    const i0 = Math.min(N - 2, Math.floor(t));
                    const fraction = t - i0;
                    return arr[i0] * (1 - fraction) + arr[i0 + 1] * fraction;
                };

                const roofMax  = Math.max(...roof);
                const bellyMin = Math.min(...belly);
                const sideMax  = Math.max(...side);
                const carH     = roofMax - bellyMin;
                const carW     = sideMax * 2;
                console.log('Profile stats:', { roofMax, bellyMin, sideMax, carH, carW });

                // Profile extended outside car body with smooth taper (split-taper for realistic aerodynamics)
                const TAPER_FRONT = size.x * 0.45; // Short, clean deflection near the nose
                const TAPER_REAR  = size.x * 2.2;  // Longer, gradual decay in the wake
                
                console.log('Creating profile functions...');
                const getTopAt = (x) => {
                    if (x > xHi) { const t=Math.min(1,(x-xHi)/TAPER_FRONT); return lerp(roof,xHi)*(1-t)+bellyMin*t; }
                    if (x < xLo) { const t=Math.min(1,(xLo-x)/TAPER_REAR); return lerp(roof,xLo)*(1-t)+bellyMin*t; }
                    return lerp(roof, x);
                };
                const getBotAt = (x) => {
                    if (x > xHi) { const t=Math.min(1,(x-xHi)/TAPER_FRONT); return lerp(belly,xHi)*(1-t)+bellyMin*t; }
                    if (x < xLo) { const t=Math.min(1,(xLo-x)/TAPER_REAR); return lerp(belly,xLo)*(1-t)+bellyMin*t; }
                    return lerp(belly, x);
                };
                const getSideAt = (x) => {
                    if (x > xHi) { const t=Math.min(1,(x-xHi)/TAPER_FRONT); return lerp(side,xHi)*(1-t); }
                    if (x < xLo) { const t=Math.min(1,(xLo-x)/TAPER_REAR); return lerp(side,xLo)*(1-t); }
                    return lerp(side, x);
                };

                // -- 3. Core tracer using max/min clamping -----------------------
                // seedY_geom: starting height in geometry space
                // seedZ:      starting lateral offset (0 = side-view line)
                // The max() does all the work for above-car lines, min() for below.
                const SURF_GAP = carH * 0.035;
                const STEPS    = 600;
                const xStart   = 15.0; // Pinned exactly to the front boundary of the 30x30 moving floor grid
                const xEnd     = -15.0; // Pinned exactly to the back boundary of the 30x30 moving floor grid
                const DX       = (xEnd - xStart) / STEPS;

                const traceLine = (seedY_geom, seedZ) => {
                    const pts = [];
                    
                    // Statically classify the flow regime based on seed position
                    const isHighAbove = seedY_geom >= roofMax + SURF_GAP;
                    const isBelowBelly = seedY_geom < bellyMin;
                    
                    // A streamline deflects laterally ONLY if it is seeded on the outer sides of the car width and level with the body
                    const isSideDeflecting = Math.abs(seedZ) >= sideMax * 0.5 && !isHighAbove && !isBelowBelly;

                    let prev_y = seedY_geom;
                    let prev_z = seedZ;

                    for (let s = 0; s <= STEPS; s++) {
                        const x  = xStart + s * DX;
                        const tY = getTopAt(x);
                        const bY = getBotAt(x);
                        const sZ = getSideAt(x);

                        let y_geom = seedY_geom;
                        let z_out = seedZ;

                        if (isBelowBelly) {
                            // 1. Below Belly Flow: stays under the car body
                            y_geom = Math.min(seedY_geom, bY - SURF_GAP);
                            z_out = seedZ;
                        } else if (isSideDeflecting) {
                            // 2. Lateral Flow (Outer Side/Ring lines): deflects strictly laterally around car width (sZ), flat height
                            const absSZ = Math.abs(seedZ);
                            if (absSZ <= sZ + SURF_GAP) {
                                z_out = Math.sign(seedZ) * (sZ + SURF_GAP);
                            } else {
                                const excess = absSZ - sZ;
                                const bump = sZ * 0.15 * Math.exp(-excess / (carW * 0.5));
                                z_out = Math.sign(seedZ) * (absSZ + bump);
                            }
                            y_geom = seedY_geom;
                        } else {
                            // Exponential deflection decay to stack streamlines beautifully and prevent them merging
                            const obstacleHeight = Math.max(0, tY - bellyMin);
                            const heightAboveBelly = Math.max(0, seedY_geom - bellyMin);
                            const decayScale = Math.max(0.1, carH * 1.15);
                            const deflectionDecay = Math.exp(-heightAboveBelly / decayScale);
                            
                            y_geom = seedY_geom + obstacleHeight * deflectionDecay + SURF_GAP;
                            
                            // Gentle lateral nudge for non-center vertical lines
                            const absSZ = Math.abs(seedZ);
                            if (absSZ > 0.001) {
                                if (absSZ > sZ * 0.3) {
                                    const excess = absSZ - sZ;
                                    const bump = sZ * 0.05 * Math.exp(-excess / (carW * 0.6));
                                    z_out = Math.sign(seedZ) * (absSZ + bump);
                                }
                            } else {
                                z_out = 0;
                            }
                        }

                        // Apply Flow Momentum Constraints (Aerodynamic Slope limits)
                        if (s > 0) {
                            const dx_abs = Math.abs(DX);
                            
                            // 1. Vertical descent limit: prevent air from plunging vertically into Kammbacks (max ~8.5° slope)
                            if (y_geom < prev_y) {
                                y_geom = Math.max(y_geom, prev_y - 0.15 * dx_abs);
                            }
                            
                            // 2. Lateral return limit: prevent air from snapping inward instantly behind wheels/body (max ~14° slope)
                            const absZ = Math.abs(z_out);
                            const absPrevZ = Math.abs(prev_z);
                            if (absZ < absPrevZ) {
                                const clampedAbsZ = Math.max(absZ, absPrevZ - 0.25 * dx_abs);
                                z_out = Math.sign(z_out || prev_z) * clampedAbsZ;
                            }
                        }
                        prev_y = y_geom;
                        prev_z = z_out;

                        const floorY = -1.0;
                        pts.push(new THREE.Vector3(x, Math.max(y_geom + yOff, floorY + 0.01), z_out));
                    }
                    
                    // Smooth the final 3D points of the path to completely eliminate high-frequency vertex-sampling aliasing noise
                    const smoothedPts = [];
                    const w_path = 8; // moderate smoothing window size (covers 17 points)
                    for (let i = 0; i < pts.length; i++) {
                        const currentW = Math.min(w_path, i, pts.length - 1 - i);
                        let sumX = 0, sumY = 0, sumZ = 0;
                        for (let k = -currentW; k <= currentW; k++) {
                            const p = pts[i + k];
                            sumX += p.x;
                            sumY += p.y;
                            sumZ += p.z;
                        }
                        const count = 2 * currentW + 1;
                        smoothedPts.push(new THREE.Vector3(sumX / count, sumY / count, sumZ / count));
                    }
                    
                    return smoothedPts;
                };

                // -- 4. Seed layout ----------------------------------------------
                // Side-view lines (z=0): seeds at increasing heights above bellyMin.
                // Fractions 0..~1 ride the surface; fractions > 1 show far-field bump.
                const aboveFracs = [0.0, 0.04, 0.10, 0.20, 0.33, 0.50, 0.68, 0.88, 1.10, 1.38, 1.72, 2.15];
                const belowFracs = [0.05, 0.18, 0.38];  // below belly

                const seeds = [];
                aboveFracs.forEach((f, i) => seeds.push({
                    y: bellyMin + f * carH, z: 0, rank: i / aboveFracs.length, isSide: true
                }));
                belowFracs.forEach((f, i) => seeds.push({
                    y: bellyMin - f * carH, z: 0, rank: i / belowFracs.length * 0.5, isSide: true
                }));

                // Top-view / ring lines: pairs at various Z offsets + Y positions
                const ringDefs = [
                    { y: roofMax + 0.05*carH, z:  sideMax * 0.6  },
                    { y: roofMax + 0.05*carH, z: -sideMax * 0.6  },
                    { y: roofMax + 0.20*carH, z:  sideMax * 0.9  },
                    { y: roofMax + 0.20*carH, z: -sideMax * 0.9  },
                    { y: (bellyMin+roofMax)*0.5, z:  sideMax * 1.15 },
                    { y: (bellyMin+roofMax)*0.5, z: -sideMax * 1.15 },
                    { y: (bellyMin+roofMax)*0.5, z:  sideMax * 1.60 },
                    { y: (bellyMin+roofMax)*0.5, z: -sideMax * 1.60 },
                    { y: roofMax + 0.50*carH,    z:  sideMax * 0.5  },
                    { y: roofMax + 0.50*carH,    z: -sideMax * 0.5  },
                    // Front nose lines - low, positioned to flow under/around nose
                    { y: bellyMin + 0.08*carH, z:  sideMax * 0.3  },
                    { y: bellyMin + 0.08*carH, z: -sideMax * 0.3  },
                    { y: bellyMin + 0.15*carH, z:  sideMax * 0.5  },
                    { y: bellyMin + 0.15*carH, z: -sideMax * 0.5  },
                    { y: bellyMin + 0.25*carH, z:  sideMax * 0.7  },
                    { y: bellyMin + 0.25*carH, z: -sideMax * 0.7  },
                    // Hood lines - flowing over the front hood area
                    { y: bellyMin + 0.45*carH, z:  sideMax * 0.4  },
                    { y: bellyMin + 0.45*carH, z: -sideMax * 0.4  },
                    // Center spine lines - fill the middle gap in top-down view
                    { y: bellyMin + 0.10*carH, z: 0 },
                    { y: bellyMin + 0.20*carH, z: 0 },
                    { y: bellyMin + 0.35*carH, z: 0 },
                    { y: bellyMin + 0.55*carH, z: 0 },
                    // Near-center pairs for density
                    { y: bellyMin + 0.30*carH, z:  sideMax * 0.15 },
                    { y: bellyMin + 0.30*carH, z: -sideMax * 0.15 },
                ];
                ringDefs.forEach(d => seeds.push({ y: d.y, z: d.z, rank: 0.65, isSide: false }));

                // -- 5. Build Three.js geometry ----------------------------------
                seeds.forEach((seed) => {
                    const pts = traceLine(seed.y, seed.z);
                    if (pts.length < 2) return;
                    const curve = new THREE.CatmullRomCurve3(pts);
                    streamlineCurves.push(curve);

                    const opacity = THREE.MathUtils.clamp(
                        seed.isSide ? 0.78 - seed.rank * 0.48 : 0.22,
                        0.08, 0.78
                    );
                    const color = seed.isSide ? 0x00e4ff : 0x0066bb;
                    const lGeom = new THREE.BufferGeometry().setFromPoints(curve.getPoints(450));
                    streamlineGroup.add(new THREE.Line(lGeom, new THREE.LineBasicMaterial({
                        color, transparent: true, opacity,
                        blending: THREE.AdditiveBlending, depthWrite: false
                    })));

                    const speed = THREE.MathUtils.clamp(1.3 - seed.rank * 0.45, 0.75, 1.3);
                    const pSize = THREE.MathUtils.clamp(0.030 - seed.rank * 0.016, 0.008, 0.030);

                    // Create five particles per streamline with even progress offsets for dense, high-quality flow
                    for (let pi = 0; pi < 5; pi++) {
                        const pMesh = new THREE.Mesh(
                            new THREE.SphereGeometry(pSize, 6, 6),
                            new THREE.MeshBasicMaterial({ color: 0x00f5ff, transparent: true, opacity: 0.92,
                                blending: THREE.AdditiveBlending, depthWrite: false })
                        );
                        streamlineGroup.add(pMesh);
                        const progressOffset = pi / 5.0; // evenly spaced along the streamline
                        streamlineParticles.push({ mesh: pMesh, curve, progress: (Math.random() + progressOffset) % 1.0, speed });
                    }
                });
            }

            // Create flat slicing cap helper plane
            function createSliceCap() {
                if (sliceCapMesh) {
                    scene.remove(sliceCapMesh);
                    sliceCapMesh = null;
                }
                
                if (!carGeometry) return;
                
                carGeometry.computeBoundingBox();
                const box = carGeometry.boundingBox;
                const size = new THREE.Vector3();
                box.getSize(size);
                
                // Plane slightly larger than the cross-section
                const capGeo = new THREE.PlaneGeometry(size.z * 1.15, size.y * 1.15);
                const capMat = new THREE.MeshBasicMaterial({
                    color: 0x00f0ff,
                    transparent: true,
                    opacity: 0.35,
                    side: THREE.DoubleSide,
                    depthWrite: false,
                    blending: THREE.AdditiveBlending
                });
                
                sliceCapMesh = new THREE.Mesh(capGeo, capMat);
                sliceCapMesh.rotation.y = Math.PI / 2; // Face X-axis
                sliceCapMesh.visible = false;
                scene.add(sliceCapMesh);
            }

            // Update slicing plane constant & position cap mesh
            function updateSlicePlane() {
                if (!carGeometry || !sliceCapMesh) return;
                
                const sliceSlider = document.getElementById('slicePlaneConstant');
                const sliceValueDisplay = document.getElementById('slice-value-display');
                if (!sliceSlider) return;
                
                const val = parseFloat(sliceSlider.value);
                const xMin = carGeometry.boundingBox.min.x;
                const xMax = carGeometry.boundingBox.max.x;
                
                // Mapping: left side of slider = Front (xMax), right side = Rear (xMin)
                const constant = xMax - (val - xMin);
                
                // Apply clipping plane constant (normal points to -X, keeps points with -X + C >= 0 => X <= C)
                clipPlane.constant = constant;
                
                // Position slice cap mesh to align perfectly with slice boundary
                sliceCapMesh.position.x = constant;
                sliceCapMesh.position.y = carMesh.position.y;
                sliceCapMesh.position.z = 0;
                
                if (sliceValueDisplay) {
                    sliceValueDisplay.textContent = `Position: ${constant.toFixed(2)} m`;
                }
            }

            // Manage Viewport Mode States & Transitions
            function setViewMode(mode) {
                console.log('setViewMode called with:', mode);
                currentViewMode = mode;
                
                // Update active state on buttons
                document.querySelectorAll('.viewport-btn').forEach(btn => btn.classList.remove('active'));
                
                if (mode === '3d') {
                    document.getElementById('btn-3d-view').classList.add('active');
                } else if (mode === 'pressure') {
                    document.getElementById('btn-pressure-map').classList.add('active');
                } else if (mode === 'streamlines') {
                    document.getElementById('btn-streamlines').classList.add('active');
                } else if (mode === 'slice') {
                    document.getElementById('btn-slice-view').classList.add('active');
                }
                
                // Handle range slider overlay visibility
                const sliceSliderContainer = document.getElementById('slice-slider-container');
                if (sliceSliderContainer) {
                    sliceSliderContainer.style.display = (mode === 'slice') ? 'flex' : 'none';
                }
                
                if (!carMesh) return;
                
                // Reset wireframe toggle
                const wireframeChecked = document.getElementById('toggle-wireframe').checked;
                
                if (mode === '3d') {
                    carMesh.material = metallicMaterial;
                    carMesh.material.wireframe = wireframeChecked;
                    clipPlane.constant = 100; // bypass clip
                    streamlineGroup.visible = false;
                    if (sliceCapMesh) sliceCapMesh.visible = false;
                } else if (mode === 'pressure') {
                    carMesh.material = pressureMaterial;
                    carMesh.material.wireframe = wireframeChecked;
                    clipPlane.constant = 100; // bypass clip
                    streamlineGroup.visible = false;
                    if (sliceCapMesh) sliceCapMesh.visible = false;
                } else if (mode === 'streamlines') {
                    carMesh.material = metallicMaterial;
                    carMesh.material.wireframe = wireframeChecked;
                    clipPlane.constant = 100; // bypass clip
                    streamlineGroup.visible = true;
                    if (sliceCapMesh) sliceCapMesh.visible = false;
                } else if (mode === 'slice') {
                    carMesh.material = metallicMaterial;
                    carMesh.material.wireframe = wireframeChecked;
                    updateSlicePlane();
                    streamlineGroup.visible = false;
                    if (sliceCapMesh) sliceCapMesh.visible = true;
                }
            }

            // Animate streamline particles along precomputed curves
            function animateParticles(dt) {
                if (currentViewMode !== 'streamlines') return;
                
                const windSpeedSlider = document.getElementById('windSpeed');
                const windSpeed = windSpeedSlider ? parseFloat(windSpeedSlider.value) : 100;
                
                // Base speed scales with wind speed; each particle also has its own
                // speed multiplier (faster near the car — Bernoulli effect visually)
                const baseSpeed = (windSpeed / 100) * 0.22;
                
                streamlineParticles.forEach(p => {
                    p.progress += baseSpeed * (p.speed || 1.0) * dt;
                    if (p.progress > 1.0) p.progress = 0.0;
                    const pos = p.curve.getPointAt(p.progress);
                    p.mesh.position.copy(pos);
                });
            }

            // Animate moving floor grid helper
            function animateMovingFloor(dt) {
                if (!gridHelper) return;
                
                const toggleMovingFloor = document.getElementById('toggle-moving-floor');
                const isMoving = toggleMovingFloor ? toggleMovingFloor.checked : true;
                
                if (isMoving) {
                    const windSpeedSlider = document.getElementById('windSpeed');
                    const windSpeed = windSpeedSlider ? parseFloat(windSpeedSlider.value) : 100;
                    
                    // Speed scales with wind speed (3.0 units/sec at 100 km/h)
                    const speedFactor = (windSpeed / 100) * 3.0;
                    
                    gridHelper.position.x -= speedFactor * dt;
                    // Wrap around grid division boundary (1.0 unit cell size)
                    if (gridHelper.position.x <= -1.0) {
                        gridHelper.position.x += 1.0;
                    }
                } else {
                    gridHelper.position.x = 0;
                }
            }

            // Core Render and Animation loop
            let lastTime = 0;
            function animate(time) {
                requestAnimationFrame(animate);
                
                const dt = (time - lastTime) / 1000;
                lastTime = time;
                
                // Constrain dt to handle browser suspensions smoothly
                const boundedDt = Math.min(dt, 0.1);
                
                animateParticles(boundedDt);
                animateMovingFloor(boundedDt);
                
                // Anchoring the main light to the camera preserves reflection angles
                if (dirLight && camera) {
                    dirLight.position.copy(camera.position);
                }
                
                if (controls) {
                    controls.update();
                }
                
                if (renderer && scene && camera) {
                    renderer.render(scene, camera);
                }
            }

            // Fetch and ingest raw design STL binary
            async function loadDesignSTL(designId) {
                const loaderOverlay = document.getElementById('viewport-loader');
                const loaderText = document.getElementById('loader-text');
                
                if (loaderOverlay) {
                    loaderOverlay.style.display = 'flex';
                }
                if (loaderText) {
                    loaderText.textContent = "Loading 3D model...";
                }
                
                const stlLoader = new THREE.STLLoader();
                const stlUrl = `${API_BASE}/designs/${designId}/stl`;
                
                stlLoader.load(
                    stlUrl,
                    function(geometry) {
                        if (carMesh) {
                            scene.remove(carMesh);
                        }
                        
                        carGeometry = geometry;
                        
                        // Map Z-up (standard CAD export) to Y-up (Three.js standard) by default
                        carGeometry.rotateX(-Math.PI / 2);
                        
                        // Auto-Laydown: detect the longest raw dimension and orient it along the flow (X-axis)
                        carGeometry.computeBoundingBox();
                        const rawSize = new THREE.Vector3();
                        carGeometry.boundingBox.getSize(rawSize);
                        
                        if (rawSize.y > rawSize.x && rawSize.y >= rawSize.z) {
                            carGeometry.rotateZ(Math.PI / 2); // Bring Y to X axis
                        } else if (rawSize.z > rawSize.x && rawSize.z >= rawSize.y) {
                            carGeometry.rotateY(Math.PI / 2); // Bring Z to X axis
                        }
                        
                        // Centering model around local origin
                        carGeometry.center();
                        
                        // Normalize bounding coordinates: target longest side to 4.0 units
                        carGeometry.computeBoundingBox();
                        const box = carGeometry.boundingBox;
                        const size = new THREE.Vector3();
                        box.getSize(size);
                        
                        const maxDim = Math.max(size.x, size.y, size.z);
                        const scaleFactor = 4.0 / maxDim;
                        carGeometry.scale(scaleFactor, scaleFactor, scaleFactor);
                        
                        // Re-compute attributes on normalized bounds
                        carGeometry.computeVertexNormals();
                        carGeometry.computeBoundingBox();
                        
                        const scaledSize = new THREE.Vector3();
                        carGeometry.boundingBox.getSize(scaledSize);
                        
                        // Generate colors attribute for pressure gradients
                        applyPressureColoring(carGeometry);
                        
                        // Instantiate mesh and ground it perfectly on the floor grid (Y = -1.0)
                        carMesh = new THREE.Mesh(carGeometry, metallicMaterial);
                        carMesh.position.set(0, -1.0 + (scaledSize.y / 2), 0);
                        carMesh.castShadow = true;
                        carMesh.receiveShadow = true;
                        scene.add(carMesh);
                        
                        // Refocus camera controls on vehicle center
                        controls.target.set(0, carMesh.position.y, 0);
                        camera.position.set(3.5, carMesh.position.y + 0.8, 4.0);
                        controls.update();
                        
                        // Set slider bounds matching actual physical bounds
                        const xMin = carGeometry.boundingBox.min.x;
                        const xMax = carGeometry.boundingBox.max.x;
                        
                        const sliceSlider = document.getElementById('slicePlaneConstant');
                        if (sliceSlider) {
                            sliceSlider.min = xMin;
                            sliceSlider.max = xMax;
                            sliceSlider.step = 0.01;
                            sliceSlider.value = xMax; // Reset slice
                        }
                        
                        updateSlicePlane();
                        
                        // Compute visualization modes
                        createStreamlines();
                        createSliceCap();
                        
                        // Make manual orientation buttons visible
                        document.getElementById('btn-rot-x').style.display = 'block';
                        document.getElementById('btn-rot-y').style.display = 'block';
                        document.getElementById('btn-rot-z').style.display = 'block';
                        
                        // Default to beautiful metallic view mode
                        setViewMode('3d');
                        
                        if (loaderOverlay) {
                            loaderOverlay.style.display = 'none';
                        }
                    },
                    function(xhr) {
                        if (xhr.total > 0 && loaderText) {
                            const percent = Math.round((xhr.loaded / xhr.total) * 100);
                            loaderText.textContent = `Loading 3D model... ${percent}%`;
                        }
                    },
                    function(error) {
                        console.error('STLLoader failed:', error);
                        if (loaderText) {
                            loaderText.textContent = "Error: Failed to load 3D mesh.";
                        }
                        setTimeout(() => {
                            if (loaderOverlay) loaderOverlay.style.display = 'none';
                        }, 2500);
                    }
                );
            }

            // Centralized pipeline re-computation when model orientation changes
            function onModelOrientationChanged() {
                if (!carGeometry || !carMesh) return;

                // 1. Re-center geometry around origin
                carGeometry.center();

                // 2. Re-compute attributes on centered bounds
                carGeometry.computeVertexNormals();
                carGeometry.computeBoundingBox();

                const scaledSize = new THREE.Vector3();
                carGeometry.boundingBox.getSize(scaledSize);

                // 3. Re-apply pressure coloring (as flow normals have changed!)
                applyPressureColoring(carGeometry);

                // 4. Ground mesh on floor grid (Y = -1.0)
                carMesh.position.set(0, -1.0 + (scaledSize.y / 2), 0);

                // 5. Refocus camera controls on vehicle center
                controls.target.set(0, carMesh.position.y, 0);
                controls.update();

                // 6. Reset slicing plane and slider bounds
                const xMin = carGeometry.boundingBox.min.x;
                const xMax = carGeometry.boundingBox.max.x;

                const sliceSlider = document.getElementById('slicePlaneConstant');
                if (sliceSlider) {
                    sliceSlider.min = xMin;
                    sliceSlider.max = xMax;
                    sliceSlider.step = 0.01;
                    sliceSlider.value = xMax; // Reset slice to front
                }

                updateSlicePlane();

                // 7. Recompute streamlines and slice caps
                createStreamlines();
                createSliceCap();

                // 8. Re-apply current view mode to update mesh materials
                setViewMode(currentViewMode);
            }

            // Quick 90-degree manual rotation controls
            function rotateModelX() {
                if (!carGeometry) return;
                carGeometry.rotateX(Math.PI / 2);
                onModelOrientationChanged();
            }

            function rotateModelY() {
                if (!carGeometry) return;
                carGeometry.rotateY(Math.PI / 2);
                onModelOrientationChanged();
            }

            function rotateModelZ() {
                if (!carGeometry) return;
                carGeometry.rotateZ(Math.PI / 2);
                onModelOrientationChanged();
            }

            // Wire up interactive sidebar controls
            document.getElementById('toggle-wireframe').addEventListener('change', function(e) {
                if (carMesh) {
                    carMesh.material.wireframe = e.target.checked;
                }
            });

            document.getElementById('slicePlaneConstant').addEventListener('input', function() {
                updateSlicePlane();
            });

            // Wire up viewport view mode selector buttons
            document.getElementById('btn-3d-view').addEventListener('click', () => setViewMode('3d'));
            document.getElementById('btn-pressure-map').addEventListener('click', () => setViewMode('pressure'));
            document.getElementById('btn-streamlines').addEventListener('click', () => setViewMode('streamlines'));
            document.getElementById('btn-slice-view').addEventListener('click', () => setViewMode('slice'));

            // Wire up model orientation control buttons
            document.getElementById('btn-rot-x').addEventListener('click', rotateModelX);
            document.getElementById('btn-rot-y').addEventListener('click', rotateModelY);
            document.getElementById('btn-rot-z').addEventListener('click', rotateModelZ);

            // Update slider values in sidebar UI
            document.getElementById('windSpeed').addEventListener('input', function(e) {
                const value = e.target.value;
                e.target.nextElementSibling.querySelector('.current-value').textContent = value + ' km/h';
            });

            document.getElementById('enginePower').addEventListener('input', function(e) {
                const value = e.target.value;
                const scaleMode = document.getElementById('scaleMode').value;
                const unit = scaleMode === 'miniature' ? ' W' : ' HP';
                e.target.nextElementSibling.querySelector('.current-value').textContent = value + unit;
            });

            // Bind scaleMode change event to update power slider and recalculate mass with scale scaling
            document.getElementById('scaleMode').addEventListener('change', function(e) {
                const newScaleMode = e.target.value;
                
                // If geometry is loaded, scale the numerical input value appropriately
                if (currentDesignGeometry) {
                    const massInput = document.getElementById('geom-mass-input');
                    const massUnit = document.getElementById('geom-mass-unit');
                    const value = parseFloat(massInput.value);
                    
                    if (!isNaN(value) && value > 0) {
                        const origLength = currentDesignGeometry.length_m || currentDesignGeometry.dimensions.length;
                        const scaleFactor = 4.5 / Math.max(origLength, 0.01);
                        
                        if (lastScaleMode === 'miniature' && newScaleMode === 'full_scale') {
                            // Scale from miniature grams to full-scale kg
                            const kgVal = (value / 1000) * (scaleFactor ** 3);
                            massInput.value = kgVal.toFixed(1);
                            massUnit.textContent = 'kg';
                        } else if (lastScaleMode === 'full_scale' && newScaleMode === 'miniature') {
                            // Down-scale from full-scale kg to miniature grams
                            const gramsVal = (value * 1000) / (scaleFactor ** 3);
                            massInput.value = Math.round(gramsVal);
                            massUnit.textContent = 'g';
                        }
                    } else {
                        recalculateMass();
                    }
                }
                
                lastScaleMode = newScaleMode;
                updatePowerSliderUI();
            });

            // Bind material change event to recalculate default mass
            document.getElementById('material').addEventListener('change', function() {
                recalculateMass();
            });

            // Bind reset parameters button click event
            document.getElementById('btn-reset-params').addEventListener('click', function() {
                // 1. Reset scale mode & material defaults
                const scaleModeSelect = document.getElementById('scaleMode');
                const materialSelect = document.getElementById('material');
                
                if (scaleModeSelect) scaleModeSelect.value = 'miniature';
                if (materialSelect) materialSelect.value = 'foam_composite';
                
                // 2. Reset engine/motor power slider datasets and value
                const powerSlider = document.getElementById('enginePower');
                if (powerSlider) {
                    powerSlider.dataset.lastWatts = '25';
                    powerSlider.dataset.lastHp = '150';
                    powerSlider.value = '25';
                }
                
                // 3. Reset wind speed
                const windSpeedSlider = document.getElementById('windSpeed');
                if (windSpeedSlider) {
                    windSpeedSlider.value = '100';
                }
                
                // 4. Reset toggles
                const toggleMovingFloor = document.getElementById('toggle-moving-floor');
                if (toggleMovingFloor) {
                    toggleMovingFloor.checked = true;
                }
                
                const toggleWireframe = document.getElementById('toggle-wireframe');
                if (toggleWireframe) {
                    toggleWireframe.checked = false;
                    toggleWireframe.dispatchEvent(new Event('change'));
                }
                
                // 5. Update power slider range & labels
                updatePowerSliderUI();
                
                // 6. Trigger inputs to refresh display values
                if (windSpeedSlider) {
                    windSpeedSlider.dispatchEvent(new Event('input'));
                }
                if (powerSlider) {
                    powerSlider.dispatchEvent(new Event('input'));
                }
                
                // 7. Recalculate mass from geometry
                if (currentDesignGeometry) {
                    recalculateMass();
                } else {
                    const massInput = document.getElementById('geom-mass-input');
                    const massUnit = document.getElementById('geom-mass-unit');
                    const massLabel = document.getElementById('geom-mass-label');
                    if (massInput) {
                        massInput.value = '';
                        massInput.disabled = true;
                        massInput.placeholder = '--';
                    }
                    if (massUnit) {
                        massUnit.textContent = 'g';
                    }
                    if (massLabel) {
                        massLabel.textContent = 'Mass (Classroom Composite)';
                    }
                }
            });

            // File upload handling
            const uploadZone = document.querySelector('.upload-zone');
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = '.stl';
            fileInput.style.display = 'none';
            document.body.appendChild(fileInput);

            uploadZone.addEventListener('click', () => {
                if (!simulationRunning) {
                    fileInput.click();
                }
            });

            uploadZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadZone.style.borderColor = '#667eea';
                uploadZone.style.background = '#f0f4ff';
            });

            uploadZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadZone.style.borderColor = '#ddd';
                uploadZone.style.background = 'white';
            });

            uploadZone.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadZone.style.borderColor = '#ddd';
                uploadZone.style.background = 'white';
                
                const files = e.dataTransfer.files;
                if (files.length > 0 && files[0].name.endsWith('.stl')) {
                    handleFileUpload(files[0]);
                } else {
                    alert('Please upload an STL file');
                }
            });

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFileUpload(e.target.files[0]);
                }
            });

            document.getElementById('presetSelect').addEventListener('change', async (e) => {
                const presetUrl = e.target.value;
                if (!presetUrl) return;

                if (simulationRunning) {
                    e.target.value = "";
                    alert('Simulation is currently running. Please wait.');
                    return;
                }

                try {
                    const presetName = e.target.options[e.target.selectedIndex].text.split(' ')[0];
                    updateStatus(`Fetching preset ${presetName}...`, 'running');
                    
                    const response = await fetch(presetUrl);
                    if (!response.ok) {
                        throw new Error(`Failed to download preset file: ${response.statusText}`);
                    }
                    
                    const blob = await response.blob();
                    const file = new File([blob], presetName, { type: 'application/octet-stream' });
                    
                    // Trigger the file upload pipeline
                    await handleFileUpload(file);
                    
                } catch (error) {
                    console.error('Preset loading error:', error);
                    updateStatus('Failed to load preset: ' + error.message, 'ready');
                    alert('Failed to load preset design: ' + error.message);
                } finally {
                    // Reset dropdown selection
                    e.target.value = "";
                }
            });

            // Ingest file and invoke server validations
            async function handleFileUpload(file) {
                // Check if file is larger than 500 KB and show warning
                if (file.size > 500 * 1024) {
                    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                    const proceed = confirm(`Notice: The selected file "${file.name}" is quite large (${sizeMB} MB).\n\nLarge files can take 10-30 seconds to upload and process over classroom Wi-Fi.\n\nDo you want to proceed?`);
                    if (!proceed) {
                        updateStatus('Ready - Upload an STL file to begin', 'ready');
                        return;
                    }
                }

                const formData = new FormData();
                formData.append('file', file);

                updateStatus(`Uploading ${file.name}... (this may take 10-30 seconds for large files)`, 'running');
                
                try {
                    const controller = new AbortController();
                    const timeout = setTimeout(() => controller.abort(), 60000); // 60s timeout limit
                    
                    const response = await fetch(`${API_BASE}/designs/upload`, {
                        method: 'POST',
                        body: formData,
                        signal: controller.signal
                    });
                    
                    clearTimeout(timeout);

                    if (!response.ok) {
                        const errorText = await response.text();
                        throw new Error(`Upload failed: ${response.statusText} - ${errorText}`);
                    }

                    const data = await response.json();
                    currentDesignId = data.design_id;
                    
                    updateStatus(`File uploaded: ${file.name} (${data.num_triangles.toLocaleString()} triangles)`, 'complete');
                    
                    // Populate parameters metadata
                    await loadDesignInfo(currentDesignId);
                    
                    // Render STL inside Three.js scene
                    await loadDesignSTL(currentDesignId);
                    
                    // Activate simulated execution button
                    document.querySelector('.btn-primary').disabled = false;
                    
                } catch (error) {
                    console.error('Upload error:', error);
                    if (error.name === 'AbortError') {
                        updateStatus('Upload timed out - file may be too large', 'ready');
                        alert('Upload timed out. The file may be too large or complex. Try a simpler STL file.');
                    } else {
                        updateStatus('Upload failed: ' + error.message, 'ready');
                        alert('Failed to upload file: ' + error.message);
                    }
                }
            }

            // Load design information details
            async function loadDesignInfo(designId) {
                try {
                    const response = await fetch(`${API_BASE}/designs/${designId}`);
                    const data = await response.json();
                    
                    // Keep track of geometry globally so we can recalculate when needed
                    currentDesignGeometry = data.geometry;
                    
                    // Recalculate and display the default mass
                    recalculateMass();
                    
                    // For the drag-and-drop zone preview, get default Foam Composite mass
                    const defaultMass = data.geometry.volume_m3 * 1600 * 0.12;
                    const metrics = getFormattedMetrics(data.geometry, defaultMass);
                    
                    // Update upload button display
                    uploadZone.innerHTML = `
                        ✅ Design Loaded<br>
                        <small>L: ${metrics.length} | W: ${metrics.width} | H: ${metrics.height}</small><br>
                        <small>Area: ${metrics.frontalArea} | Cd: ${data.drag_estimate.cd.toFixed(3)}</small>
                    `;
                    uploadZone.style.borderColor = '#10b981';
                    uploadZone.style.background = '#d1fae5';
                    
                    // Update Geometric Properties panel
                    document.getElementById('geom-length').textContent = metrics.length;
                    document.getElementById('geom-width').textContent = metrics.width;
                    document.getElementById('geom-height').textContent = metrics.height;
                    document.getElementById('geom-frontal-area').textContent = metrics.frontalArea;
                    document.getElementById('geom-volume').textContent = metrics.volume;
                    
                } catch (error) {
                    console.error('Failed to load design info:', error);
                }
            }

            // Run simulation API request
            document.querySelector('.btn-primary').addEventListener('click', async function() {
                if (!currentDesignId || simulationRunning) return;
                
                const windSpeed = parseFloat(document.getElementById('windSpeed').value);
                const enginePower = parseFloat(document.getElementById('enginePower').value);
                const material = document.getElementById('material').value;
                const scaleMode = document.getElementById('scaleMode').value;
                
                // Translate enginePower from Watts to HP if in miniature mode
                let enginePowerHp = enginePower;
                if (scaleMode === 'miniature') {
                    enginePowerHp = enginePower / 745.7;
                }
                
                // Read custom mass from input box and convert to kg for backend
                const massInput = document.getElementById('geom-mass-input');
                const massInputVal = massInput ? parseFloat(massInput.value) : NaN;
                let customMassKg = null;
                if (!isNaN(massInputVal) && massInputVal > 0 && currentDesignGeometry) {
                    if (scaleMode === 'miniature') {
                        customMassKg = massInputVal / 1000.0; // grams to kg
                    } else {
                        // In full-scale mode, the input value is the scaled mass.
                        // The backend expects the unscaled (miniature) mass in kg.
                        const origLength = currentDesignGeometry.length_m || currentDesignGeometry.dimensions.length;
                        const scaleFactor = 4.5 / Math.max(origLength, 0.01);
                        customMassKg = massInputVal / (scaleFactor ** 3);
                    }
                }
                
                simulationRunning = true;
                this.disabled = true;
                
                updateStatus('Running simulation...', 'running');
                
                const loader = document.getElementById('viewport-loader');
                const loaderText = document.getElementById('loader-text');
                
                // Show standard loader with sleek classroom text
                loaderText.textContent = 'Simulating wind tunnel airflow...';
                loader.style.display = 'flex';
                
                try {
                    // Fetch results immediately in background (takes ~50ms)
                    const response = await fetch(`${API_BASE}/simulations/run`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            design_id: currentDesignId,
                            simulation_mode: 'quick_preview',
                            wind_speed_kmh: windSpeed,
                            moving_floor: document.getElementById('toggle-moving-floor').checked,
                            scale_mode: scaleMode,
                            material: material,
                            engine_power_hp: enginePowerHp,
                            custom_mass_kg: customMassKg
                        })
                    });

                    if (!response.ok) {
                        throw new Error(`Simulation failed: ${response.statusText}`);
                    }

                    const results = await response.json();
                    
                    // Snappy and satisfying 1.5s interactive loop delay
                    await new Promise(resolve => setTimeout(resolve, 1500));
                    
                    displayResults(results);
                    updateStatus('Simulation complete!', 'complete');
                    
                } catch (error) {
                    console.error('Simulation error:', error);
                    updateStatus('Simulation failed: ' + error.message, 'ready');
                    alert('Simulation failed: ' + error.message);
                } finally {
                    // Hide loader and restore button state
                    loader.style.display = 'none';
                    loaderText.textContent = 'Loading STL model...'; // reset default
                    simulationRunning = false;
                    this.disabled = false;
                }
            });

            // Display simulation results in metrics grid
            function displayResults(results) {
                const metrics = getFormattedMetrics(results.geometry, results.vehicle_mass_kg);

                document.getElementById('geom-length').textContent = metrics.length;
                document.getElementById('geom-width').textContent = metrics.width;
                document.getElementById('geom-height').textContent = metrics.height;
                document.getElementById('geom-frontal-area').textContent = metrics.frontalArea;
                document.getElementById('geom-volume').textContent = metrics.volume;
                
                const materialSelect = document.getElementById('material');
                const selectedMaterialLabel = materialSelect ? materialSelect.options[materialSelect.selectedIndex].text : 'Selected';
                document.getElementById('geom-mass-label').textContent = `Mass (${selectedMaterialLabel})`;
                
                const massInput = document.getElementById('geom-mass-input');
                if (massInput) {
                    massInput.value = metrics.massVal;
                }
                const massUnit = document.getElementById('geom-mass-unit');
                if (massUnit) {
                    massUnit.textContent = metrics.massUnit;
                }

                const metricCards = document.querySelectorAll('.metric-card');
                
                // Cd
                metricCards[0].style.opacity = '1';
                metricCards[0].querySelector('.metric-value').innerHTML = 
                    `${results.estimated_cd.toFixed(3)} <span class="metric-unit"></span>`;
                metricCards[0].querySelector('.metric-subtext').textContent = 
                    `Reynolds: ${results.reynolds_number.toExponential(2)}`;
                
                // Mass
                metricCards[1].style.opacity = '1';
                metricCards[1].querySelector('.metric-value').innerHTML = 
                    `${metrics.massVal} <span class="metric-unit">${metrics.massUnit}</span>`;
                metricCards[1].querySelector('.metric-subtext').textContent = 
                    `Material: ${selectedMaterialLabel} | Frontal Area: ${metrics.frontalArea}`;
                
                // Top Speed
                const scaleMode = document.getElementById('scaleMode').value;
                const enginePower = document.getElementById('enginePower').value;
                const powerUnit = scaleMode === 'miniature' ? 'W' : 'HP';
                
                metricCards[2].style.opacity = '1';
                metricCards[2].querySelector('.metric-value').innerHTML = 
                    `${Math.round(results.top_speed_kmh)} <span class="metric-unit">km/h</span>`;
                metricCards[2].querySelector('.metric-subtext').textContent = `At ${enginePower} ${powerUnit}`;
                
                // 0-100 or 0-60 acceleration
                const accelCard = metricCards[3];
                accelCard.style.opacity = '1';
                
                if (scaleMode === 'miniature') {
                    accelCard.querySelector('.metric-label').textContent = '0-60 km/h';
                    if (results.acceleration_0_60_sec) {
                        accelCard.querySelector('.metric-value').innerHTML = 
                            `${results.acceleration_0_60_sec.toFixed(2)} <span class="metric-unit">sec</span>`;
                        accelCard.querySelector('.metric-subtext').textContent = 'Acceleration time';
                    } else {
                        accelCard.querySelector('.metric-value').innerHTML = 
                            `N/A <span class="metric-unit"></span>`;
                        accelCard.querySelector('.metric-subtext').textContent = 'Insufficient power';
                    }
                } else {
                    accelCard.querySelector('.metric-label').textContent = '0-100 km/h';
                    if (results.acceleration_0_100_sec) {
                        accelCard.querySelector('.metric-value').innerHTML = 
                            `${results.acceleration_0_100_sec.toFixed(2)} <span class="metric-unit">sec</span>`;
                        accelCard.querySelector('.metric-subtext').textContent = 'Acceleration time';
                    } else {
                        accelCard.querySelector('.metric-value').innerHTML = 
                            `N/A <span class="metric-unit"></span>`;
                        accelCard.querySelector('.metric-subtext').textContent = 'Insufficient power';
                    }
                }
                
                // Drag Force
                const windSpeed = parseFloat(document.getElementById('windSpeed').value);
                metricCards[4].style.opacity = '1';
                metricCards[4].querySelector('.metric-label').textContent = `Drag Force @ ${windSpeed} km/h`;
                metricCards[4].querySelector('.metric-value').innerHTML = 
                    `${Math.round(results.drag_force_n)} <span class="metric-unit">N</span>`;
                
                sessionStorage.setItem('lastSimulation', JSON.stringify(results));
            }

            // Update status badge message & styling
            function updateStatus(message, status) {
                const statusBadge = document.querySelector('.status-badge');
                if (statusBadge) {
                    statusBadge.textContent = message;
                    statusBadge.className = 'status-badge status-' + status;
                }
            }

            // Initialize Three.js on page load
            initThree();
            updatePowerSliderUI();
            updateStatus('Ready - Upload an STL file to begin', 'ready');
            document.querySelector('.btn-primary').disabled = true;
        });
    