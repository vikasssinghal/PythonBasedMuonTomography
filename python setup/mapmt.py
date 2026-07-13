import numpy as np

class MAPMT:
    def __init__(self, plane_id, axis, center, size=(8.0, 8.0, 4.0)):
        """
        Represents a Multi-Anode Photomultiplier Tube (MAPMT) readout module.
        
        Args:
            plane_id (int): ID of the scintillator plane (1-8)
            axis (str): 'X' or 'Y' indicating which fiber coordinate it reads
            center (np.ndarray): 3D position (x, y, z) of the MAPMT block center
            size (tuple): Dimensions of the MAPMT box (dx, dy, dz)
        """
        self.plane_id = plane_id
        self.axis = axis
        self.center = np.array(center, dtype=float)
        self.size = np.array(size, dtype=float)
        self.hits = [] # List of hits registered by this MAPMT

    def reset(self):
        """Clear registered hits."""
        self.hits = []

    def register_hit(self, fiber_idx, charge, time):
        """
        Registers a fiber activation.
        
        Args:
            fiber_idx (int): Channel index (0-99)
            charge (float): Signal amplitude (e.g. simulated photoelectrons)
            time (float): Hit arrival time (ns)
        """
        self.hits.append({
            'fiber_index': fiber_idx,
            'charge': charge,
            'time': time
        })

    def get_hits_summary(self):
        return {
            'plane_id': self.plane_id,
            'axis': self.axis,
            'num_active_channels': len(self.hits),
            'active_channels': [h['fiber_index'] for h in self.hits]
        }
