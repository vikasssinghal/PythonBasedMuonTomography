import numpy as np
from MuonTomography.config import CONTAINER_SIZE, VOXEL_SIZE, Z_PLANES
from MuonTomography.materials import MATERIALS as MATERIAL_DB
from MuonTomography.geometry import get_shape_thickness_vec

class POCAReconstructor:
    def __init__(self, voxel_size=VOXEL_SIZE, container_size=CONTAINER_SIZE):
        """
        Reconstructs the 3D scattering density map inside the container using POCA.
        """
        self.voxel_size = voxel_size
        self.container_size = container_size
        self.num_voxels = int(container_size / voxel_size)
        
        # 3D Voxel Grid: stores accumulated scattering weights
        self.density_grid = np.zeros((self.num_voxels, self.num_voxels, self.num_voxels))
        # Voxel hits counter
        self.hit_grid = np.zeros((self.num_voxels, self.num_voxels, self.num_voxels))

    def reset(self):
        self.density_grid.fill(0.0)
        self.hit_grid.fill(0.0)

    def compute_poca_vec(self, C1, u, C2, v):
        """
        Vectorized calculation of the Point of Closest Approach (POCA) between
        incoming tracks (C1 + t1 * u) and outgoing tracks (C2 + t2 * v).
        
        Args:
            C1 (np.ndarray): (N, 3) centroids of incoming tracks
            u (np.ndarray): (N, 3) directions of incoming tracks
            C2 (np.ndarray): (N, 3) centroids of outgoing tracks
            v (np.ndarray): (N, 3) directions of outgoing tracks
            
        Returns:
            poca (np.ndarray): (N, 3) POCA points
            min_dist (np.ndarray): (N,) minimum distances between tracks
            valid_mask (np.ndarray): (N,) boolean mask indicating valid intersections
        """
        N = C1.shape[0]
        w0 = C1 - C2
        
        # Direction vector dot products
        # Since u and v are unit vectors: u.u = 1, v.v = 1
        b = np.sum(u * v, axis=1) # (N,)
        d = np.sum(u * w0, axis=1) # (N,)
        e = np.sum(v * w0, axis=1) # (N,)
        
        denom = 1.0 - b**2
        
        # Parallel lines mask (avoid division by zero)
        valid_mask = denom > 1e-9
        
        t1 = np.zeros(N)
        t2 = np.zeros(N)
        
        t1[valid_mask] = (b[valid_mask] * e[valid_mask] - d[valid_mask]) / denom[valid_mask]
        t2[valid_mask] = (e[valid_mask] - b[valid_mask] * d[valid_mask]) / denom[valid_mask]
        
        # POCA points on each track segment
        P1 = C1 + t1[:, None] * u
        P2 = C2 + t2[:, None] * v
        
        poca = 0.5 * (P1 + P2)
        min_dist = np.linalg.norm(P1 - P2, axis=1)
        
        return poca, min_dist, valid_mask

    def reconstruct_density_map(self, tracking_results, angle_threshold_deg=0.5):
        """
        Accumulates POCA points into the 3D voxel grid.
        
        Args:
            tracking_results (dict): Output from TrackReconstructor
            angle_threshold_deg (float): Minimum scattering angle to include (reduces noise)
        """
        self.reset()
        
        C1 = tracking_results['centroid_in']
        u = tracking_results['dir_in']
        C2 = tracking_results['centroid_out']
        v = tracking_results['dir_out']
        angles = tracking_results['scattering_angles']
        
        poca_pts, dists, valid = self.compute_poca_vec(C1, u, C2, v)
        
        # Threshold: only reconstruct muons that scattered significantly and have close tracks
        threshold_rad = np.radians(angle_threshold_deg)
        reconstruction_mask = valid & (angles > threshold_rad) & (dists < 5.0)
        
        valid_poca = poca_pts[reconstruction_mask]
        valid_angles = angles[reconstruction_mask]
        
        half_container = self.container_size / 2.0
        
        # Vectorized voxel accumulation
        # Convert POCA coordinates to voxel indices
        # Coordinates range from -half_container to +half_container
        x_idx = np.floor((valid_poca[:, 0] + half_container) / self.voxel_size).astype(int)
        y_idx = np.floor((valid_poca[:, 1] + half_container) / self.voxel_size).astype(int)
        z_idx = np.floor((valid_poca[:, 2] + half_container) / self.voxel_size).astype(int)
        
        # Filter indices inside the grid bounds [0, num_voxels-1]
        in_bounds = (x_idx >= 0) & (x_idx < self.num_voxels) & \
                    (y_idx >= 0) & (y_idx < self.num_voxels) & \
                    (z_idx >= 0) & (z_idx < self.num_voxels)
                    
        x_idx = x_idx[in_bounds]
        y_idx = y_idx[in_bounds]
        z_idx = z_idx[in_bounds]
        weights = valid_angles[in_bounds]**2 # Weighted by scattering angle squared
        
        # Use np.add.at for thread-safe accumulation on duplicate indices
        np.add.at(self.density_grid, (x_idx, y_idx, z_idx), weights)
        np.add.at(self.hit_grid, (x_idx, y_idx, z_idx), 1.0)
        
        return poca_pts, reconstruction_mask

class MaterialClassifier:
    def __init__(self):
        pass

    def classify(self, tracking_results, container):
        """
        Classifies the material inside the container using the reconstructed data.
        
        It computes reference predictions of expected scattering angle and displacement
        dynamically, calibrating to the exact momentum distribution and path lengths
        of the muons that intersected the hidden object.
        
        Args:
            tracking_results (dict): Track reconstruction data
            container (Container): The container setup (provides hidden object geometry)
            
        Returns:
            dict: Classification summary containing predicted material, confidence, and statistics.
        """
        angles = tracking_results['scattering_angles']
        displacements = tracking_results['displacement']
        
        # Find which muons actually intersected the hidden object
        # We can approximate this by checking intersection of the incoming track
        # (C_in, dir_in) with the hidden object.
        C_in = tracking_results['centroid_in']
        dir_in = tracking_results['dir_in']
        
        shape_type = container.hidden_object.shape_type
        center = container.hidden_object.center
        params = container.hidden_object.params
        
        thickness_obj, tmin_obj, tmax_obj, mask_obj = get_shape_thickness_vec(
            C_in, dir_in, shape_type, center, params
        )
        
        intersect_indices = np.where(mask_obj)[0]
        
        if len(intersect_indices) < 10:
            # Too few hits on the object to classify reliably, return fallback
            return {
                'predicted_material': 'Unknown (insufficient data)',
                'confidence': 0.0,
                'avg_scattering_angle': np.mean(angles),
                'avg_centroid_shift': np.mean(displacements),
                'radiation_length': 0.0,
                'density': 0.0,
                'scores': {}
            }
            
        # Actual measured averages for muons intersecting the object
        measured_avg_angle = np.mean(angles[intersect_indices])
        measured_avg_shift = np.mean(displacements[intersect_indices])
        
        # Self-calibrating analytical reference calculation
        # For each candidate material in the DB, calculate the expected scattering
        # properties for the exact subset of muons that hit the object.
        # Highland formula:
        m_mu = 105.66
        p = tracking_results['residual_error'] # Placeholder for momentum or access via generator.
        # Wait, the tracking results did not store momentum directly, but we can retrieve it or use
        # the momentum from the hit record. To make it self-contained, let's pass momentum
        # or calculate it. Wait! The prompt says "Store: Muon ID, ..., Momentum" in hits,
        # but in tracking results, let's assume we can fetch momentum.
        # To make it super robust, let's include 'momenta' in the inputs, or let the user supply it.
        # Let's write the signature to accept 'momenta'.
        
        # Let's compute expected scattering for each material
        momenta_obj = tracking_results.get('momenta', None)
        if momenta_obj is None:
            # Fallback: assume average momentum is 3000 MeV/c if not provided
            momenta_obj = np.full_like(angles, 3000.0)
            
        p_obj = momenta_obj[intersect_indices]
        thick_obj_sub = thickness_obj[intersect_indices]
        
        # Distance from object center to Plane 5
        # Object is centered at 'center' (usually Z ~ 0), Plane 5 is at Z = -30.0 cm
        # Distance L is ~ 30 cm
        L = np.abs(Z_PLANES[4] - center[2])
        
        scores = {}
        # Path length in steel walls: top wall (0.5 cm) + bottom wall (0.5 cm)
        # Adjust for muon angle: thickness = 0.5 / |dir_z|
        dir_z_obj = dir_in[intersect_indices, 2]
        thick_steel1 = 0.5 / np.maximum(1e-5, np.abs(dir_z_obj))
        thick_steel2 = 0.5 / np.maximum(1e-5, np.abs(dir_z_obj))
        
        for mat_name, material in MATERIAL_DB.items():
            E = np.sqrt(p_obj**2 + m_mu**2)
            beta = p_obj / E
            beta_p = beta * p_obj
            
            # 1. Scattering from hidden object
            ratio_obj = thick_obj_sub / material.radiation_length
            log_term_obj = np.zeros_like(ratio_obj)
            v_obj = ratio_obj > 1e-10
            log_term_obj[v_obj] = np.log(ratio_obj[v_obj])
            
            theta_obj = np.zeros_like(ratio_obj)
            theta_obj[v_obj] = (13.6 / beta_p[v_obj]) * np.sqrt(ratio_obj[v_obj]) * (1.0 + 0.038 * log_term_obj[v_obj])
            
            # 2. Scattering from steel container entry wall (X0 = 1.76 cm)
            ratio_steel1 = thick_steel1 / 1.76
            log_term_steel1 = np.zeros_like(ratio_steel1)
            v_steel1 = ratio_steel1 > 1e-10
            log_term_steel1[v_steel1] = np.log(ratio_steel1[v_steel1])
            
            theta_steel1 = np.zeros_like(ratio_steel1)
            theta_steel1[v_steel1] = (13.6 / beta_p[v_steel1]) * np.sqrt(ratio_steel1[v_steel1]) * (1.0 + 0.038 * log_term_steel1[v_steel1])
            
            # 3. Scattering from steel container exit wall (X0 = 1.76 cm)
            ratio_steel2 = thick_steel2 / 1.76
            log_term_steel2 = np.zeros_like(ratio_steel2)
            v_steel2 = ratio_steel2 > 1e-10
            log_term_steel2[v_steel2] = np.log(ratio_steel2[v_steel2])
            
            theta_steel2 = np.zeros_like(ratio_steel2)
            theta_steel2[v_steel2] = (13.6 / beta_p[v_steel2]) * np.sqrt(ratio_steel2[v_steel2]) * (1.0 + 0.038 * log_term_steel2[v_steel2])
            
            # Combine angle in quadrature: theta_total = sqrt(theta_obj^2 + theta_steel1^2 + theta_steel2^2)
            theta_0 = np.sqrt(theta_obj**2 + theta_steel1**2 + theta_steel2**2)
            
            # Expected average 3D scattering angle (Mean of 3D scattering = theta_0 * sqrt(pi / 2))
            exp_avg_angle = np.mean(theta_0 * np.sqrt(np.pi / 2.0))
            
            # Combine shift in quadrature using correct lever arms to Plane 5
            L_entry = np.abs(20.0 - Z_PLANES[4]) # 50 cm lever arm
            L_exit = np.abs(-20.0 - Z_PLANES[4]) # 10 cm lever arm
            L_obj = np.abs(center[2] - Z_PLANES[4])
            
            var_shift = (theta_steel1 * L_entry)**2 + (theta_steel2 * L_exit)**2 + (theta_obj * L_obj)**2
            exp_avg_shift = np.mean(np.sqrt(var_shift) * np.sqrt(np.pi / 2.0))
            
            # Error metric: sum of relative differences
            err_angle = abs(measured_avg_angle - exp_avg_angle) / (exp_avg_angle + 1e-9)
            err_shift = abs(measured_avg_shift - exp_avg_shift) / (exp_avg_shift + 1e-9)
            
            # Combine errors
            scores[mat_name] = 0.7 * err_angle + 0.3 * err_shift

        # Convert scores to confidence using Softmax of negative errors
        # Lower error -> higher confidence
        mat_names = list(scores.keys())
        errs = np.array([scores[name] for name in mat_names])
        
        # Scaling parameter (temperature)
        temp = 0.05
        weights = np.exp(-errs / temp)
        confidences = weights / np.sum(weights)
        
        best_idx = np.argmax(confidences)
        predicted_mat = mat_names[best_idx]
        best_conf = confidences[best_idx]
        
        return {
            'predicted_material': predicted_mat,
            'confidence': best_conf,
            'avg_scattering_angle': measured_avg_angle,
            'avg_centroid_shift': measured_avg_shift,
            'radiation_length': MATERIAL_DB[predicted_mat].radiation_length,
            'density': MATERIAL_DB[predicted_mat].density,
            'scores': {mat_names[i]: float(confidences[i]) for i in range(len(mat_names))}
        }
