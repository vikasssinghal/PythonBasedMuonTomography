# 3D Muon Scattering Tomography Simulator

This project implements a complete, highly optimized, and vectorized 3D Muon Scattering Tomography (MST) simulation in Python. It models a realistic cosmic-ray tracking detector system, simulates Multiple Coulomb Scattering (MCS) through a steel container housing an unknown object, reconstructs the muon trajectories, calculates the Point of Closest Approach (POCA) to yield a 3D density map, and classifies the hidden material.

## 🚀 Features

- **Object-Oriented Architecture**: Modular design representing `ScintillatorPlane`, `FiberLayer`, `MAPMT`, `DetectorStack`, `Container`, `HiddenObject`, `Muon`, `Track`, `ScatteringSimulator`, `TrackReconstructor`, `POCAReconstructor`, `MaterialClassifier`, and `Simulation`.
- **Vectorized MCS & Tracking**: Uses NumPy vectorization for intersection, scattering, and least-squares tracking, capable of simulating 100,000 muons in less than a second.
- **Realistic Readout Routing**: Models 100 X-fibers and 100 Y-fibers per plane, including the smooth curved routing around detector edges to the two MAPMT readout modules.
- **3D POCA Reconstruction**: Computes the Point of Closest Approach for scattered tracks and voxelizes the container space into a 1 cm³ grid weighted by the scattering angle squared.
- **Self-Calibrating Classifier**: Compares reconstructed statistics against expected Highland models calibrated to the exact momenta and path lengths of intersecting muons.
- **Interactive 3D Event Display**: Renders detector planes, fiber meshes, MAPMTs, tracks, hit pixels, POCA points, and a voxel density cloud in Plotly.

---

## 📦 Project Structure & File Specifications

This repository is structured as a modular Python package (`MuonTomography/`)[cite: 6, 7]. Below is an explicit, file-by-file breakdown detailing exactly what is implemented inside every component:

### Core Configurations & Utilities
*   **`__init__.py`**
    *   **Description**: Marks the directory as a structured, importable Python package[cite: 6].
    *   **Role**: Initializes the namespace and facilitates clean, modular package-level imports across the simulation pipeline[cite: 6, 7].
*   **`config.py`**
    *   **Description**: The centralized source of truth for global physical constants, detector dimensions, layout bounds, and algorithmic parameters[cite: 1].
    *   **Key Specifications**: 
        *   Defines active tracking areas ($100\text{ cm} \times 100\text{ cm}$), scintillator slab thicknesses ($7.8\text{ cm}$), and a $1\text{ cm}$ fiber pitch yielding $100$ individual fibers per axis[cite: 1].
        *   Hardcodes the spatial layout of all 8 tracker planes along the $Z$-axis, dividing them into an upper stack (Planes 1–4) and a lower stack (Planes 5–8) around a central $60\text{ cm}$ container clearance gap[cite: 1].
        *   Establishes cosmic muon generator settings, including flat momentum ranges ($1{,}000\text{ to }10{,}000\text{ MeV/c}$) and an angular cosmic spread[cite: 1].
        *   Configures 3D reconstruction parameters such as voxel dimensional sizes ($1\text{ cm}^3$), grid dimensions ($40 \times 40 \times 40$ voxels), and POCA visualization thresholds[cite: 1].
*   **`materials.py`**
    *   **Description**: A physical lookup database storing elemental material constants required by the scattering physics engine[cite: 2, 9].
    *   **Key Specifications**:
        *   Implements a structured `Material` data class that links a substance's identity to its precise Radiation Length ($X_0$ in $\text{cm}$) and density ($\text{g/cm}^3$)[cite: 9].
        *   Exposes a comprehensive dictionary named `MATERIALS` pre-populated with standard reference media spanning low-Z and high-Z materials: Air, Water, Plastic, Aluminium, Concrete, Iron, Copper, Lead, Tungsten, and Uranium[cite: 2, 9].

### Mathematical & Geometric Engines
*   **`geometry.py`**
    *   **Description**: The vector math backbone of the simulator, hosting optimized NumPy equations that solve algebraic intersections instantly without nested loops[cite: 5].
    *   **Key Specifications**:
        *   `intersect_aabb_vec`: Computes vectorized intersections between linear trajectories (rays) and Axis-Aligned Bounding Boxes (AABB) to extract entry/exit thresholds[cite: 5].
        *   `intersect_sphere_vec` & `intersect_cylinder_vec`: Leverages quadratic equations to find exact analytical track entry/exit steps for spherical and Z-aligned cylindrical solids[cite: 5].
        *   `get_shape_thickness_vec`: Functions as a master gateway calculating the exact integrated path length (thickness) penetrated by hundreds of thousands of concurrent muons inside complex geometry variations, including a custom composite 3D cross[cite: 5].

### Detector Hardware & Readout Simulation
*   **`fiber.py`**
    *   **Description**: Simulates the physical behavior and custom routing geometry of wavelength-shifting optical components[cite: 4].
    *   **Key Specifications**:
        *   `Fiber`: Tracks localized $X$ or $Y$ intersection lines[cite: 3, 4]. It produces a high-fidelity 3D path combining the straight tracking line crossing the active scintillator volume with a smooth quadratic Bezier curve that realistically maps the edge onto a tight $10 \times 10$ array grid on the photodetector module[cite: 4].
        *   `FiberLayer`: Coordinates a strict parallel grid array of exactly 100 fibers along an orthogonal orientation[cite: 4].
*   **`mapmt.py`**
    *   **Description**: Models electronic data acquisition and charge collection hardware attached to the detector system[cite: 8].
    *   **Key Specifications**:
        *   `MAPMT`: Replicates a Multi-Anode Photomultiplier Tube module, maintaining its dedicated position offsets, channel registries, and state management[cite: 3, 8].
        *   Tracks digital readout structures containing activated channel indices, incoming time-of-flight measurements, and raw collected signal amplitudes[cite: 8].
*   **`detector.py`**
    *   **Description**: Integrates tracking meshes, logic planes, and hardware readouts into unified high-level tracking modules[cite: 3].
    *   **Key Specifications**:
        *   `ScintillatorPlane`: Unifies an X fiber layer, a Y fiber layer, and two independent, orthogonal MAPMT readout components[cite: 3]. It maps floating-point coordinates into discrete fiber indices and applies a Poisson distribution (mean of 25 photoelectrons) to simulate scintillation light fluctuations[cite: 3].
        *   `DetectorStack`: Coordinates the full 8-plane tracker array[cite: 3]. It manages mass vectorized projections across planes, computes timing offsets, and filters signal lists captured inside active target areas[cite: 3].

### Physical Environment & Kinematics
*   **`container.py`**
    *   **Description**: Establishes the structural inspection volume and targets hidden inside the scanning region[cite: 2].
    *   **Key Specifications**:
        *   `Container`: Represents the physical cargo environment—a $40\text{ cm}^3$ steel container volume centered at $(0,0,0)$ with $0.5\text{ cm}$ thick structural boundary walls[cite: 2].
        *   `HiddenObject`: Programmatically spawns hidden targets inside the core inspection cavity[cite: 2]. It randomizes or constructs a dedicated configuration tracking its structural type (`cube`, `sphere`, `cylinder`, or an irregular composite 3D cross), physical material type, sizing parameters, and position offsets[cite: 2].
*   **`muon_generator.py`**
    *   **Description**: Simulates the natural downward flux, spatial profiles, and kinematics of incoming cosmic ray particles[cite: 10].
    *   **Key Specifications**:
        *   `Muon`: A structured object holding metadata for an individual particle, tracking its custom ID, initial position vector, direction unit vectors, total momentum, and velocity[cite: 10].
        *   `MuonGenerator`: Spawns large-scale, high-statistics batches of muons simultaneously using vectorized NumPy models[cite: 10]. It applies precise physical relationships to calculate relativistic particle speeds ($\beta$) alongside an inverse-CDF implementation that correctly samples an atmospheric cosmic-ray angular intensity matching a realistic $\cos^2(\theta)$ distribution[cite: 10].

### Specialized Physics, Tracking, & Visualization
*   **`scattering.py`**
    *   **Description**: The physical interaction engine implementing Multiple Coulomb Scattering (MCS) models.
    *   **Key Specifications**: Utilizes the structural thickness computed by `geometry.py` and materials properties via `materials.py` to deflect individual muon trajectory vectors randomly according to the momentum-dependent Highland formula.
*   **`tracking.py`**
    *   **Description**: Provides statistical path-fitting algorithms for raw hit readouts.
    *   **Key Specifications**: Houses the track reconstruction algorithms that fit localized coordinate hits across both tracking arms using vectorized linear regression (least-squares methods), extracting clear incoming and outgoing direction vectors for each triggered event.
*   **`reconstruction.py`**
    *   **Description**: Implements 3D spatial voxelization and localized dense element identification algorithms.
    *   **Key Specifications**:
        *   `POCAReconstructor`: Executes the 3D Point of Closest Approach (POCA) routine to locate vertex intersection regions where trajectories bend. Projects these points into a $1\text{ cm}^3$ voxel tensor to yield a high-fidelity density map[cite: 1, 7].
        *   `MaterialClassifier`: Compares calculated track deflections against theoretical models calibrated for material paths to statistically output density, radiation length, and identity configurations.
*   **`visualization.py`**
    *   **Description**: Generates high-fidelity user visualizer elements[cite: 7].
    *   **Key Specifications**: Integrates global geometries into multi-mesh elements using Plotly, generating active fiber arrays, hit coordinates, 3D track path arrows, localized POCA point groupings, and bounded voxel clouds[cite: 7].

### Orchestration & Main Entrypoint
*   **`main.py`**
    *   **Description**: The main executor and orchestration pipeline that connects every subsystem into a coherent command-line execution app[cite: 7].
    *   **Key Specifications**:
        *   `Simulation`: Manages the global execution flow[cite: 7]. It triggers the generation of cosmic ray batches, steps through tracking interactions across the upper planes, calls the external scattering mechanics inside the container space, logs responses across the lower tracking arm, and applies coincidence filters to isolate tracks hitting all 8 planes[cite: 7].
        *   `main()` & Analysis Routines: Orchestrates single-run scenarios, coordinates validation test loops, plots terminal-based ASCII histograms for immediate data inspection, and writes an interactive 3D event visualization into an autonomous HTML file (`muon_tomography_display.html`)[cite: 7].

---

## 🛠️ Requirements

The project requires Python 3 and the following dependencies:

```bash
pip install numpy plotly
