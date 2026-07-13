import numpy as np
import random
from MuonTomography.config import CONTAINER_SIZE, CONTAINER_WALL_THICKNESS
from MuonTomography.materials import MATERIALS

class HiddenObject:
    def __init__(self, shape_type=None, material_name=None, center=None):
        """
        Represents the unknown target object hidden inside the container.
        
        Args:
            shape_type (str): 'cube', 'sphere', 'cylinder', or 'irregular'. If None, chosen randomly.
            material_name (str): Material name. If None, chosen randomly.
            center (np.ndarray): 3D position (x, y, z). If None, chosen randomly with a slight offset.
        """
        # 1. Select material
        if material_name is None:
            # Randomly select one material from candidates
            material_name = random.choice(list(MATERIALS.keys()))
        self.material_name = material_name
        self.material = MATERIALS[material_name]
        
        # 2. Select shape
        if shape_type is None:
            shape_type = random.choice(['cube', 'sphere', 'cylinder', 'irregular'])
        self.shape_type = shape_type
        
        # 3. Setup position (slight offset from origin to test reconstruction)
        if center is None:
            # Slightly offset from container center (0,0,0)
            cx = random.uniform(-4.0, 4.0)
            cy = random.uniform(-4.0, 4.0)
            cz = random.uniform(-4.0, 4.0)
            self.center = np.array([cx, cy, cz])
        else:
            self.center = np.array(center, dtype=float)
            
        # 4. Setup dimensions based on shape
        self.params = {}
        if self.shape_type == 'cube':
            self.params['size'] = random.uniform(20.0, 28.0) # size in cm
        elif self.shape_type == 'sphere':
            self.params['radius'] = random.uniform(10.0, 14.0) # radius in cm
        elif self.shape_type == 'cylinder':
            self.params['radius'] = random.uniform(8.0, 12.0) # radius in cm
            self.params['height'] = random.uniform(22.0, 30.0) # height in cm
        elif self.shape_type == 'irregular':
            # Cross shape parameters
            self.params['cross_width'] = 30.0
            self.params['cross_thickness'] = 10.0
            
    def get_summary(self):
        """Returns the ground truth description of the hidden object."""
        desc = f"Shape: {self.shape_type.capitalize()}, Material: {self.material_name}, "
        desc += f"Position: ({self.center[0]:.2f}, {self.center[1]:.2f}, {self.center[2]:.2f}) cm, "
        if self.shape_type == 'cube':
            desc += f"Size: {self.params['size']:.1f} cm"
        elif self.shape_type == 'sphere':
            desc += f"Radius: {self.params['radius']:.1f} cm"
        elif self.shape_type == 'cylinder':
            desc += f"Radius: {self.params['radius']:.1f} cm, Height: {self.params['height']:.1f} cm"
        elif self.shape_type == 'irregular':
            desc += "3D Cross (30 cm span, 10 cm limb width)"
        return desc

class Container:
    def __init__(self, hidden_object=None):
        """
        Represents the steel container.
        
        Args:
            hidden_object (HiddenObject): Optional pre-defined hidden object.
        """
        self.size = CONTAINER_SIZE
        self.wall_thickness = CONTAINER_WALL_THICKNESS
        self.center = np.zeros(3) # Centered at origin (0, 0, 0)
        
        # Steel wall material properties
        self.wall_radiation_length = MATERIALS['Iron'].radiation_length
        self.wall_density = MATERIALS['Iron'].density
        
        # Outer AABB
        self.outer_min = self.center - self.size / 2.0
        self.outer_max = self.center + self.size / 2.0
        
        # Inner cavity AABB
        self.inner_min = self.outer_min + self.wall_thickness
        self.inner_max = self.outer_max - self.wall_thickness
        
        # Instantiate the hidden object inside
        if hidden_object is None:
            self.hidden_object = HiddenObject()
        else:
            self.hidden_object = hidden_object
