import pandas as pd
import numpy as np
import json
from MuonTomography.tracking import TrackReconstructor
from MuonTomography.reconstruction import POCAReconstructor

def export_data():
    csv_path = "data/geant4/muon_hits_nt_Hits.csv"
    out_path = "web/data.json"
    
    print("Loading Geant4 data...")
    df = pd.read_csv(csv_path, comment='#', names=['event_id', 'plane_id', 'x_mm', 'y_mm', 'z_mm', 'edep_MeV', 'time_ns', 'momentum_MeV'])
    
    df_clean = df.groupby(['event_id', 'plane_id']).first().reset_index()
    hits_per_event = df_clean.groupby('event_id')['plane_id'].count()
    good_events = hits_per_event[hits_per_event == 8].index
    df_good = df_clean[df_clean['event_id'].isin(good_events)].sort_values(['event_id', 'plane_id']).reset_index(drop=True)
    
    N = len(good_events)
    coords = df_good[['x_mm', 'y_mm', 'z_mm']].values / 10.0 # cm
    
    all_hits = coords.reshape((N, 8, 3))
    hits_in = all_hits[:, 0:4, :]
    hits_out = all_hits[:, 4:8, :]

    print("Reconstructing tracks and POCA...")
    tracker = TrackReconstructor()
    res = tracker.reconstruct_tracks_vec(hits_in, hits_out)
    
    momenta = df_good['momentum_MeV'].values[0::8]
    res['momenta'] = momenta 
    
    poca = POCAReconstructor()
    poca_pts, mask = poca.reconstruct_density_map(res, angle_threshold_deg=0.5)

    export_dict = {
        "tracks": [],
        "hits": [],       # <-- NEW: To draw red dots on planes
        "poca_points": [],
        "voxels": []
    }

    # 1. Export Tracks (First 50)
    for i in range(min(50, N)):
        track = []
        for j in range(8):
            track.append({"x": all_hits[i, j, 0], "y": all_hits[i, j, 1], "z": all_hits[i, j, 2]})
            # Add to hits list
            export_dict["hits"].append({"x": all_hits[i, j, 0], "y": all_hits[i, j, 1], "z": all_hits[i, j, 2]})
        export_dict["tracks"].append(track)

    # 2. Export PoCA points (First 500)
    for i in range(min(500, len(poca_pts))):
        if mask[i]: 
            export_dict["poca_points"].append({
                "x": poca_pts[i, 0], "y": poca_pts[i, 1], "z": poca_pts[i, 2]
            })

    # 3. Export Voxels
    grid = poca.density_grid
    half_c = poca.container_size / 2.0
    max_density = np.max(grid)
    
    if max_density > 0:
        x_idx, y_idx, z_idx = np.where(grid > (max_density * 0.1))
        for xi, yi, zi in zip(x_idx, y_idx, z_idx):
            export_dict["voxels"].append({
                "x": (xi * poca.voxel_size) - half_c + 0.5,
                "y": (yi * poca.voxel_size) - half_c + 0.5,
                "z": (zi * poca.voxel_size) - half_c + 0.5,
                "density": float(grid[xi, yi, zi] / max_density)
            })

    with open(out_path, 'w') as f:
        json.dump(export_dict, f)
    print("Done! Exported data to web/data.json")

if __name__ == "__main__":
    export_data()
