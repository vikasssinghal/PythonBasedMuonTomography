import numpy as np
from MuonTomography.config import ACTIVE_AREA_SIZE, SLAB_THICKNESS, FIBER_PITCH, Z_PLANES
from MuonTomography.fiber import FiberLayer
from MuonTomography.mapmt import MAPMT

class ScintillatorPlane:
    def __init__(self, plane_id, z_center):
        """
        Represents a single detector plane.
        
        Args:
            plane_id (int): 1 to 8
            z_center (float): Z position of the plane center (cm)
        """
        self.plane_id = plane_id
        self.z_center = z_center
        self.thickness = SLAB_THICKNESS
        self.size = np.array([ACTIVE_AREA_SIZE, ACTIVE_AREA_SIZE, SLAB_THICKNESS])
        
        # Fiber layers
        self.x_fiber_layer = FiberLayer('X', z_center)
        self.y_fiber_layer = FiberLayer('Y', z_center)
        
        # MAPMT modules
        # X-MAPMT: mounted on the +Y side (reads X-fibers which route to +Y)
        # Face is at Y = 54.0, center is at (0.0, 56.0, z_center), size is 8 x 4 x 8 (width, depth, height)
        self.x_mapmt = MAPMT(plane_id, 'X', [0.0, 56.0, z_center], size=[8.0, 4.0, 8.0])
        
        # Y-MAPMT: mounted on the +X side (reads Y-fibers which route to +X)
        # Face is at X = 54.0, center is at (56.0, 0.0, z_center), size is 4 x 8 x 8
        self.y_mapmt = MAPMT(plane_id, 'Y', [56.0, 0.0, z_center], size=[4.0, 8.0, 8.0])

    def reset(self):
        """Reset photodetectors."""
        self.x_mapmt.reset()
        self.y_mapmt.reset()

    def process_hit(self, x_hit, y_hit, muon_id, momentum, time):
        """
        Calculates pixel intersections and triggers readout electronics.
        
        Args:
            x_hit (float): X coordinate of hit (cm)
            y_hit (float): Y coordinate of hit (cm)
            muon_id (int): Muon ID
            momentum (float): Muon momentum (MeV/c)
            time (float): Hit time (ns)
            
        Returns:
            dict or None: Hit information if hit was in active area, else None
        """
        half_area = ACTIVE_AREA_SIZE / 2.0
        
        # Check active area
        if -half_area <= x_hit <= half_area and -half_area <= y_hit <= half_area:
            # Determine fibers (pixels)
            pixel_x = int(np.floor((x_hit + half_area) / FIBER_PITCH))
            pixel_y = int(np.floor((y_hit + half_area) / FIBER_PITCH))
            
            # Bound check indices (e.g. exactly 50.0)
            pixel_x = min(max(pixel_x, 0), 99)
            pixel_y = min(max(pixel_y, 0), 99)
            
            # Pixel number is 100 * pixel_y + pixel_x (goes from 0 to 9999)
            pixel_num = pixel_y * 100 + pixel_x
            
            # Simulate signal amplitude (photoelectrons)
            # Typically 20-30 p.e. with Poisson fluctuation
            pe_x = np.random.poisson(25)
            pe_y = np.random.poisson(25)
            
            # Register hit in MAPMTs
            self.x_mapmt.register_hit(pixel_x, pe_x, time)
            self.y_mapmt.register_hit(pixel_y, pe_y, time)
            
            return {
                'muon_id': muon_id,
                'plane_id': self.plane_id,
                'pixel_x': pixel_x,
                'pixel_y': pixel_y,
                'pixel_num': pixel_num,
                'x': x_hit,
                'y': y_hit,
                'z': self.z_center,
                'time': time,
                'momentum': momentum
            }
        return None

class DetectorStack:
    def __init__(self):
        """
        Manages the 8-plane tracker stack.
        """
        self.planes = []
        for i, z in enumerate(Z_PLANES):
            self.planes.append(ScintillatorPlane(i + 1, z))

    def reset(self):
        for plane in self.planes:
            plane.reset()

    def get_plane(self, plane_id):
        return self.planes[plane_id - 1]

    def simulate_hits(self, S, D, muon_ids, momenta, velocities):
        """
        Propagates muons to all planes and registers hits.
        
        Args:
            S (np.ndarray): Muon start positions (N, 3) at Z=85.0
            D (np.ndarray): Muon directions (N, 3)
            muon_ids (np.ndarray): (N,) array of Muon IDs
            momenta (np.ndarray): (N,) array of momenta (MeV/c)
            velocities (np.ndarray): (N,) array of velocities (cm/ns)
            
        Returns:
            list: List of hit records for all planes
        """
        hits = []
        N = S.shape[0]
        
        for plane in self.planes:
            z_plane = plane.z_center
            
            # Time of flight from start position Z to plane Z
            # t_hit = t0 + delta_z / (vz)
            # S[:, 2] is start Z (around 85.0 cm), z_plane is plane Z
            # direction component D[:, 2] is negative, vz = velocity * D[:, 2]
            dz = z_plane - S[:, 2]
            vz = velocities * D[:, 2]
            
            t_flight = dz / vz # Positive time since dz < 0 and vz < 0
            
            # Hit positions
            x_hit = S[:, 0] + t_flight * D[:, 0]
            y_hit = S[:, 1] + t_flight * D[:, 1]
            
            # Check hits
            # To do this in a fast vectorized way, we filter first, then call process_hit
            half_area = ACTIVE_AREA_SIZE / 2.0
            active_mask = (x_hit >= -half_area) & (x_hit <= half_area) & (y_hit >= -half_area) & (y_hit <= half_area)
            
            valid_indices = np.where(active_mask)[0]
            for idx in valid_indices:
                hit_dict = plane.process_hit(
                    x_hit[idx],
                    y_hit[idx],
                    int(muon_ids[idx]),
                    float(momenta[idx]),
                    float(t_flight[idx])
                )
                if hit_dict is not None:
                    hits.append(hit_dict)
                    
        return hits
