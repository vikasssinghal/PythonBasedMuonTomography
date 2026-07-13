import numpy as np
from MuonTomography.config import ACTIVE_AREA_SIZE, MAPMT_SIZE

class Fiber:
    def __init__(self, fiber_id, axis, coord_val, z_plane):
        """
        Represents a single optical fiber.
        
        Args:
            fiber_id (int): 0 to 99
            axis (str): 'X' or 'Y'
            coord_val (float): Constant coordinate value (X for X-fiber, Y for Y-fiber)
            z_plane (float): Z-coordinate of the plane center
        """
        self.fiber_id = fiber_id
        self.axis = axis
        self.coord_val = coord_val
        self.z_plane = z_plane
        
    def get_3d_path(self, num_points=20):
        """
        Generates the 3D coordinates representing the fiber path,
        including the straight active segment and the curved routing to the MAPMT.
        
        For X-fibers:
            - Run parallel to Y (from Y = -50 to Y = 50) at X = coord_val.
            - Offset in Z = z_plane + 0.5.
            - Bend at Y = 50 towards the X-MAPMT face at Y = 55.
        For Y-fibers:
            - Run parallel to X (from X = -50 to X = 50) at Y = coord_val.
            - Offset in Z = z_plane - 0.5.
            - Bend at X = 50 towards the Y-MAPMT face at X = 55.
        """
        half_active = ACTIVE_AREA_SIZE / 2.0
        path = []
        
        if self.axis == 'X':
            # Straight section: parallel to Y, from -half_active to +half_active
            # We sample a few points along the straight section
            y_straight = np.linspace(-half_active, half_active, 10)
            x_straight = np.full_like(y_straight, self.coord_val)
            z_straight = np.full_like(y_straight, self.z_plane + 0.5)
            
            for xs, ys, zs in zip(x_straight, y_straight, z_straight):
                path.append([xs, ys, zs])
                
            # Curve section: from Y = 50, Z = z_plane + 0.5 to MAPMT face at Y = 54
            # MAPMT center is (0, 54, z_plane)
            # The 100 fibers map to a 10x10 grid on the MAPMT face of size 8x8 cm
            row = self.fiber_id // 10
            col = self.fiber_id % 10
            
            # Map grid to face: X in [-3.6, 3.6], Z in [z_plane - 3.6, z_plane + 3.6]
            x_term = -3.6 + col * 0.8
            z_term = self.z_plane - 3.6 + row * 0.8
            y_term = 54.0 # MAPMT front face
            
            # Generate a smooth curve (e.g. Bezier-like quadratic interpolation)
            # Control point is (coord_val, 52.0, z_plane + 0.5) to keep it straight for a bit
            p_start = np.array([self.coord_val, half_active, self.z_plane + 0.5])
            p_ctrl = np.array([self.coord_val, 52.0, self.z_plane + 0.5])
            p_end = np.array([x_term, y_term, z_term])
            
            t = np.linspace(0.0, 1.0, num_points)
            for tv in t:
                # Quadratic Bezier
                pt = (1-tv)**2 * p_start + 2*(1-tv)*tv * p_ctrl + tv**2 * p_end
                path.append(pt.tolist())
                
        else: # axis == 'Y'
            # Straight section: parallel to X, from -half_active to +half_active
            x_straight = np.linspace(-half_active, half_active, 10)
            y_straight = np.full_like(x_straight, self.coord_val)
            z_straight = np.full_like(x_straight, self.z_plane - 0.5)
            
            for xs, ys, zs in zip(x_straight, y_straight, z_straight):
                path.append([xs, ys, zs])
                
            # Curve section: from X = 50, Z = z_plane - 0.5 to Y-MAPMT face at X = 54
            row = self.fiber_id // 10
            col = self.fiber_id % 10
            
            # Map grid to face: Y in [-3.6, 3.6], Z in [z_plane - 3.6, z_plane + 3.6]
            y_term = -3.6 + col * 0.8
            z_term = self.z_plane - 3.6 + row * 0.8
            x_term = 54.0 # MAPMT front face
            
            # Control point is (52.0, coord_val, z_plane - 0.5)
            p_start = np.array([half_active, self.coord_val, self.z_plane - 0.5])
            p_ctrl = np.array([52.0, self.coord_val, self.z_plane - 0.5])
            p_end = np.array([x_term, y_term, z_term])
            
            t = np.linspace(0.0, 1.0, num_points)
            for tv in t:
                pt = (1-tv)**2 * p_start + 2*(1-tv)*tv * p_ctrl + tv**2 * p_end
                path.append(pt.tolist())
                
        return np.array(path)

class FiberLayer:
    def __init__(self, axis, z_plane):
        """
        Manages the grid of 100 fibers along one axis of a plane.
        """
        self.axis = axis
        self.z_plane = z_plane
        self.fibers = []
        
        half_active = ACTIVE_AREA_SIZE / 2.0
        # Fiber pitch is 1.0 cm, so center of fiber i is:
        # -49.5, -48.5, ..., 48.5, 49.5
        for i in range(100):
            coord_val = -half_active + 0.5 + i
            self.fibers.append(Fiber(i, axis, coord_val, z_plane))
            
    def get_fiber(self, fiber_id):
        return self.fibers[fiber_id]
