import numpy as np

# Detector geometry configurations
ACTIVE_AREA_SIZE = 100.0   # 100 cm x 100 cm
SLAB_THICKNESS = 7.8      # 7.8 cm
FIBER_PITCH = 1.0         # 1 cm pitch
NUM_FIBERS = 100          # 100 fibers per axis
MAPMT_SIZE = 8.0          # MAPMT box size: 8 cm x 8 cm x 4 cm

# Placement configurations
PLANE_SPACING = 15.0      # Spacing between planes in the same stack (cm)
STACK_GAP = 60.0          # Distance between Plane 4 and Plane 5 (container space)
CONTAINER_SIZE = 40.0     # 40 cm x 40 cm x 40 cm steel container
CONTAINER_WALL_THICKNESS = 0.5  # Steel wall thickness (cm)

# Center positions for planes in Z (computed based on spacing and gap)
# Plane Z positions:
# Plane 1: +75 cm
# Plane 2: +60 cm
# Plane 3: +45 cm
# Plane 4: +30 cm
# Container space: Z between -20 cm and +20 cm
# Plane 5: -30 cm
# Plane 6: -45 cm
# Plane 7: -60 cm
# Plane 8: -75 cm
Z_PLANES = [
    30.0 + 3.0 * PLANE_SPACING, # Plane 1
    30.0 + 2.0 * PLANE_SPACING, # Plane 2
    30.0 + PLANE_SPACING,       # Plane 3
    30.0,                       # Plane 4
    -30.0,                      # Plane 5
    -30.0 - PLANE_SPACING,      # Plane 6
    -30.0 - 2.0 * PLANE_SPACING,# Plane 7
    -30.0 - 3.0 * PLANE_SPACING # Plane 8
]

# Muon Generator configurations
DEFAULT_NUM_MUONS = 100000 # Default number of cosmic muons for full run
MUON_MIN_MOMENTUM = 1000.0  # 1 GeV/c (in MeV/c)
MUON_MAX_MOMENTUM = 10000.0 # 10 GeV/c (in MeV/c)
MUON_ANGULAR_SPREAD = 15.0  # Theta spread in degrees

# Reconstruction configurations
VOXEL_SIZE = 1.0          # 1 cm^3 voxels
CONTAINER_VOXELS = 40     # Number of voxels along each dimension (40 cm container / 1 cm voxel)
POCA_THRESHOLD = 0.05     # Weight threshold or angle threshold for POCA visualization

# Steel container material reference
STEEL_RADIATION_LENGTH = 1.76  # cm (Iron)
STEEL_DENSITY = 7.87          # g/cm^3
