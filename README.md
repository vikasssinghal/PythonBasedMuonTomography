# Muon Tomography Simulation Platform

<p align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-yellow.svg)
![Three.js](https://img.shields.io/badge/Three.js-WebGL-green.svg)
![License](https://img.shields.io/badge/License-MIT-success.svg)

*A complete simulation and visualization platform for **Muon Scattering Tomography (MST)**.*

</p>

---

## Overview

This repository contains a complete end-to-end implementation of a **Muon Scattering Tomography (MST)** system. It combines a high-performance Python simulation engine with an interactive browser-based visualization dashboard to model, reconstruct, and analyze cosmic-ray muons passing through unknown materials.

The project demonstrates the complete workflow of a muon tomography experiment:

* Cosmic muon generation
* Detector geometry simulation
* Plastic scintillator response
* Optical fiber routing
* MAPMT readout
* Multiple Coulomb Scattering (MCS)
* Track reconstruction
* Point of Closest Approach (PoCA)
* Material identification
* Interactive 3D visualization

The repository is designed for educational purposes, research, and rapid prototyping of muon tomography systems.

---

# Repository Structure

```
muon/
│
├── pythonsetup/
│   ├── Simulation Engine
│   ├── Detector Geometry
│   ├── Physics Models
│   ├── Muon Generator
│   ├── Reconstruction Algorithms
│   ├── Material Classification
│   └── README.md
│
├── web/
│   ├── Interactive Dashboard
│   ├── Three.js Visualization
│   ├── Physics Animation
│   ├── User Interface
│   └── README.md
│
└── README.md
```

---

# Project Components

## 1. Python Simulation Engine

Located in:

```
pythonsetup/
```

This module performs the complete physics simulation of the detector system.

### Features

* Modular detector geometry
* Plastic scintillator detector planes
* Optical fiber readout
* MAPMT simulation
* Cosmic muon generation
* Multiple Coulomb Scattering (MCS)
* Track fitting
* Point of Closest Approach (PoCA)
* Material classification
* High-performance NumPy implementation

📖 For complete documentation, installation instructions, and implementation details, see:

```
pythonsetup/README.md
```

---

## 2. Web Visualization Dashboard

Located in:

```
web/
```

The web application provides a real-time 3D visualization of the detector and reconstructed events.

### Features

* Interactive detector visualization
* Three.js rendering
* Detector animation
* Muon trajectory display
* Hidden object visualization
* Material reconstruction display
* Responsive UI
* Modern WebGL graphics

📖 For setup instructions and implementation details, see:

```
web/README.md
```

---

# Complete Workflow

```
Cosmic Muons
      │
      ▼
Detector Planes
      │
      ▼
Plastic Scintillators
      │
      ▼
Optical Fibers
      │
      ▼
MAPMT Readout
      │
      ▼
Track Reconstruction
      │
      ▼
Multiple Coulomb Scattering
      │
      ▼
PoCA Reconstruction
      │
      ▼
Voxel Density Map
      │
      ▼
Material Classification
      │
      ▼
Interactive 3D Visualization
```

---

# Technologies Used

### Programming Languages

* Python
* JavaScript
* HTML5
* CSS3

### Scientific Libraries

* NumPy
* Plotly

### Web Technologies

* Three.js
* WebGL

### Algorithms

* Multiple Coulomb Scattering (Highland Formula)
* Least Squares Track Fitting
* Point of Closest Approach (PoCA)
* Voxel-based Density Reconstruction
* Material Classification

---

# Applications

This project can be used for:

* Muon tomography research
* Detector simulation
* Particle physics education
* Nuclear security studies
* Non-destructive testing
* Radiation imaging research
* Algorithm development
* Scientific visualization

---

# Getting Started

Clone the repository:

```bash
git clone https://github.com/prathamchawda231-netizen/muon.git
cd muon
```

Then choose the component you want to use.

### Python Simulation

```bash
cd pythonsetup
```

Follow the instructions in:

```
pythonsetup/README.md
```

### Web Dashboard

```bash
cd web
```

Open the project according to the instructions in:

```
web/README.md
```

---

# Documentation

| Component               | Description                                            |
| ----------------------- | ------------------------------------------------------ |
| `pythonsetup/README.md` | Complete documentation for the simulation engine       |
| `web/README.md`         | Complete documentation for the visualization dashboard |

---

# Future Improvements

* Geant4 integration
* ROOT output support
* GPU acceleration
* Machine learning–based material classification
* Detector calibration tools
* Real detector data support
* Distributed simulation
* Docker deployment
* Cloud-based visualization

---

# Contributing

Contributions are welcome.

If you would like to improve the project:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Submit a Pull Request.

---

# License

This project is released under the MIT License unless otherwise specified.

---

# Acknowledgements

This project is inspired by research in cosmic-ray muon tomography, detector physics, and particle tracking. It is intended as an educational and research-oriented implementation demonstrating the principles of Muon Scattering Tomography.

---

## Explore the Project

* **Simulation Engine:** `pythonsetup/`
* **Visualization Dashboard:** `web/`

Each component includes its own detailed documentation covering architecture, installation, usage, and implementation details.
