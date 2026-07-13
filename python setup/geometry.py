import numpy as np

def intersect_aabb_vec(S, D, box_min, box_max):
    """
    Vectorized Ray-AABB (Axis-Aligned Bounding Box) intersection.
    
    Args:
        S (np.ndarray): Shape (N, 3) representing ray start positions
        D (np.ndarray): Shape (N, 3) representing ray directions (unit vectors)
        box_min (np.ndarray): Shape (3,) representing box minimum corner
        box_max (np.ndarray): Shape (3,) representing box maximum corner
        
    Returns:
        tmin_val (np.ndarray): Shape (N,) entry intersection distances
        tmax (np.ndarray): Shape (N,) exit intersection distances
        mask (np.ndarray): Shape (N,) boolean array where True indicates intersection
    """
    N = S.shape[0]
    tmin = np.full(N, -np.inf)
    tmax = np.full(N, np.inf)
    
    for i in range(3):
        d = D[:, i]
        s = S[:, i]
        
        # Mask for non-parallel rays
        non_parallel = np.abs(d) > 1e-9
        
        t1 = (box_min[i] - s) / np.where(non_parallel, d, 1.0)
        t2 = (box_max[i] - s) / np.where(non_parallel, d, 1.0)
        
        t_entry = np.minimum(t1, t2)
        t_exit = np.maximum(t1, t2)
        
        tmin = np.where(non_parallel, np.maximum(tmin, t_entry), tmin)
        tmax = np.where(non_parallel, np.minimum(tmax, t_exit), tmax)
        
        # Parallel rays must be within the bounds
        parallel_inside = (s >= box_min[i]) & (s <= box_max[i])
        tmin = np.where(~non_parallel & ~parallel_inside, np.inf, tmin)
        tmax = np.where(~non_parallel & ~parallel_inside, -np.inf, tmax)
        
    mask = (tmin <= tmax) & (tmax > 0)
    tmin_val = np.maximum(0.0, tmin)
    return tmin_val, tmax, mask

def intersect_sphere_vec(S, D, center, radius):
    """
    Vectorized Ray-Sphere intersection.
    """
    V = S - center
    b = 2.0 * np.sum(V * D, axis=1)
    c = np.sum(V * V, axis=1) - radius**2
    disc = b**2 - 4.0 * c
    mask = disc >= 0
    
    sqrt_disc = np.zeros_like(disc)
    sqrt_disc[mask] = np.sqrt(disc[mask])
    
    t1 = (-b - sqrt_disc) / 2.0
    t2 = (-b + sqrt_disc) / 2.0
    
    valid = mask & (t2 > 0)
    tmin = np.maximum(0.0, t1)
    return tmin, t2, valid

def intersect_cylinder_vec(S, D, center, radius, height):
    """
    Vectorized Ray-Cylinder intersection (cylinder aligned with Z-axis).
    """
    Cx, Cy, Cz = center
    z_min = Cz - height / 2.0
    z_max = Cz + height / 2.0
    
    Vx = S[:, 0] - Cx
    Vy = S[:, 1] - Cy
    Dx = D[:, 0]
    Dy = D[:, 1]
    
    A = Dx**2 + Dy**2
    
    N = S.shape[0]
    t_min = np.full(N, np.inf)
    t_max = np.full(N, -np.inf)
    mask = np.zeros(N, dtype=bool)
    
    # Ray parallel to cylinder Z axis (A == 0)
    par_mask = A < 1e-9
    inside_xy = (Vx**2 + Vy**2) <= radius**2
    valid_par = par_mask & inside_xy
    if np.any(valid_par):
        dz = D[valid_par, 2]
        sz = S[valid_par, 2]
        non_zero_dz = np.abs(dz) > 1e-9
        t1 = np.where(non_zero_dz, (z_min - sz) / np.where(non_zero_dz, dz, 1.0), -np.inf)
        t2 = np.where(non_zero_dz, (z_max - sz) / np.where(non_zero_dz, dz, 1.0), np.inf)
        t_min[valid_par] = np.minimum(t1, t2)
        t_max[valid_par] = np.maximum(t1, t2)
        mask[valid_par] = True
        
    # Ray not parallel to axis
    non_par = ~par_mask
    if np.any(non_par):
        Vx_np = Vx[non_par]
        Vy_np = Vy[non_par]
        Dx_np = Dx[non_par]
        Dy_np = Dy[non_par]
        A_np = A[non_par]
        
        B = 2.0 * (Vx_np * Dx_np + Vy_np * Dy_np)
        C_coeff = Vx_np**2 + Vy_np**2 - radius**2
        disc = B**2 - 4.0 * A_np * C_coeff
        
        valid_disc = disc >= 0
        idx = np.where(non_par)[0][valid_disc]
        
        if len(idx) > 0:
            sqrt_disc = np.sqrt(disc[valid_disc])
            t_cyl1 = (-B[valid_disc] - sqrt_disc) / (2.0 * A_np[valid_disc])
            t_cyl2 = (-B[valid_disc] + sqrt_disc) / (2.0 * A_np[valid_disc])
            t_cyl_min = np.minimum(t_cyl1, t_cyl2)
            t_cyl_max = np.maximum(t_cyl1, t_cyl2)
            
            # Intersect with Z-caps
            sz = S[idx, 2]
            dz = D[idx, 2]
            
            horizontal = np.abs(dz) < 1e-9
            t_z_min = np.where(horizontal, -np.inf, (z_min - sz) / np.where(~horizontal, dz, 1.0))
            t_z_max = np.where(horizontal, np.inf, (z_max - sz) / np.where(~horizontal, dz, 1.0))
            
            t_z_entry = np.minimum(t_z_min, t_z_max)
            t_z_exit = np.maximum(t_z_min, t_z_max)
            
            tmin_np = np.maximum(t_cyl_min, t_z_entry)
            tmax_np = np.minimum(t_cyl_max, t_z_exit)
            
            valid_z = np.where(horizontal, (sz >= z_min) & (sz <= z_max), True)
            valid_np = (tmin_np <= tmax_np) & (tmax_np > 0) & valid_z
            
            t_min[idx[valid_np]] = np.maximum(0.0, tmin_np[valid_np])
            t_max[idx[valid_np]] = tmax_np[valid_np]
            mask[idx[valid_np]] = True
            
    return t_min, t_max, mask

def get_shape_thickness_vec(S, D, shape_type, center, params):
    """
    Computes path length (thickness) inside a hidden object.
    
    Args:
        S (np.ndarray): Ray start positions (N, 3)
        D (np.ndarray): Ray directions (N, 3)
        shape_type (str): 'cube', 'sphere', 'cylinder', 'irregular'
        center (np.ndarray): Object center position (3,)
        params (dict): Geometry parameters for the shape
        
    Returns:
        thickness (np.ndarray): Path length (N,)
        tmin (np.ndarray): Entry distances (N,)
        tmax (np.ndarray): Exit distances (N,)
        mask (np.ndarray): Boolean mask indicating intersection (N,)
    """
    if shape_type == 'cube':
        size = params.get('size', 25.0)
        box_min = center - size / 2.0
        box_max = center + size / 2.0
        tmin, tmax, mask = intersect_aabb_vec(S, D, box_min, box_max)
        thickness = np.zeros(S.shape[0])
        thickness[mask] = tmax[mask] - tmin[mask]
        return thickness, tmin, tmax, mask
        
    elif shape_type == 'sphere':
        radius = params.get('radius', 15.0)
        tmin, tmax, mask = intersect_sphere_vec(S, D, center, radius)
        thickness = np.zeros(S.shape[0])
        thickness[mask] = tmax[mask] - tmin[mask]
        return thickness, tmin, tmax, mask
        
    elif shape_type == 'cylinder':
        radius = params.get('radius', 12.0)
        height = params.get('height', 30.0)
        tmin, tmax, mask = intersect_cylinder_vec(S, D, center, radius, height)
        thickness = np.zeros(S.shape[0])
        thickness[mask] = tmax[mask] - tmin[mask]
        return thickness, tmin, tmax, mask
        
    elif shape_type == 'irregular':
        # Union of a vertical slab and a horizontal slab forming a 3D cross
        Cx, Cy, Cz = center
        box1_min = np.array([Cx - 5.0, Cy - 5.0, Cz - 15.0])
        box1_max = np.array([Cx + 5.0, Cy + 5.0, Cz + 15.0])
        box2_min = np.array([Cx - 15.0, Cy - 5.0, Cz - 5.0])
        box2_max = np.array([Cx + 15.0, Cy + 5.0, Cz + 5.0])
        
        t_min1, t_max1, m1 = intersect_aabb_vec(S, D, box1_min, box1_max)
        t_min2, t_max2, m2 = intersect_aabb_vec(S, D, box2_min, box2_max)
        
        N = S.shape[0]
        thickness = np.zeros(N)
        t_min = np.full(N, np.inf)
        t_max = np.full(N, -np.inf)
        mask = m1 | m2
        
        len1 = np.where(m1, t_max1 - t_min1, 0.0)
        len2 = np.where(m2, t_max2 - t_min2, 0.0)
        
        t_min[m1] = np.minimum(t_min[m1], t_min1[m1])
        t_max[m1] = np.maximum(t_max[m1], t_max1[m1])
        t_min[m2] = np.minimum(t_min[m2], t_min2[m2])
        t_max[m2] = np.maximum(t_max[m2], t_max2[m2])
        
        # Calculate overlap thickness
        overlap = m1 & m2 & (np.maximum(t_min1, t_min2) <= np.minimum(t_max1, t_max2))
        
        thickness[mask] = np.where(overlap[mask],
                                   np.maximum(t_max1[mask], t_max2[mask]) - np.minimum(t_min1[mask], t_min2[mask]),
                                   len1[mask] + len2[mask])
        
        tmin_final = np.where(mask, t_min, 0.0)
        tmax_final = np.where(mask, t_max, 0.0)
        return thickness, tmin_final, tmax_final, mask
    else:
        N = S.shape[0]
        return np.zeros(N), np.zeros(N), np.zeros(N), np.zeros(N, dtype=bool)
