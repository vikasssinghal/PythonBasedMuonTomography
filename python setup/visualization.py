import numpy as np
import plotly.graph_objects as go
from MuonTomography.config import ACTIVE_AREA_SIZE, SLAB_THICKNESS, Z_PLANES, CONTAINER_SIZE
from MuonTomography.materials import MATERIALS

def get_box_mesh(center, size, color, opacity, name):
    """Generates a go.Mesh3d for a 3D box."""
    dx, dy, dz = size
    x, y, z = center
    
    x_verts = [x-dx/2, x+dx/2, x+dx/2, x-dx/2, x-dx/2, x+dx/2, x+dx/2, x-dx/2]
    y_verts = [y-dy/2, y-dy/2, y+dy/2, y+dy/2, y-dy/2, y-dy/2, y+dy/2, y+dy/2]
    z_verts = [z-dz/2, z-dz/2, z-dz/2, z-dz/2, z+dz/2, z+dz/2, z+dz/2, z+dz/2]
    
    # 12 triangles for box faces
    i = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3]
    j = [1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 0, 4]
    k = [2, 3, 6, 7, 5, 4, 6, 5, 7, 6, 4, 7]
    
    return go.Mesh3d(
        x=x_verts, y=y_verts, z=z_verts,
        i=i, j=j, k=k,
        color=color, opacity=opacity, name=name, showlegend=True
    )

def get_sphere_mesh(center, radius, color, opacity, name):
    """Generates a go.Mesh3d for a sphere."""
    n_theta = 15
    n_phi = 15
    theta = np.linspace(0, np.pi, n_theta)
    phi = np.linspace(0, 2 * np.pi, n_phi)
    
    x_verts = []
    y_verts = []
    z_verts = []
    
    for t in theta:
        for p in phi:
            x_verts.append(center[0] + radius * np.sin(t) * np.cos(p))
            y_verts.append(center[1] + radius * np.sin(t) * np.sin(p))
            z_verts.append(center[2] + radius * np.cos(t))
            
    i = []
    j = []
    k = []
    for r in range(n_theta - 1):
        for c in range(n_phi - 1):
            p1 = r * n_phi + c
            p2 = p1 + 1
            p3 = (r + 1) * n_phi + c
            p4 = p3 + 1
            
            i.append(p1)
            j.append(p2)
            k.append(p3)
            
            i.append(p2)
            j.append(p4)
            k.append(p3)
            
    return go.Mesh3d(
        x=x_verts, y=y_verts, z=z_verts,
        i=i, j=j, k=k,
        color=color, opacity=opacity, name=name, showlegend=True
    )

def get_cylinder_mesh(center, radius, height, color, opacity, name):
    """Generates a go.Mesh3d for a cylinder."""
    n_slices = 20
    theta = np.linspace(0, 2 * np.pi, n_slices)
    
    x_verts = []
    y_verts = []
    z_verts = []
    
    z_min = center[2] - height / 2.0
    z_max = center[2] + height / 2.0
    
    for t in theta:
        x_verts.append(center[0] + radius * np.cos(t))
        y_verts.append(center[1] + radius * np.sin(t))
        z_verts.append(z_min)
        
    for t in theta:
        x_verts.append(center[0] + radius * np.cos(t))
        y_verts.append(center[1] + radius * np.sin(t))
        z_verts.append(z_max)
        
    x_verts.append(center[0])
    y_verts.append(center[1])
    z_verts.append(z_min)
    
    x_verts.append(center[0])
    y_verts.append(center[1])
    z_verts.append(z_max)
    
    i = []
    j = []
    k = []
    
    for s in range(n_slices - 1):
        p1 = s
        p2 = s + 1
        p3 = s + n_slices
        p4 = p3 + 1
        
        i.append(p1)
        j.append(p2)
        k.append(p3)
        
        i.append(p2)
        j.append(p4)
        k.append(p3)
        
    c_bottom = 2 * n_slices
    for s in range(n_slices - 1):
        i.append(c_bottom)
        j.append(s)
        k.append(s + 1)
        
    c_top = 2 * n_slices + 1
    for s in range(n_slices - 1):
        i.append(c_top)
        j.append(s + n_slices + 1)
        k.append(s + n_slices)
        
    return go.Mesh3d(
        x=x_verts, y=y_verts, z=z_verts,
        i=i, j=j, k=k,
        color=color, opacity=opacity, name=name, showlegend=True
    )

def create_visualization(detector_stack, container, tracking_results, poca_pts, density_grid, num_show_tracks=50, recon_mask=None):
    """
    Creates an interactive 3D Plotly visualization of the complete detector setup,
    muon tracks, and reconstructed density.
    """
    fig = go.Figure()
    
    # 1. Scintillator Planes & MAPMTs & Fiber Grids
    # For performance, we combine the lines of all fibers of a plane into a single trace
    for plane in detector_stack.planes:
        z_p = plane.z_center
        # Draw Scintillator Body
        fig.add_trace(get_box_mesh(
            center=[0.0, 0.0, z_p],
            size=[ACTIVE_AREA_SIZE, ACTIVE_AREA_SIZE, SLAB_THICKNESS],
            color='rgba(135, 206, 250, 0.15)', # Light transparent blue
            opacity=0.3,
            name=f"Plane {plane.plane_id} Scintillator"
        ))
        
        # Draw MAPMTs
        fig.add_trace(get_box_mesh(
            center=plane.x_mapmt.center,
            size=plane.x_mapmt.size,
            color='rgb(40, 40, 40)', # Dark gray
            opacity=0.9,
            name=f"Plane {plane.plane_id} X-MAPMT"
        ))
        fig.add_trace(get_box_mesh(
            center=plane.y_mapmt.center,
            size=plane.y_mapmt.size,
            color='rgb(40, 40, 40)',
            opacity=0.9,
            name=f"Plane {plane.plane_id} Y-MAPMT"
        ))
        
        # Merge X fiber grid curves into 1 trace
        x_fib_x, x_fib_y, x_fib_z = [], [], []
        # Draw a subset of fibers to keep plot light, e.g. every 5th fiber
        for i in range(0, 100, 5):
            path = plane.x_fiber_layer.get_fiber(i).get_3d_path()
            x_fib_x.extend(path[:, 0])
            x_fib_x.append(None)
            x_fib_y.extend(path[:, 1])
            x_fib_y.append(None)
            x_fib_z.extend(path[:, 2])
            x_fib_z.append(None)
            
        fig.add_trace(go.Scatter3d(
            x=x_fib_x, y=x_fib_y, z=x_fib_z,
            mode='lines',
            line=dict(color='rgba(0, 255, 0, 0.15)', width=1.5), # semi-transparent green
            name=f"Plane {plane.plane_id} X-Fibers",
            showlegend=False
        ))
        
        # Merge Y fiber grid curves into 1 trace
        y_fib_x, y_fib_y, y_fib_z = [], [], []
        for j in range(0, 100, 5):
            path = plane.y_fiber_layer.get_fiber(j).get_3d_path()
            y_fib_x.extend(path[:, 0])
            y_fib_x.append(None)
            y_fib_y.extend(path[:, 1])
            y_fib_y.append(None)
            y_fib_z.extend(path[:, 2])
            y_fib_z.append(None)
            
        fig.add_trace(go.Scatter3d(
            x=y_fib_x, y=y_fib_y, z=y_fib_z,
            mode='lines',
            line=dict(color='rgba(255, 69, 0, 0.15)', width=1.5), # semi-transparent orange
            name=f"Plane {plane.plane_id} Y-Fibers",
            showlegend=False
        ))

    # 2. Draw Steel Container
    # We draw the container walls as a semi-transparent gray box
    fig.add_trace(get_box_mesh(
        center=container.center,
        size=[CONTAINER_SIZE, CONTAINER_SIZE, CONTAINER_SIZE],
        color='rgba(128, 128, 128, 0.1)', # highly transparent gray
        opacity=0.2,
        name="Steel Container Walls"
    ))
    # Draw container wireframe edges
    c_half = CONTAINER_SIZE / 2.0
    cx, cy, cz = container.center
    wf_x = [
        cx-c_half, cx+c_half, cx+c_half, cx-c_half, cx-c_half, None,
        cx-c_half, cx+c_half, cx+c_half, cx-c_half, cx-c_half, None,
        cx-c_half, cx-c_half, None, cx+c_half, cx+c_half, None,
        cx+c_half, cx+c_half, None, cx-c_half, cx-c_half
    ]
    wf_y = [
        cy-c_half, cy-c_half, cy+c_half, cy+c_half, cy-c_half, None,
        cy-c_half, cy-c_half, cy+c_half, cy+c_half, cy-c_half, None,
        cy-c_half, cy-c_half, None, cy-c_half, cy-c_half, None,
        cy+c_half, cy+c_half, None, cy+c_half, cy+c_half
    ]
    wf_z = [
        cz-c_half, cz-c_half, cz-c_half, cz-c_half, cz-c_half, None,
        cz+c_half, cz+c_half, cz+c_half, cz+c_half, cz+c_half, None,
        cz-c_half, cz+c_half, None, cz-c_half, cz+c_half, None,
        cz-c_half, cz+c_half, None, cz-c_half, cz+c_half
    ]
    fig.add_trace(go.Scatter3d(
        x=wf_x, y=wf_y, z=wf_z,
        mode='lines',
        line=dict(color='rgb(100, 100, 100)', width=3),
        name="Steel Container Frame"
    ))

    # 3. Draw Hidden Object inside the Container
    obj = container.hidden_object
    obj_name = f"Hidden Object ({obj.material_name})"
    
    if obj.shape_type == 'cube':
        size_val = obj.params['size']
        fig.add_trace(get_box_mesh(
            center=obj.center,
            size=[size_val, size_val, size_val],
            color='rgba(255, 215, 0, 0.4)', # Gold
            opacity=0.6,
            name=obj_name
        ))
    elif obj.shape_type == 'sphere':
        rad_val = obj.params['radius']
        fig.add_trace(get_sphere_mesh(
            center=obj.center,
            radius=rad_val,
            color='rgba(255, 215, 0, 0.4)',
            opacity=0.6,
            name=obj_name
        ))
    elif obj.shape_type == 'cylinder':
        rad_val = obj.params['radius']
        h_val = obj.params['height']
        fig.add_trace(get_cylinder_mesh(
            center=obj.center,
            radius=rad_val,
            height=h_val,
            color='rgba(255, 215, 0, 0.4)',
            opacity=0.6,
            name=obj_name
        ))
    elif obj.shape_type == 'irregular':
        # Union of two boxes (cross shape)
        cx, cy, cz = obj.center
        fig.add_trace(get_box_mesh(
            center=obj.center,
            size=[10.0, 10.0, 30.0],
            color='rgba(255, 215, 0, 0.4)',
            opacity=0.6,
            name=obj_name
        ))
        fig.add_trace(get_box_mesh(
            center=obj.center,
            size=[30.0, 10.0, 10.0],
            color='rgba(255, 215, 0, 0.4)',
            opacity=0.6,
            name=obj_name + " (Horizontal limb)",
            showlegend=False
        ))

    # 4. Draw Reconstructed Scattering Density Heatmap (Voxels)
    # Filter density grid to only show significant scattering voxels
    max_density = np.max(density_grid)
    if max_density > 0:
        threshold = max_density * 0.05
        vox_indices = np.where(density_grid > threshold)
        
        # Calculate voxel center coordinates
        half_cont = CONTAINER_SIZE / 2.0
        v_size = 1.0 # 1 cm voxel
        x_vox = -half_cont + vox_indices[0] * v_size + 0.5 * v_size
        y_vox = -half_cont + vox_indices[1] * v_size + 0.5 * v_size
        z_vox = -half_cont + vox_indices[2] * v_size + 0.5 * v_size
        densities = density_grid[vox_indices]
        
        # Scale marker size based on density
        sizes = 2 + 10 * (densities / max_density)
        
        fig.add_trace(go.Scatter3d(
            x=x_vox, y=y_vox, z=z_vox,
            mode='markers',
            marker=dict(
                size=sizes,
                color=densities,
                colorscale='YlOrRd', # Yellow-Orange-Red
                opacity=0.5,
                colorbar=dict(title="Scattering Density (rad²)", x=0.85),
                showscale=True
            ),
            name="Scattering Density Voxel Map"
        ))

    muon_ids = tracking_results.get('muon_ids', None)
    momenta = tracking_results.get('momenta', None)
    scattering_angles = tracking_results.get('scattering_angles', None)
    displacements = tracking_results.get('displacement', None)
    dir_in = tracking_results.get('dir_in', None)

    # 5. Draw Reconstructed POCA Points
    num_poca = len(poca_pts)
    if num_poca > 0:
        if recon_mask is not None and muon_ids is not None:
            recon_indices = np.where(recon_mask)[0]
            show_poca_cnt = min(500, len(poca_pts))
            selected_poca_k = np.random.choice(len(poca_pts), show_poca_cnt, replace=False)
            
            poca_x, poca_y, poca_z = [], [], []
            poca_hover_texts = []
            
            for k in selected_poca_k:
                orig_idx = recon_indices[k]
                pt = poca_pts[k]
                
                muon_id = muon_ids[orig_idx]
                scat_angle_deg = np.degrees(scattering_angles[orig_idx])
                shift_val = displacements[orig_idx]
                p_gev = momenta[orig_idx] / 1000.0
                
                poca_x.append(pt[0])
                poca_y.append(pt[1])
                poca_z.append(pt[2])
                
                poca_hover_texts.append(
                    f"POCA Point<br>"
                    f"Muon ID: {muon_id}<br>"
                    f"Coordinates: ({pt[0]:.2f}, {pt[1]:.2f}, {pt[2]:.2f}) cm<br>"
                    f"Scattering Angle: {scat_angle_deg:.3f}°<br>"
                    f"Centroid Shift: {shift_val:.3f} cm<br>"
                    f"Momentum: {p_gev:.2f} GeV/c"
                )
                
            fig.add_trace(go.Scatter3d(
                x=poca_x, y=poca_y, z=poca_z,
                mode='markers',
                marker=dict(size=3.5, color='rgb(255, 0, 0)', opacity=0.8),
                text=poca_hover_texts,
                hoverinfo='text',
                name="POCA Points"
            ))
        else:
            show_poca_cnt = min(500, num_poca)
            poca_idx = np.random.choice(num_poca, show_poca_cnt, replace=False)
            fig.add_trace(go.Scatter3d(
                x=poca_pts[poca_idx, 0],
                y=poca_pts[poca_idx, 1],
                z=poca_pts[poca_idx, 2],
                mode='markers',
                marker=dict(size=3, color='rgb(255, 0, 0)', opacity=0.8),
                name="POCA Points"
            ))

    # 6. Draw Muon Trajectories & Fitted Tracks & Highlighted Hit Pixels
    total_tracks = tracking_results['dir_in'].shape[0]
    show_idx = np.random.choice(total_tracks, min(num_show_tracks, total_tracks), replace=False)
    
    slope_x_in = tracking_results['slope_x_in']
    intercept_x_in = tracking_results['intercept_x_in']
    slope_y_in = tracking_results['slope_y_in']
    intercept_y_in = tracking_results['intercept_y_in']
    
    slope_x_out = tracking_results['slope_x_out']
    intercept_x_out = tracking_results['intercept_x_out']
    slope_y_out = tracking_results['slope_y_out']
    intercept_y_out = tracking_results['intercept_y_out']
    
    hit_pixels_x, hit_pixels_y, hit_pixels_z = [], [], []
    hit_hover_texts = []
    
    # We add tracks individually to allow individual hovertext with Muon ID and scattering angle!
    for count, idx in enumerate(show_idx):
        muon_id = muon_ids[idx] if muon_ids is not None else idx + 1
        p_gev = (momenta[idx] / 1000.0) if momenta is not None else 3.0
        scat_angle_deg = np.degrees(scattering_angles[idx]) if scattering_angles is not None else 0.0
        scat_angle_rad = scattering_angles[idx] if scattering_angles is not None else 0.0
        shift_val = displacements[idx] if displacements is not None else 0.0
        
        is_first = (count == 0)
        
        # Z ranges for plotting
        # Incoming: Z from Plane 1 (75 cm) to top container boundary (20 cm)
        x_in_start = slope_x_in[idx] * 75.0 + intercept_x_in[idx]
        y_in_start = slope_y_in[idx] * 75.0 + intercept_y_in[idx]
        x_in_end = slope_x_in[idx] * 20.0 + intercept_x_in[idx]
        y_in_end = slope_y_in[idx] * 20.0 + intercept_y_in[idx]
        
        fig.add_trace(go.Scatter3d(
            x=[x_in_start, x_in_end],
            y=[y_in_start, y_in_end],
            z=[75.0, 20.0],
            mode='lines',
            line=dict(color='rgba(30, 144, 255, 0.6)', width=2.5),
            hovertext=f"Muon ID: {muon_id}<br>Momentum: {p_gev:.2f} GeV/c<br>Incoming Angle: {np.degrees(np.arccos(np.clip(np.abs(dir_in[idx, 2]), -1.0, 1.0))):.2f}°",
            hoverinfo='text',
            name="Incoming Fitted Muon Tracks" if is_first else "",
            legendgroup="incoming",
            showlegend=is_first
        ))
        
        # Outgoing: Z from bottom container boundary (-20 cm) to Plane 8 (-75 cm)
        x_out_start = slope_x_out[idx] * -20.0 + intercept_x_out[idx]
        y_out_start = slope_y_out[idx] * -20.0 + intercept_y_out[idx]
        x_out_end = slope_x_out[idx] * -75.0 + intercept_x_out[idx]
        y_out_end = slope_y_out[idx] * -75.0 + intercept_y_out[idx]
        
        fig.add_trace(go.Scatter3d(
            x=[x_out_start, x_out_end],
            y=[y_out_start, y_out_end],
            z=[-20.0, -75.0],
            mode='lines',
            line=dict(color='rgba(255, 0, 128, 0.6)', width=2.5),
            hovertext=f"Muon ID: {muon_id}<br>Scattering Angle: {scat_angle_deg:.3f}° ({scat_angle_rad:.5f} rad)<br>Centroid Shift: {shift_val:.3f} cm",
            hoverinfo='text',
            name="Outgoing Scattered Muon Tracks" if is_first else "",
            legendgroup="outgoing",
            showlegend=is_first
        ))
        
        # Highlight hits on each Z-plane for these show tracks
        for d, zp in enumerate(Z_PLANES):
            plane_id = d + 1
            if zp > 0:
                xh = slope_x_in[idx] * zp + intercept_x_in[idx]
                yh = slope_y_in[idx] * zp + intercept_y_in[idx]
            else:
                xh = slope_x_out[idx] * zp + intercept_x_out[idx]
                yh = slope_y_out[idx] * zp + intercept_y_out[idx]
                
            # Pixel alignment: 1 cm grid
            half_a = ACTIVE_AREA_SIZE / 2.0
            px = int(np.floor((xh + half_a) / 1.0))
            py = int(np.floor((yh + half_a) / 1.0))
            px = min(max(px, 0), 99)
            py = min(max(py, 0), 99)
            
            xh_aligned = -half_a + px + 0.5
            yh_aligned = -half_a + py + 0.5
            
            hit_pixels_x.append(xh_aligned)
            hit_pixels_y.append(yh_aligned)
            hit_pixels_z.append(zp)
            
            hit_hover_texts.append(
                f"Muon ID: {muon_id}<br>"
                f"Plane: {plane_id} (Z = {zp} cm)<br>"
                f"Fibers: X={px}, Y={py} (Pixel #{py*100+px})<br>"
                f"Coordinates: ({xh:.2f}, {yh:.2f}, {zp:.1f}) cm<br>"
                f"Scattering Angle: {scat_angle_deg:.3f}°"
            )
            
    fig.add_trace(go.Scatter3d(
        x=hit_pixels_x, y=hit_pixels_y, z=hit_pixels_z,
        mode='markers',
        marker=dict(size=4.5, color='yellow', symbol='square', line=dict(color='black', width=1.5)),
        text=hit_hover_texts,
        hoverinfo='text',
        name="Highlighted Hit Pixels"
    ))

    # Set Layout
    fig.update_layout(
        title={
            'text': "3D Muon Scattering Tomography Event Display & Reconstruction",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 20, 'color': 'white'}
        },
        scene=dict(
            xaxis=dict(title='X (cm)', range=[-70, 70], backgroundcolor='black', gridcolor='gray', showbackground=True),
            yaxis=dict(title='Y (cm)', range=[-70, 70], backgroundcolor='black', gridcolor='gray', showbackground=True),
            zaxis=dict(title='Z (cm)', range=[-85, 85], backgroundcolor='black', gridcolor='gray', showbackground=True),
            aspectratio=dict(x=1, y=1, z=1.2)
        ),
        paper_bgcolor='black',
        plot_bgcolor='black',
        legend=dict(
            font=dict(color='white'),
            x=0.02, y=0.98,
            bgcolor='rgba(0, 0, 0, 0.5)'
        ),
        margin=dict(l=0, r=0, b=0, t=50)
    )
    
    return fig
