# Muon Tomography Simulation Platform
### Geant4-Based Monte Carlo Simulation, Reconstruction & Material Discrimination

<p align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![C++](https://img.shields.io/badge/C++-17-blue.svg)
![Geant4](https://img.shields.io/badge/Geant4-11.3.2-red.svg)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-yellow.svg)
![Three.js](https://img.shields.io/badge/Three.js-WebGL-green.svg)
![License](https://img.shields.io/badge/License-MIT-success.svg)

**A hybrid computational framework for Muon Scattering Tomography (MST), combining Geant4 Monte Carlo particle transport, Python-based reconstruction, and interactive 3D visualization.**

</p>

---

## 1. Overview

The Muon Tomography Simulation Platform is a research-oriented computational framework designed to simulate, reconstruct, and investigate the interactions of cosmic-ray muons with different materials.

The project extends an existing Python-based muon tomography platform by introducing a **Geant4-based Monte Carlo simulation backend** for particle transport and material interaction studies.

The framework combines three major components:

- **Geant4 (C++):** Particle generation, detector geometry, material interactions, and Monte Carlo transport.
- **Python:** Detector hit processing, track reconstruction, Point of Closest Approach (PoCA), and material analysis.
- **Three.js:** Interactive browser-based visualization of detector geometry, particle trajectories, and reconstruction results.

The primary research direction is to investigate how different material compositions influence muon scattering behaviour and explore the potential of scattering signatures for material discrimination.

### Research Objectives

1. Simulate cosmic-ray muon transport through different materials.
2. Investigate multiple Coulomb scattering (MCS) under different material conditions.
3. Study the relationship between material composition, radiation length, thickness, and scattering distributions.
4. Reconstruct particle trajectories using detector hit information.
5. Investigate material discrimination using reconstructed scattering characteristics.
6. Establish a computational framework that can eventually be compared with experimental detector data.

---

## 2. Scientific Background

### Muon Scattering Tomography

Cosmic-ray muons are highly penetrating charged particles that continuously reach Earth's surface.

As muons pass through matter, they undergo electromagnetic interactions, including multiple Coulomb scattering.

The resulting changes in particle direction contain information about the material traversed.

The approximate projected RMS scattering angle can be estimated using the Highland formula:

\[
\theta_0 \approx
\frac{13.6\,\mathrm{MeV}}{\beta pc}
\sqrt{\frac{x}{X_0}}
\left[
1+0.038\ln\left(\frac{x}{X_0}\right)
\right]
\]

Where:

- \(\theta_0\): Projected RMS scattering angle.
- \(p\): Muon momentum.
- \(\beta\): Muon velocity divided by the speed of light.
- \(x\): Material thickness.
- \(X_0\): Radiation length of the material.

The Highland formula provides an analytical approximation. Geant4 allows the framework to investigate particle transport and scattering through Monte Carlo physics processes rather than relying exclusively on this parameterization.

**Important:** Scattering depends on momentum, material composition, radiation length, and path length. Density alone does not uniquely determine the scattering response.

---

## 3. Repository Architecture

```text
PythonBasedMuonTomography/
│
├── MuonTomography/
│   ├── tracking.py
│   ├── reconstruction.py
│   ├── materials.py
│   └── ...
│
├── geant4_simulation/
│   ├── include/
│   │   └── DetectorConstruction.hh
│   ├── src/
│   │   └── DetectorConstruction.cc
│   └── CMakeLists.txt
│
├── geant4_bridge.py
├── export_web_data.py
│
├── data/
│   ├── geant4/
│   └── test_results.csv
│
├── web/
│   ├── geant4_dashboard.html
│   ├── physics.js
│   └── data.json
│
└── README.md
```

*Note: This is the documented project layout. Individual source files and additional directories may vary between branches.*

---

## 4. System Components

### 4.1 Geant4 Monte Carlo Simulation

**Location:** `geant4_simulation/`

This is the physics simulation backend introduced as an extension to the original Python-based implementation.

Geant4 (Geometry and Tracking) is a Monte Carlo simulation toolkit developed for modelling the passage of particles through matter.

The simulation backend is intended to handle:

- Particle generation and transport.
- Detector geometry construction.
- Material definition and assignment.
- Electromagnetic interactions.
- Multiple Coulomb scattering.
- Energy deposition and detector hit scoring.
- Event-level simulation output.

The simulation generates detector information that can subsequently be processed by the Python reconstruction pipeline.

**Version:** Geant4 11.3.2

### 4.2 Python Reconstruction Engine

**Location:** `MuonTomography/`

The existing Python reconstruction framework is retained and integrated with the Geant4 simulation output.

Its responsibilities include:

- Detector hit processing.
- Incoming and outgoing track reconstruction.
- Least Squares track fitting.
- Scattering-angle calculation.
- Point of Closest Approach (PoCA).
- Voxel-based reconstruction.
- Material classification.

The Python layer acts as the analysis and reconstruction interface between Geant4 and the visualization dashboard.

### 4.3 Geant4-Python Bridge

**File:** `geant4_bridge.py`

The bridge connects the Geant4 simulation output with the existing Python reconstruction algorithms.

Its workflow includes:

1. Reading Geant4-generated CSV data.
2. Grouping detector hits by event and detector plane.
3. Selecting usable detector events.
4. Separating incoming and outgoing track measurements.
5. Reconstructing particle trajectories.
6. Calculating scattering characteristics.
7. Executing PoCA reconstruction.
8. Passing reconstructed information to material analysis.

### 4.4 Web Data Export

**File:** `export_web_data.py`

This module exports reconstruction results into JSON format for browser-based visualization.

The exported information can include:

- Reconstructed muon trajectories.
- Detector hit positions.
- PoCA coordinates.
- Voxel reconstruction data.
- Material-related visualization information.

### 4.5 Interactive 3D Dashboard

**Location:** `web/`

The visualization layer uses Three.js and WebGL.

Features include:

- Interactive detector geometry.
- Muon trajectory visualization.
- Incoming and outgoing particle tracks.
- Hidden-object representation.
- PoCA point visualization.
- Voxel-based reconstruction display.

The dashboard provides a visual interface for inspecting simulation and reconstruction outputs.

---

## 5. Complete Simulation Workflow

```text
                 COSMIC-RAY MUONS
                         |
                         v
              GEANT4 PARTICLE GENERATION
                         |
                         v
                 DETECTOR GEOMETRY
                         |
                         v
                MATERIAL INTERACTION
                         |
                         v
             MONTE CARLO PARTICLE TRANSPORT
                         |
                         v
               MULTIPLE COULOMB SCATTERING
                         |
                         v
                 DETECTOR HIT SCORING
                         |
                         v
                    CSV OUTPUT
                         |
                         v
                 GEANT4-PYTHON BRIDGE
                         |
                         v
                TRACK RECONSTRUCTION
                         |
                         v
                 SCATTERING ANALYSIS
                         |
                         v
                 PoCA RECONSTRUCTION
                         |
                         v
                VOXEL-BASED ANALYSIS
                         |
                         v
                MATERIAL DISCRIMINATION
                         |
                         v
                  JSON DATA EXPORT
                         |
                         v
                THREE.JS VISUALIZATION
```

---

## 6. Material Investigation

An important objective of the Geant4 extension is to investigate material-dependent muon scattering.

The framework can be used to compare different materials under controlled simulation conditions.

### Initial Material Test Matrix

| Material | Approximate Density (g/cm³) |
|---|---:|
| Aluminium | 2.70 |
| Iron | 7.87 |
| Copper | 8.96 |
| Lead | 11.34 |
| Tungsten | 19.25 |
| Uranium | 19.05 |

These are reference densities. The actual material composition and properties used by Geant4 should be verified in the simulation.

### Proposed Experimental Parameters

- Incident muon momentum.
- Incident angular distribution.
- Material composition.
- Material thickness.
- Radiation length.
- Scattering-angle distribution.
- Energy loss.
- Detector spatial resolution.
- Number of simulated events.

### Suggested Investigation Strategy

**Experiment 1 — Material dependence**

Compare scattering distributions for different materials using identical geometry and incident particle conditions.

**Experiment 2 — Thickness dependence**

Investigate how scattering changes as the thickness of a particular material increases.

**Experiment 3 — Momentum dependence**

Study how different incident muon momenta affect material-dependent scattering.

**Experiment 4 — Material discrimination**

Investigate whether reconstructed scattering signatures can distinguish materials with similar physical properties.

**Experiment 5 — Reconstruction performance**

Evaluate how detector resolution, event statistics, and track reconstruction affect material identification.

For meaningful comparisons, both equal physical thickness and equal areal density conditions should be considered.

---

## 7. Preliminary Simulation Results

The following results are from an initial six-material simulation and classification test using 5,000 simulated muons per run.

| True Material | Predicted Material | Reported Confidence | Mean Scattering Angle |
|---|---|---:|---:|
| Aluminium | Aluminium | 75.90% | 0.0087 rad |
| Iron | Iron | 81.97% | 0.0197 rad |
| Copper | Copper | 74.14% | 0.0225 rad |
| Lead | Lead | 96.64% | 0.0358 rad |
| Tungsten | Uranium | 60.97% | 0.0489 rad |
| Uranium | Uranium | 61.65% | 0.0515 rad |

**Reported overall identification accuracy: 83.3%.**

These are preliminary reported results, not yet an independently validated performance benchmark.

### Observations

- Tungsten and uranium show overlapping scattering responses in this initial test.
- Material discrimination becomes challenging when scattering distributions overlap.
- A classifier's reported confidence is not necessarily a calibrated probability of correct identification.
- Mean scattering angle alone may not be sufficient for reliable material discrimination.

### Future Validation

The next validation phase should include:

- Repeated independent simulation runs.
- Full scattering-angle distributions.
- Confusion matrices and per-class precision and recall.
- Uncertainty estimates.
- Momentum and path-length control.
- Comparison with analytical scattering predictions.
- Detector-response effects.
- Experimental validation when detector data becomes available.

---

## 8. Installation and Requirements

### System Requirements

- Ubuntu Linux or Ubuntu through WSL2.
- C++17-compatible compiler.
- CMake 3.16 or later.
- Geant4 11.3.2.
- Python 3.10 or later.
- Git.
- Modern browser with WebGL support.

### Step 1 — Install WSL2 (Windows Users)

Open PowerShell as Administrator:

```powershell
wsl --install
```

Restart the computer if requested and launch Ubuntu.

Update Ubuntu:

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2 — Install Build Dependencies

```bash
sudo apt install -y \
    build-essential \
    cmake \
    git \
    wget \
    libxerces-c-dev \
    libexpat1-dev \
    libboost-all-dev
```

### Step 3 — Download Geant4

Download the Geant4 11.3.2 source archive:

```bash
wget https://geant4-data.web.cern.ch/geant4-data/releases/geant4-v11.3.2.tar.gz

tar -xzf geant4-v11.3.2.tar.gz
```

### Step 4 — Build and Install Geant4

```bash
mkdir geant4-build
cd geant4-build

cmake \
  -DCMAKE_INSTALL_PREFIX=/usr/local \
  -DGEANT4_INSTALL_DATA=ON \
  -DGEANT4_BUILD_MULTITHREADED=ON \
  ../geant4-v11.3.2

cmake --build . --parallel 2

sudo cmake --install .
```

The build time depends on the hardware and available resources. Geant4 datasets may also require additional download time and storage.

### Step 5 — Configure the Environment

```bash
source /usr/local/bin/geant4.sh
```

To load the environment automatically in future terminal sessions:

```bash
echo 'source /usr/local/bin/geant4.sh' >> ~/.bashrc

source ~/.bashrc
```

Verify the installation:

```bash
geant4-config --version
```

---

## 9. Running the Project

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Himanshu-dxt/PythonBasedMuonTomography.git

cd PythonBasedMuonTomography
```

If you are using the Geant4 integration branch:

```bash
git checkout geant4-integration
```

### Step 2 — Build the Geant4 Simulation

```bash
cd geant4_simulation

mkdir -p build
cd build

cmake ..

cmake --build . --parallel 2
```

### Step 3 — Run the Simulation

```bash
./muon_sim run.mac
```

The macro configures the run, including the requested number of events.

The expected CSV output is:

```text
data/geant4/muon_hits_nt_Hits.csv
```

The actual output location depends on the configured Geant4 analysis output path.

### Step 4 — Install Python Dependencies

Return to the project root:

```bash
cd ../..
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install numpy pandas scipy
```

### Step 5 — Execute the Reconstruction Bridge

```bash
python geant4_bridge.py
```

The bridge processes the Geant4 detector output and executes the reconstruction pipeline.

### Step 6 — Export Visualization Data

```bash
python export_web_data.py
```

This generates the JSON data consumed by the visualization dashboard.

### Step 7 — Launch the Web Dashboard

```bash
cd web

python3 -m http.server 8000
```

Open:

```text
http://localhost:8000/geant4_dashboard.html
```

The dashboard displays the available detector and reconstruction data.

---

## 10. Technologies Used

### Programming Languages

- C++
- Python
- JavaScript
- HTML5
- CSS3

### Physics and Simulation

- Geant4
- Electromagnetic particle transport
- Multiple Coulomb scattering
- Highland approximation for analytical comparisons

### Scientific Computing

- NumPy
- Pandas
- SciPy

### Reconstruction Algorithms

- Least Squares track fitting
- Point of Closest Approach (PoCA)
- Voxel-based reconstruction
- Material classification

### Visualization

- Three.js
- WebGL
- JSON-based data exchange

### Build System

- CMake
- GCC/G++

---

## 11. Future Development

The project is intended to evolve towards a more comprehensive physics-driven muon tomography framework.

Potential development directions include:

1. **Advanced reconstruction:** Maximum Likelihood Scattering and Displacement (MLSD) and alternative voxel-based methods.
2. **Material discrimination:** Statistical methods using scattering distributions, momentum and reconstructed displacement.
3. **Detector modelling:** Scintillator response, optical photon transport, photosensor response, and realistic detector resolution.
4. **ROOT integration:** Support for structured scientific simulation and experimental data.
5. **Experimental validation:** Comparison with real cosmic-ray muon detector measurements.
6. **Machine learning:** Investigating ML-based material classification and reconstruction improvements.
7. **Performance:** Parallel simulation and computational optimization.

---

## 12. Contributors and Acknowledgements

### Original Framework

**Vikas Singhal**

Original Python-based muon tomography simulator, reconstruction algorithms, and visualization platform.

### Geant4 Extension and Integration

**Himanshu Kumar Dixit**

- Geant4-based simulation integration.
- C++ simulation development.
- Geant4-to-Python data bridge.
- Reconstruction pipeline integration.
- Web data export and dashboard integration.
- Material-dependent muon scattering investigations.

This repository builds upon the original framework while extending its simulation architecture towards Monte Carlo particle transport and physics-driven material investigation.

---

## 13. References and Resources

- [Geant4 Official Website](https://geant4.web.cern.ch/)
- [Geant4 Documentation](https://geant4.web.cern.ch/docs/)
- [Geant4 User Documentation](https://geant4-userdoc.web.cern.ch/)
- [Geant4 Physics Reference Manual](https://geant4-userdoc.web.cern.ch/UsersGuides/PhysicsReferenceManual/html/index.html)
- [Geant4 Source Repository](https://github.com/Geant4/geant4)
- [Muon Tomography Research — Nature](https://www.nature.com/)
- [CERN](https://home.cern/)

---

## 14. License

This project is released under the MIT License, subject to the original repository's licensing terms and applicable third-party dependencies.

---

<p align="center">

**Muon Tomography Simulation Platform**

*From particle transport to material discrimination.*

</p>
