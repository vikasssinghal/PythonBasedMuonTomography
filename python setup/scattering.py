import numpy as np
from MuonTomography.materials import MATERIALS
from MuonTomography.geometry import intersect_aabb_vec, intersect_sphere_vec, intersect_cylinder_vec, get_shape_thickness_vec

class ScatteringSimulator:
    def __init__(self, container):
        """
        Simulates Multiple Coulomb Scattering of muons through the container setup.
        
        Args:
            container (Container): The container geometry and hidden object
        """
        self.container = container

    def compute_highland_theta0(self, x, X0, p):
        """
        Vectorized calculation of the scattering angle standard deviation
        using the Highland formula.
        
        Args:
            x (np.ndarray): Thickness of material traversed (cm)
            X0 (float): Radiation length of material (cm)
            p (np.ndarray): Muon momentum (MeV/c)
            
        Returns:
            np.ndarray: Theta_0 (radians) for each muon
        """
        m_mu = 105.66 # MeV/c^2
        E = np.sqrt(p**2 + m_mu**2)
        beta = p / E
        beta_p = beta * p # MeV
        
        ratio = x / X0
        
        # Avoid log of zero or negative numbers
        log_term = np.zeros_like(ratio)
        valid = ratio > 1e-10
        log_term[valid] = np.log(ratio[valid])
        
        theta_0 = np.zeros_like(ratio)
        theta_0[valid] = (13.6 / beta_p[valid]) * np.sqrt(ratio[valid]) * (1.0 + 0.038 * log_term[valid])
        
        return np.maximum(0.0, theta_0)

    def scatter_direction_vec(self, D, theta_0):
        """
        Applies random scattering to the direction unit vectors.
        
        Args:
            D (np.ndarray): (N, 3) direction unit vectors
            theta_0 (np.ndarray): (N,) scattering angle standard deviations
            
        Returns:
            np.ndarray: (N, 3) scattered direction unit vectors
        """
        N = D.shape[0]
        if N == 0:
            return D
            
        # Sample scattering angles in two orthogonal planes
        dtheta_1 = np.random.normal(0, 1.0, N) * theta_0
        dtheta_2 = np.random.normal(0, 1.0, N) * theta_0
        
        D_norm = np.linalg.norm(D, axis=1)
        D_unit = D / D_norm[:, None]
        
        # Build local orthonormal frames
        e1 = np.zeros_like(D_unit)
        is_vertical = (np.abs(D_unit[:, 0]) < 1e-5) & (np.abs(D_unit[:, 1]) < 1e-5)
        
        # For near-vertical vectors, use X-axis as perpendicular
        e1[is_vertical] = np.array([1.0, 0.0, 0.0])
        
        # For others, project to XY plane and rotate 90 degrees
        not_vertical = ~is_vertical
        if np.any(not_vertical):
            e1_nv = np.zeros((np.sum(not_vertical), 3))
            e1_nv[:, 0] = -D_unit[not_vertical, 1]
            e1_nv[:, 1] = D_unit[not_vertical, 0]
            e1_nv_norm = np.linalg.norm(e1_nv, axis=1)
            e1[not_vertical] = e1_nv / e1_nv_norm[:, None]
            
        e2 = np.cross(D_unit, e1)
        e2_norm = np.linalg.norm(e2, axis=1)
        e2 = e2 / e2_norm[:, None]
        
        # Compute scattered direction
        new_D = D_unit + dtheta_1[:, None] * e1 + dtheta_2[:, None] * e2
        new_D_norm = np.linalg.norm(new_D, axis=1)
        new_D = new_D / new_D_norm[:, None]
        
        return new_D * D_norm[:, None]

    def simulate_scattering(self, S, D, momenta):
        """
        Vectorized propagation of muons through the container walls,
        the cavity space, and the hidden object.
        
        Args:
            S (np.ndarray): (N, 3) starting positions (above container, e.g. at Z=30)
            D (np.ndarray): (N, 3) direction unit vectors
            momenta (np.ndarray): (N,) momenta in MeV/c
            
        Returns:
            P_ref (np.ndarray): (N, 3) positions just below container (Z=-25)
            D_ref (np.ndarray): (N, 3) directions after leaving the container
            scatter_records (dict): Detailed scattering details for debugging/visualization
        """
        N = S.shape[0]
        P = S.copy()
        D_curr = D.copy()
        
        # Track total scattering angles for classification
        total_scatter_angles = np.zeros(N)
        
        # Intersect with outer container box [-20, 20]^3
        tmin_out, tmax_out, mask_out = intersect_aabb_vec(P, D_curr, self.container.outer_min, self.container.outer_max)
        
        # Intersect with inner cavity [-19.5, 19.5]^3
        tmin_in, tmax_in, mask_in = intersect_aabb_vec(P, D_curr, self.container.inner_min, self.container.inner_max)
        
        idx_out = np.where(mask_out)[0]
        
        if len(idx_out) > 0:
            P_out = P[idx_out]
            D_out = D_curr[idx_out]
            p_out = momenta[idx_out]
            
            mask_in_out = mask_in[idx_out]
            
            # Group A: Intersect both outer walls and inner cavity
            idx_A = np.where(mask_in_out)[0]
            if len(idx_A) > 0:
                idx_A_rel = idx_out[idx_A]
                
                P_A = P_out[idx_A]
                D_A = D_out[idx_A]
                p_A = p_out[idx_A]
                
                tmin_out_A = tmin_out[idx_A_rel]
                tmax_out_A = tmax_out[idx_A_rel]
                tmin_in_A = tmin_in[idx_A_rel]
                tmax_in_A = tmax_in[idx_A_rel]
                
                # --- Segment 1: Entry Steel Wall ---
                s_wall1 = np.maximum(0.0, tmin_in_A - tmin_out_A)
                P_mid1 = P_A + (tmin_out_A + 0.5 * s_wall1)[:, None] * D_A
                theta0_wall1 = self.compute_highland_theta0(s_wall1, self.container.wall_radiation_length, p_A)
                D_A_scat1 = self.scatter_direction_vec(D_A, theta0_wall1)
                
                # Keep track of local scattering angle
                cos_ang = np.sum(D_A * D_A_scat1, axis=1)
                cos_ang = np.clip(cos_ang, -1.0, 1.0)
                total_scatter_angles[idx_A_rel] += np.arccos(cos_ang)
                D_A = D_A_scat1
                
                # Propagate to cavity entry
                P_cavity_entry = P_mid1 + (0.5 * s_wall1)[:, None] * D_A
                
                # --- Segment 2: Cavity (containing hidden object) ---
                shape_type = self.container.hidden_object.shape_type
                center = self.container.hidden_object.center
                params = self.container.hidden_object.params
                
                # Path length in hidden object
                thick_obj, tmin_obj, tmax_obj, mask_obj = get_shape_thickness_vec(
                    P_cavity_entry, D_A, shape_type, center, params
                )
                
                # Total distance in cavity along D_A
                s_cavity = tmax_in_A - tmin_in_A
                
                idx_A1 = np.where(mask_obj)[0]  # Hits hidden object
                idx_A2 = np.where(~mask_obj)[0] # Misses hidden object
                
                P_cavity_exit = np.zeros_like(P_A)
                
                # Misses hidden object: propagates through cavity filled with Air
                if len(idx_A2) > 0:
                    s_cav_A2 = s_cavity[idx_A2]
                    p_A2 = p_A[idx_A2]
                    D_A2 = D_A[idx_A2]
                    P_cav_A2 = P_cavity_entry[idx_A2]
                    
                    P_cav_mid_A2 = P_cav_A2 + (0.5 * s_cav_A2)[:, None] * D_A2
                    theta0_air = self.compute_highland_theta0(s_cav_A2, MATERIALS['Air'].radiation_length, p_A2)
                    D_A2_scat = self.scatter_direction_vec(D_A2, theta0_air)
                    
                    cos_ang = np.sum(D_A2 * D_A2_scat, axis=1)
                    cos_ang = np.clip(cos_ang, -1.0, 1.0)
                    total_scatter_angles[idx_A_rel[idx_A2]] += np.arccos(cos_ang)
                    D_A[idx_A2] = D_A2_scat
                    P_cavity_exit[idx_A2] = P_cav_mid_A2 + (0.5 * s_cav_A2)[:, None] * D_A[idx_A2]
                    
                # Hits hidden object
                if len(idx_A1) > 0:
                    tmin_obj_A1 = tmin_obj[idx_A1]
                    tmax_obj_A1 = tmax_obj[idx_A1]
                    thick_obj_A1 = thick_obj[idx_A1]
                    p_A1 = p_A[idx_A1]
                    D_A1 = D_A[idx_A1]
                    P_cav_A1 = P_cavity_entry[idx_A1]
                    s_cav_A1 = s_cavity[idx_A1]
                    
                    # Propagate to object entrance (through air)
                    P_obj_entry = P_cav_A1 + tmin_obj_A1[:, None] * D_A1
                    
                    # Propagate to object center and scatter
                    P_obj_mid = P_obj_entry + (0.5 * thick_obj_A1)[:, None] * D_A1
                    theta0_obj = self.compute_highland_theta0(
                        thick_obj_A1, self.container.hidden_object.material.radiation_length, p_A1
                    )
                    D_A1_scat = self.scatter_direction_vec(D_A1, theta0_obj)
                    
                    cos_ang = np.sum(D_A1 * D_A1_scat, axis=1)
                    cos_ang = np.clip(cos_ang, -1.0, 1.0)
                    total_scatter_angles[idx_A_rel[idx_A1]] += np.arccos(cos_ang)
                    D_A[idx_A1] = D_A1_scat
                    
                    # Propagate out of the object and to bottom steel wall entry
                    P_obj_exit = P_obj_mid + (0.5 * thick_obj_A1)[:, None] * D_A[idx_A1]
                    s_air2 = np.maximum(0.0, s_cav_A1 - tmax_obj_A1)
                    P_cavity_exit[idx_A1] = P_obj_exit + s_air2[:, None] * D_A[idx_A1]
                    
                # --- Segment 3: Exit Steel Wall ---
                s_wall2 = np.maximum(0.0, tmax_out_A - tmax_in_A)
                P_mid2 = P_cavity_exit + (0.5 * s_wall2)[:, None] * D_A
                theta0_wall2 = self.compute_highland_theta0(s_wall2, self.container.wall_radiation_length, p_A)
                D_A_scat2 = self.scatter_direction_vec(D_A, theta0_wall2)
                
                cos_ang = np.sum(D_A * D_A_scat2, axis=1)
                cos_ang = np.clip(cos_ang, -1.0, 1.0)
                total_scatter_angles[idx_A_rel] += np.arccos(cos_ang)
                D_A = D_A_scat2
                P_exit_A = P_mid2 + (0.5 * s_wall2)[:, None] * D_A
                
                P[idx_A_rel] = P_exit_A
                D_curr[idx_A_rel] = D_A
                
            # Group B: Skims outer steel box wall only, missing cavity
            idx_B = np.where(~mask_in_out)[0]
            if len(idx_B) > 0:
                idx_B_rel = idx_out[idx_B]
                P_B = P_out[idx_B]
                D_B = D_out[idx_B]
                p_B = p_out[idx_B]
                
                tmin_out_B = tmin_out[idx_B_rel]
                tmax_out_B = tmax_out[idx_B_rel]
                s_steel = np.maximum(0.0, tmax_out_B - tmin_out_B)
                
                P_mid = P_B + (tmin_out_B + 0.5 * s_steel)[:, None] * D_B
                theta0_steel = self.compute_highland_theta0(s_steel, self.container.wall_radiation_length, p_B)
                D_B_scat = self.scatter_direction_vec(D_B, theta0_steel)
                
                cos_ang = np.sum(D_B * D_B_scat, axis=1)
                cos_ang = np.clip(cos_ang, -1.0, 1.0)
                total_scatter_angles[idx_B_rel] += np.arccos(cos_ang)
                D_B = D_B_scat
                P_exit_B = P_mid + (0.5 * s_steel)[:, None] * D_B
                
                P[idx_B_rel] = P_exit_B
                D_curr[idx_B_rel] = D_B

        # Propagate all muons to a common Z reference plane below the container (Z = -25 cm)
        t_to_ref = (-25.0 - P[:, 2]) / D_curr[:, 2]
        P_ref = P + t_to_ref[:, None] * D_curr
        
        return P_ref, D_curr, {
            'total_scattering_angles': total_scatter_angles,
            'hit_container': mask_out
        }
